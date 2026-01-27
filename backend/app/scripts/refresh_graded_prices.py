import os
import time
import urllib.parse
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import Card, GradedItem, LatestPrice, PriceHistory, Set
from app.routers.graded import (
    compute_sales_average,
    extract_sales_by_grade,
    fetch_json,
    load_set_metadata,
    normalize_grade_key,
    normalize_number,
    ensure_price_source,
)


def main():
    api_key = os.environ.get("POKEMONPRICETRACKER_API_KEY")
    if not api_key:
        raise SystemExit("POKEMONPRICETRACKER_API_KEY is not set")
    base_url = os.environ.get("POKEMONPRICETRACKER_BASE_URL", "https://www.pokemonpricetracker.com")
    retries = int(os.environ.get("PRICE_RETRIES", "2"))
    backoff = float(os.environ.get("PRICE_BACKOFF", "1.2"))
    mode = os.environ.get("GRADED_SALES_MODE", "last3")
    max_days = int(os.environ.get("GRADED_SALES_MAX_DAYS", "30"))
    limit = int(os.environ.get("GRADED_REFRESH_LIMIT", "0"))
    sleep_seconds = float(os.environ.get("GRADED_REFRESH_SLEEP", "0"))
    set_metadata_path = os.environ.get("SET_METADATA_PATH", "/data/sets/en.json")
    set_name_overrides = load_set_metadata(set_metadata_path)

    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        rows = (
            db.query(GradedItem, Card, Set)
            .join(Card, GradedItem.card_id == Card.id)
            .join(Set, Card.set_id == Set.id)
            .order_by(GradedItem.id.asc())
            .all()
        )
        if limit > 0:
            rows = rows[:limit]

        if not rows:
            print("No graded items found.")
            return

        source = ensure_price_source(db, "pokemonpricetracker_ebay", "PokemonPriceTracker (eBay)")
        updated_at = datetime.utcnow()

        for graded, card, set_row in rows:
            resolved_set_name = (set_row.name or "").strip()
            if set_name_overrides.get(set_row.code):
                resolved_set_name = set_name_overrides.get(set_row.code)
            number_value = normalize_number(str(card.number).split("/")[0].strip())
            params = {
                "setName": resolved_set_name,
                "cardNumber": number_value,
                "search": card.name,
                "limit": 1,
                "offset": 0,
                "includeEbay": "true",
                "language": "english",
            }
            url = f"{base_url}/api/v2/cards?{urllib.parse.urlencode({k: v for k, v in params.items() if v})}"
            payload, error = fetch_json(url, retries, backoff, api_key)
            if error == "HTTP 401":
                raise SystemExit("PokemonPriceTracker API key rejected")
            data = (payload or {}).get("data") or []
            entry = data[0] if data else {}
            sales_by_grade = extract_sales_by_grade(entry)
            grade_key = normalize_grade_key(graded.grader, graded.grade)
            sales = sales_by_grade.get(grade_key) or []
            average = compute_sales_average(sales, mode, max_days)
            if average is None:
                print(f"[skip] {card.name} {graded.grader} {graded.grade} no sales data")
                continue

            latest = (
                db.query(LatestPrice)
                .filter(
                    LatestPrice.entity_type == "graded",
                    LatestPrice.entity_id == graded.id,
                    LatestPrice.source_id == source.id,
                )
                .first()
            )
            if not latest:
                latest = LatestPrice(
                    entity_type="graded",
                    entity_id=graded.id,
                    source_id=source.id,
                )
                db.add(latest)
            latest.currency = "USD"
            latest.market = average
            latest.updated_at = updated_at
            db.add(PriceHistory(
                entity_type="graded",
                entity_id=graded.id,
                source_id=source.id,
                ts=updated_at,
                market=average,
            ))
            db.commit()
            print(f"[ok] {card.name} {graded.grader} {graded.grade} = {average:.2f}")
            if sleep_seconds:
                time.sleep(sleep_seconds)
    finally:
        db.close()


if __name__ == "__main__":
    main()
