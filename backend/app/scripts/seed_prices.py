import concurrent.futures
import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import create_engine
from sqlalchemy import or_
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import Holding, LatestPrice, PriceHistory, PriceSource, Set, Card


def parse_updated(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if value > 1_000_000_000_000:
            return datetime.utcfromtimestamp(value / 1000.0)
        if value > 1_000_000_000:
            return datetime.utcfromtimestamp(value)
        return datetime.utcfromtimestamp(value)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            return None
    return None


def pick_variant(pricing: dict) -> Optional[dict]:
    if not pricing:
        return None
    for key in (
        "normal",
        "holofoil",
        "reverse-holofoil",
        "reverse",
        "holo",
        "1st-edition",
        "1st-edition-holofoil",
        "unlimited",
        "unlimited-holofoil",
    ):
        variant = pricing.get(key)
        if isinstance(variant, dict):
            if any(variant.get(field) is not None for field in ("marketPrice", "midPrice", "lowPrice", "highPrice")):
                return variant
    return None


def fetch_json(url: str, retries: int, backoff_seconds: float) -> tuple[Optional[dict], Optional[str]]:
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "PokeVault/1.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
            return payload, None
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None, "404"
            last_error = f"HTTP {exc.code}"
        except Exception as exc:
            last_error = str(exc)
        if attempt < retries:
            time.sleep(backoff_seconds * attempt)
    return None, last_error


def normalize_token(value: str) -> str:
    return "".join(ch for ch in value.lower().strip() if ch.isalnum())


def parse_card_number(value: str) -> str:
    if not value:
        return ""
    cleaned = value.split("/")[0].strip()
    return cleaned


def extract_extended_number(extended_data: list) -> str:
    for item in extended_data or []:
        if not isinstance(item, dict):
            continue
        if item.get("name") == "Number" or item.get("displayName") == "Card Number":
            return parse_card_number(str(item.get("value") or ""))
    return ""


def extract_number_from_name(name: str) -> str:
    if not name:
        return ""
    match = re.search(r"#\s*([A-Za-z]*\d+[A-Za-z0-9]*)", name)
    if match:
        return match.group(1)
    match = re.search(r"([A-Za-z]*\d+[A-Za-z0-9]*)\s*$", name)
    if match:
        return match.group(1)
    return ""


def pick_tcgcsv_variant(prices: list) -> Optional[dict]:
    if not prices:
        return None
    preference = [
        "normal",
        "holofoil",
        "reverseholofoil",
        "reverse",
        "holo",
        "1stedition",
        "1steditionholofoil",
        "unlimited",
        "unlimitedholofoil",
    ]
    by_key = {}
    for price in prices:
        subtype = normalize_token(str(price.get("subTypeName") or ""))
        by_key[subtype] = price
    for key in preference:
        if key in by_key:
            return by_key[key]
    return prices[0] if prices else None


def fetch_tcgcsv_groups(base_url: str, retries: int, backoff_seconds: float) -> list:
    payload, error = fetch_json(f"{base_url}/tcgplayer/3/groups", retries, backoff_seconds)
    if payload and isinstance(payload.get("results"), list):
        return payload["results"]
    raise SystemExit(f"Failed to load TCGCSV groups: {error or 'unknown error'}")


def resolve_tcgcsv_group_id(groups: list, set_name: str, set_code: str) -> Optional[int]:
    if not set_name and not set_code:
        return None
    best = None
    best_score = 0
    set_name_norm = normalize_token(set_name or "")
    set_code_norm = normalize_token(set_code or "")
    set_code_trim = set_code_norm[:-1] if set_code_norm.endswith("p") else set_code_norm
    for group in groups:
        group_name = normalize_token(str(group.get("name") or ""))
        group_abbr = normalize_token(str(group.get("abbreviation") or ""))
        score = 0
        if set_name_norm and group_name == set_name_norm:
            score = 4
        elif set_name_norm and group_name and set_name_norm in group_name:
            score = 3
        elif set_name_norm and group_name and group_name in set_name_norm:
            score = 2
        elif set_code_norm and group_abbr and set_code_norm == group_abbr:
            score = 2
        elif set_code_trim and group_abbr and set_code_trim == group_abbr:
            score = 2
        if score > best_score:
            best_score = score
            best = group
    if not best:
        if set_code_trim:
            promo_key = set_code_trim.upper()
            for group in groups:
                group_name = str(group.get("name") or "").lower()
                group_abbr = str(group.get("abbreviation") or "").upper()
                if "promo" not in group_name:
                    continue
                if group_abbr.startswith(promo_key):
                    return group.get("groupId")
                if promo_key in group_name.replace("&", "and"):
                    return group.get("groupId")
        return None
    return best.get("groupId")


def fetch_tcgcsv_group_products(base_url: str, group_id: int, retries: int, backoff_seconds: float) -> list:
    payload, error = fetch_json(f"{base_url}/tcgplayer/3/{group_id}/products", retries, backoff_seconds)
    if payload and isinstance(payload.get("results"), list):
        return payload["results"]
    raise SystemExit(f"Failed to load TCGCSV products for group {group_id}: {error or 'unknown error'}")


def fetch_tcgcsv_group_prices(base_url: str, group_id: int, retries: int, backoff_seconds: float) -> list:
    payload, error = fetch_json(f"{base_url}/tcgplayer/3/{group_id}/prices", retries, backoff_seconds)
    if payload and isinstance(payload.get("results"), list):
        return payload["results"]
    raise SystemExit(f"Failed to load TCGCSV prices for group {group_id}: {error or 'unknown error'}")


def load_optional_json(path: str) -> dict:
    if not path or not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, dict):
        return data
    return {}


def load_set_metadata(path: str) -> dict:
    if not path or not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    items = []
    if isinstance(data, dict):
        if isinstance(data.get("data"), list):
            items = data["data"]
        elif isinstance(data.get("sets"), list):
            items = data["sets"]
    elif isinstance(data, list):
        items = data
    result = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        code = item.get("id") or item.get("code")
        name = item.get("name")
        if code and name:
            result[str(code)] = str(name)
    return result

def main():
    mode = os.environ.get("SEED_MODE", "tracked")
    set_code = os.environ.get("SET_CODE")
    set_id = os.environ.get("SET_ID")
    limit = os.environ.get("SEED_LIMIT")
    workers = int(os.environ.get("PRICE_WORKERS", "10"))
    retries = int(os.environ.get("PRICE_RETRIES", "3"))
    backoff = float(os.environ.get("PRICE_BACKOFF", "1.5"))
    base_url = os.environ.get("PRICE_BASE_URL", "https://api.tcgdex.net/v2/en")
    tcgcsv_base_url = os.environ.get("TCGCSV_BASE_URL", "https://tcgcsv.com")
    tcgcsv_set_map_path = os.environ.get("TCGCSV_SET_MAP", "/data/tcgcsv_set_map.json")
    tcgcsv_number_overrides_path = os.environ.get("TCGCSV_NUMBER_OVERRIDES", "/data/tcgcsv_number_overrides.json")
    set_metadata_path = os.environ.get("SET_METADATA_PATH", "/data/sets/en.json")
    debug_samples = int(os.environ.get("PRICE_DEBUG_SAMPLES", "0"))
    limit_value = int(limit) if limit else None
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    db = Session()
    print(f"Seeding prices from TCGdex (TCGplayer) for mode={mode}")

    tcgdex_source = db.query(PriceSource).filter(PriceSource.type == "tcgdex_tcgplayer").first()
    if not tcgdex_source:
        tcgdex_source = PriceSource(
            name="TCGplayer via TCGdex",
            type="tcgdex_tcgplayer",
            config_json={"base_url": base_url},
        )
        db.add(tcgdex_source)
        db.commit()

    tcgcsv_source = db.query(PriceSource).filter(PriceSource.type == "tcgcsv_tcgplayer").first()
    if not tcgcsv_source:
        tcgcsv_source = PriceSource(
            name="TCGplayer via TCGCSV",
            type="tcgcsv_tcgplayer",
            config_json={"base_url": tcgcsv_base_url},
        )
        db.add(tcgcsv_source)
        db.commit()

    query = db.query(Card, Set).join(Set, Card.set_id == Set.id)
    if mode == "tracked":
        query = query.join(Holding, Holding.card_id == Card.id).filter(
            or_(
                Holding.is_watched.is_(True),
                Holding.is_wantlist.is_(True),
                Holding.quantity > 0,
                Holding.is_for_trade.is_(True),
            )
        ).distinct()
    elif mode == "set":
        if set_id:
            query = query.filter(Card.set_id == int(set_id))
        elif set_code:
            query = query.filter(Set.code == set_code)
        else:
            raise SystemExit("SEED_MODE=set requires SET_CODE or SET_ID")
    elif mode != "all":
        raise SystemExit("Unsupported SEED_MODE. Use tracked|set|all.")

    if limit_value:
        query = query.limit(limit_value)

    set_name_overrides = load_set_metadata(set_metadata_path)
    rows = query.with_entities(Card.id, Card.number, Card.name, Set.code, Set.name).all()
    tasks = []
    for card_id, number, card_name, set_code_row, set_name in rows:
        if not number or not set_code_row:
            continue
        normalized_set_name = str(set_name or "").strip()
        if not normalized_set_name or normalized_set_name == str(set_code_row).strip():
            normalized_set_name = set_name_overrides.get(str(set_code_row).strip(), normalized_set_name)
        tasks.append({
            "card_id": card_id,
            "number": str(number).strip(),
            "name": str(card_name or "").strip(),
            "set_code": str(set_code_row).strip(),
            "set_name": normalized_set_name,
        })

    total_tasks = len(tasks)
    if total_tasks == 0:
        print("No cards eligible for pricing.")
        return

    log_every = max(1, total_tasks // 20)
    completed = 0
    updated_count = 0
    skipped_count = 0
    error_count = 0
    missing_for_tcgcsv = []
    debug_entries = []
    tcgcsv_debug_entries = []

    def worker(task):
        url = f"{base_url}/cards/{task['set_code']}-{task['number']}"
        payload, error = fetch_json(url, retries, backoff)
        return task, payload, error

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = {executor.submit(worker, task): task for task in tasks}
        for future in concurrent.futures.as_completed(future_map):
            task, payload, error = future.result()
            if payload is None:
                skipped_count += 1
                if error and error != "404":
                    error_count += 1
                completed += 1
            else:
                pricing = payload.get("pricing") or {}
                tcgplayer = pricing.get("tcgplayer") or {}
                variant = pick_variant(tcgplayer)
                if not variant:
                    skipped_count += 1
                    completed += 1
                else:
                    updated_at = parse_updated(tcgplayer.get("updated")) or datetime.utcnow()
                    latest = db.query(LatestPrice).filter(
                        LatestPrice.entity_type == "card",
                        LatestPrice.entity_id == task["card_id"],
                        LatestPrice.source_id == tcgdex_source.id,
                    ).first()
                    if not latest:
                        latest = LatestPrice(
                            entity_type="card",
                            entity_id=task["card_id"],
                            source_id=tcgdex_source.id,
                        )
                        db.add(latest)
                    latest.currency = str(tcgplayer.get("unit") or "USD")
                    latest.market = variant.get("marketPrice")
                    latest.low = variant.get("lowPrice")
                    latest.mid = variant.get("midPrice")
                    latest.high = variant.get("highPrice")
                    latest.updated_at = updated_at
                    db.add(PriceHistory(
                        entity_type="card",
                        entity_id=task["card_id"],
                        source_id=tcgdex_source.id,
                        ts=updated_at,
                        market=latest.market,
                        low=latest.low,
                        mid=latest.mid,
                        high=latest.high,
                    ))
                    updated_count += 1
                    completed += 1
            if payload is not None:
                if not variant:
                    missing_for_tcgcsv.append({**task, "reason": "tcgdex_no_pricing"})
                    if debug_samples and len(debug_entries) < debug_samples:
                        debug_entries.append({**task, "reason": "tcgdex_no_pricing"})
            else:
                missing_for_tcgcsv.append({**task, "reason": "tcgdex_missing"})
                if debug_samples and len(debug_entries) < debug_samples:
                    debug_entries.append({**task, "reason": "tcgdex_missing"})

            if completed % log_every == 0 or completed == total_tasks:
                print(f"Progress {completed}/{total_tasks} | updated={updated_count} | skipped={skipped_count} | errors={error_count}")

    if missing_for_tcgcsv:
        print(f"TCGdex missing pricing for {len(missing_for_tcgcsv)} cards. Falling back to TCGCSV.")
        groups = fetch_tcgcsv_groups(tcgcsv_base_url, retries, backoff)
        tcgcsv_set_map = load_optional_json(tcgcsv_set_map_path)
        tcgcsv_number_overrides = load_optional_json(tcgcsv_number_overrides_path)
        group_cache: dict[str, Optional[int]] = {}
        product_cache: dict[int, dict] = {}
        price_cache: dict[int, dict] = {}
        tcgcsv_updated = 0
        tcgcsv_skipped = 0
        tcgcsv_errors = 0
        tcgcsv_completed = 0
        tcgcsv_log_every = max(1, len(missing_for_tcgcsv) // 20)

        tcgcsv_reason_counts = {
            "tcgcsv_group_missing": 0,
            "tcgcsv_group_fetch_failed": 0,
            "tcgcsv_product_missing": 0,
            "tcgcsv_price_missing": 0,
        }
        group_missing_counts: dict[str, int] = {}
        product_missing_counts: dict[str, int] = {}
        for task in missing_for_tcgcsv:
            set_code_row = task["set_code"]
            set_name = task["set_name"]
            if set_code_row in group_cache:
                group_id = group_cache[set_code_row]
            else:
                override_group = tcgcsv_set_map.get(set_code_row)
                if override_group:
                    group_id = int(override_group)
                else:
                    group_id = resolve_tcgcsv_group_id(groups, set_name, set_code_row)
                group_cache[set_code_row] = group_id
            if not group_id:
                tcgcsv_skipped += 1
                tcgcsv_completed += 1
                tcgcsv_reason_counts["tcgcsv_group_missing"] += 1
                group_missing_counts[set_code_row] = group_missing_counts.get(set_code_row, 0) + 1
                if debug_samples and len(debug_entries) < debug_samples:
                    debug_entries.append({**task, "reason": "tcgcsv_group_missing"})
                if debug_samples and len(tcgcsv_debug_entries) < debug_samples:
                    tcgcsv_debug_entries.append({**task, "reason": "tcgcsv_group_missing"})
            else:
                if group_id not in product_cache:
                    try:
                        products = fetch_tcgcsv_group_products(tcgcsv_base_url, group_id, retries, backoff)
                        prices = fetch_tcgcsv_group_prices(tcgcsv_base_url, group_id, retries, backoff)
                    except Exception:
                        tcgcsv_errors += 1
                        tcgcsv_completed += 1
                        tcgcsv_reason_counts["tcgcsv_group_fetch_failed"] += 1
                        if debug_samples and len(debug_entries) < debug_samples:
                            debug_entries.append({**task, "reason": "tcgcsv_group_fetch_failed"})
                        if debug_samples and len(tcgcsv_debug_entries) < debug_samples:
                            tcgcsv_debug_entries.append({**task, "reason": "tcgcsv_group_fetch_failed"})
                        continue
                    products_by_id = {p.get("productId"): p for p in products if isinstance(p, dict)}
                    number_map = {}
                    for product in products_by_id.values():
                        number_value = extract_extended_number(product.get("extendedData") or [])
                        if not number_value:
                            number_value = extract_number_from_name(str(product.get("name") or ""))
                        if not number_value:
                            continue
                        key = normalize_token(number_value)
                        number_map.setdefault(key, []).append(product.get("productId"))
                    prices_by_product = {}
                    for price in prices:
                        product_id = price.get("productId")
                        if product_id is None:
                            continue
                        prices_by_product.setdefault(product_id, []).append(price)
                    product_cache[group_id] = {
                        "products": products_by_id,
                        "number_map": number_map,
                    }
                    price_cache[group_id] = prices_by_product

                override_map = tcgcsv_number_overrides.get(set_code_row, {})
                override_value = override_map.get(task["number"])
                explicit_product_id = None
                number_value = task["number"]
                if isinstance(override_value, dict):
                    explicit_product_id = override_value.get("productId")
                    if override_value.get("number"):
                        number_value = str(override_value.get("number"))
                elif isinstance(override_value, (str, int)):
                    number_value = str(override_value)
                number_key = normalize_token(parse_card_number(number_value))
                group_products = product_cache[group_id]
                if explicit_product_id:
                    candidates = [explicit_product_id]
                else:
                    candidates = group_products["number_map"].get(number_key, [])
                if not candidates:
                    tcgcsv_skipped += 1
                    tcgcsv_completed += 1
                    tcgcsv_reason_counts["tcgcsv_product_missing"] += 1
                    product_missing_counts[set_code_row] = product_missing_counts.get(set_code_row, 0) + 1
                    if debug_samples and len(debug_entries) < debug_samples:
                        debug_entries.append({**task, "reason": "tcgcsv_product_missing"})
                    if debug_samples and len(tcgcsv_debug_entries) < debug_samples:
                        tcgcsv_debug_entries.append({**task, "reason": "tcgcsv_product_missing"})
                else:
                    card_name_norm = normalize_token(task["name"])
                    selected_product_id = None
                    for product_id in candidates:
                        product = group_products["products"].get(product_id) or {}
                        product_name_norm = normalize_token(str(product.get("name") or ""))
                        if card_name_norm and product_name_norm == card_name_norm:
                            selected_product_id = product_id
                            break
                    if not selected_product_id:
                        selected_product_id = candidates[0]
                    price_entries = price_cache[group_id].get(selected_product_id, [])
                    variant = pick_tcgcsv_variant(price_entries)
                    if not variant:
                        tcgcsv_skipped += 1
                        tcgcsv_completed += 1
                        tcgcsv_reason_counts["tcgcsv_price_missing"] += 1
                        if debug_samples and len(debug_entries) < debug_samples:
                            debug_entries.append({**task, "reason": "tcgcsv_price_missing"})
                        if debug_samples and len(tcgcsv_debug_entries) < debug_samples:
                            tcgcsv_debug_entries.append({**task, "reason": "tcgcsv_price_missing"})
                    else:
                        updated_at = datetime.utcnow()
                        latest = db.query(LatestPrice).filter(
                            LatestPrice.entity_type == "card",
                            LatestPrice.entity_id == task["card_id"],
                            LatestPrice.source_id == tcgcsv_source.id,
                        ).first()
                        if not latest:
                            latest = LatestPrice(
                                entity_type="card",
                                entity_id=task["card_id"],
                                source_id=tcgcsv_source.id,
                            )
                            db.add(latest)
                        latest.currency = "USD"
                        latest.market = variant.get("marketPrice")
                        latest.low = variant.get("lowPrice")
                        latest.mid = variant.get("midPrice")
                        latest.high = variant.get("highPrice")
                        latest.updated_at = updated_at
                        db.add(PriceHistory(
                            entity_type="card",
                            entity_id=task["card_id"],
                            source_id=tcgcsv_source.id,
                            ts=updated_at,
                            market=latest.market,
                            low=latest.low,
                            mid=latest.mid,
                            high=latest.high,
                        ))
                        tcgcsv_updated += 1
                        tcgcsv_completed += 1

            if tcgcsv_completed % tcgcsv_log_every == 0 or tcgcsv_completed == len(missing_for_tcgcsv):
                print(f"TCGCSV progress {tcgcsv_completed}/{len(missing_for_tcgcsv)} | updated={tcgcsv_updated} | skipped={tcgcsv_skipped} | errors={tcgcsv_errors}")
        print(
            "TCGCSV skip reasons:"
            f" group_missing={tcgcsv_reason_counts['tcgcsv_group_missing']}"
            f" product_missing={tcgcsv_reason_counts['tcgcsv_product_missing']}"
            f" price_missing={tcgcsv_reason_counts['tcgcsv_price_missing']}"
            f" group_fetch_failed={tcgcsv_reason_counts['tcgcsv_group_fetch_failed']}"
        )
        if group_missing_counts:
            top = sorted(group_missing_counts.items(), key=lambda item: item[1], reverse=True)[:20]
            print("TCGCSV group_missing top sets:")
            for set_code_row, count in top:
                print(f"{set_code_row}: {count}")
        if product_missing_counts:
            top = sorted(product_missing_counts.items(), key=lambda item: item[1], reverse=True)[:20]
            print("TCGCSV product_missing top sets:")
            for set_code_row, count in top:
                print(f"{set_code_row}: {count}")

    db.commit()
    print(f"Updated {updated_count} prices from TCGdex, skipped {skipped_count}, errors {error_count}")
    if debug_entries:
        print("Sample missing cards (for manual mapping):")
        for entry in debug_entries:
            print(f"{entry['reason']} | {entry['set_code']} | {entry['number']} | {entry['name']}")
    if tcgcsv_debug_entries:
        print("Sample TCGCSV misses (for manual mapping):")
        for entry in tcgcsv_debug_entries:
            print(f"{entry['reason']} | {entry['set_code']} | {entry['number']} | {entry['name']}")


if __name__ == "__main__":
    main()
