import concurrent.futures
import hashlib
import os
import time
import urllib.request
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import Card, CardImage, Holding, Set


def safe_segment(value: str) -> str:
    return value.replace("/", "-").replace("\\", "-").strip()


def download_file(url: str, dest_path: str) -> tuple[bool, str | None]:
    if os.path.exists(dest_path):
        return False, None
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    sha256 = hashlib.sha256()
    try:
        with urllib.request.urlopen(url, timeout=30) as response, open(dest_path, "wb") as handle:
            while True:
                chunk = response.read(1024 * 256)
                if not chunk:
                    break
                sha256.update(chunk)
                handle.write(chunk)
    except Exception:
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise
    return True, sha256.hexdigest()


def download_with_retries(url: str, dest_path: str, retries: int, backoff_seconds: float) -> tuple[bool, str | None, str | None]:
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            downloaded, sha = download_file(url, dest_path)
            return downloaded, sha, None
        except Exception as exc:
            last_error = str(exc)
            if attempt < retries:
                time.sleep(backoff_seconds * attempt)
    return False, None, last_error


def ensure_card_image(db, card_id: int, kind: str, local_path: str, source_url: str, sha256: str | None, downloaded: bool):
    existing = db.query(CardImage).filter(CardImage.card_id == card_id, CardImage.kind == kind).first()
    if existing:
        if source_url and not existing.source_url:
            existing.source_url = source_url
        if local_path and not existing.local_path:
            existing.local_path = local_path
        if downloaded and not existing.downloaded_at:
            existing.downloaded_at = datetime.utcnow()
        if sha256 and not existing.sha256:
            existing.sha256 = sha256
        return
    db.add(CardImage(
        card_id=card_id,
        kind=kind,
        source_url=source_url,
        local_path=local_path,
        sha256=sha256,
        downloaded_at=datetime.utcnow() if downloaded else None,
    ))


def main():
    mode = os.environ.get("PREFETCH_MODE", "owned")
    set_code = os.environ.get("SET_CODE")
    set_id = os.environ.get("SET_ID")
    limit = os.environ.get("PREFETCH_LIMIT")
    workers = int(os.environ.get("PREFETCH_WORKERS", "10"))
    retries = int(os.environ.get("PREFETCH_RETRIES", "3"))
    backoff = float(os.environ.get("PREFETCH_BACKOFF", "1.5"))
    limit_value = int(limit) if limit else None
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    query = db.query(Card).join(Set, Card.set_id == Set.id)
    if mode == "owned":
        query = query.join(Holding, Holding.card_id == Card.id).distinct()
    elif mode == "set":
        if set_id:
            query = query.filter(Card.set_id == int(set_id))
        elif set_code:
            query = query.filter(Set.code == set_code)
        else:
            raise SystemExit("PREFETCH_MODE=set requires SET_CODE or SET_ID")
    elif mode != "all":
        raise SystemExit("Unsupported PREFETCH_MODE. Use owned|set|all.")

    total = query.count()
    print(f"Prefetch mode={mode} cards={total}")
    if limit_value:
        query = query.limit(limit_value)

    rows = query.with_entities(Card.id, Card.number, Set.code).all()
    tasks = []
    for card_id, number, set_code_row in rows:
        if not number or not set_code_row:
            continue
        number_segment = safe_segment(number)
        set_segment = safe_segment(set_code_row)
        tasks.append({
            "card_id": card_id,
            "number_segment": number_segment,
            "set_segment": set_segment,
        })

    total_tasks = len(tasks)
    skipped_count = total - total_tasks
    if total_tasks == 0:
        print("No cards eligible for image download.")
        return

    log_every = max(1, total_tasks // 20)
    downloaded_count = 0
    error_count = 0
    completed = 0

    def worker(task):
        set_segment = task["set_segment"]
        number_segment = task["number_segment"]
        base_dir = os.path.join(settings.media_root, "official", set_segment, number_segment)
        small_url = f"https://images.pokemontcg.io/{set_segment}/{number_segment}.png"
        large_url = f"https://images.pokemontcg.io/{set_segment}/{number_segment}_hires.png"
        small_path = os.path.join(base_dir, "small.png")
        large_path = os.path.join(base_dir, "large.png")
        small_downloaded, small_sha, small_err = download_with_retries(small_url, small_path, retries, backoff)
        large_downloaded, large_sha, large_err = download_with_retries(large_url, large_path, retries, backoff)
        return {
            "card_id": task["card_id"],
            "set_segment": set_segment,
            "number_segment": number_segment,
            "small": {"downloaded": small_downloaded, "sha": small_sha, "error": small_err},
            "large": {"downloaded": large_downloaded, "sha": large_sha, "error": large_err},
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = {executor.submit(worker, task): task for task in tasks}
        for future in concurrent.futures.as_completed(future_map):
            result = future.result()
            card_id = result["card_id"]
            set_segment = result["set_segment"]
            number_segment = result["number_segment"]
            small = result["small"]
            large = result["large"]

            ensure_card_image(
                db,
                card_id,
                "small",
                f"/media/official/{set_segment}/{number_segment}/small.png",
                f"https://images.pokemontcg.io/{set_segment}/{number_segment}.png",
                small["sha"],
                small["downloaded"],
            )
            ensure_card_image(
                db,
                card_id,
                "large",
                f"/media/official/{set_segment}/{number_segment}/large.png",
                f"https://images.pokemontcg.io/{set_segment}/{number_segment}_hires.png",
                large["sha"],
                large["downloaded"],
            )

            if small["downloaded"]:
                downloaded_count += 1
            if large["downloaded"]:
                downloaded_count += 1
            if small["error"] or large["error"]:
                error_count += 1

            completed += 1
            if completed % log_every == 0 or completed == total_tasks:
                print(f"Progress {completed}/{total_tasks} | downloaded={downloaded_count} | errors={error_count} | skipped={skipped_count}")

    db.commit()
    print(f"Downloaded {downloaded_count} images, skipped {skipped_count} cards, errors {error_count}")


if __name__ == "__main__":
    main()
