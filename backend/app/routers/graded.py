import json
import os
import time
import urllib.error
import re
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from typing import Optional

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.models import Card, ExternalId, GradedItem, LatestPrice, PriceHistory, PriceSource, Set, TagDetail, User
from app.schemas import GradedCreate, GradedOut

router = APIRouter()
logger = logging.getLogger("uvicorn.error")


@router.post("", response_model=GradedOut)
def create_graded(payload: GradedCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    graded = GradedItem(user_id=current_user.id, **payload.model_dump())
    db.add(graded)
    db.commit()
    db.refresh(graded)
    return graded


@router.get("")
def list_graded(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = db.query(GradedItem).filter(GradedItem.user_id == current_user.id).all()
    return [GradedOut.model_validate(row) for row in rows]


@router.post("/upsert")
def upsert_graded(payload: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    card_id = payload.get("card_id")
    grader = payload.get("grader")
    grade = payload.get("grade")
    if not card_id or not grader or not grade:
        raise HTTPException(status_code=400, detail="card_id, grader, and grade are required")
    graded = db.query(GradedItem).filter(
        GradedItem.user_id == current_user.id,
        GradedItem.card_id == card_id,
    ).first()
    if graded:
        graded.grader = grader
        graded.grade = str(grade)
    else:
        graded = GradedItem(
            user_id=current_user.id,
            card_id=card_id,
            grader=grader,
            grade=str(grade),
        )
        db.add(graded)
    db.commit()
    db.refresh(graded)
    return GradedOut.model_validate(graded)


def fetch_json(url: str, retries: int, backoff_seconds: float, api_key: Optional[str]) -> tuple[Optional[dict], Optional[str]]:
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            headers = {"User-Agent": "PokeVault/1.0"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
                headers["X-API-Key"] = api_key
            req = urllib.request.Request(url, headers=headers)
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


def extract_card_id(payload: dict) -> Optional[str]:
    if not payload:
        return None
    if isinstance(payload.get("card"), dict) and payload["card"].get("id"):
        return str(payload["card"]["id"])
    if payload.get("id"):
        return str(payload["id"])
    return None


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


def price_key_for_grade(grader: str, grade: str) -> Optional[str]:
    normalized_grader = str(grader).strip().upper()
    normalized_grade = str(grade).strip()
    if not normalized_grader:
        return None
    normalized_grade = normalized_grade.replace(" ", "").replace("-", "").replace("_", ".")
    return f"{normalized_grader.lower()}_{normalized_grade}"


def price_key_for_v2(grader: str, grade: str) -> Optional[list[str]]:
    normalized_grader = str(grader).strip().lower()
    normalized_grade = str(grade).strip().replace(" ", "").replace("-", "").replace("_", "")
    if not normalized_grader:
        return None
    return [
        f"{normalized_grader}{normalized_grade}",
        f"{normalized_grader}{normalized_grade.replace('.', '')}",
    ]


def slugify_set_name(value: str) -> str:
    if not value:
        return ""
    cleaned = value.lower().replace("&", "and")
    cleaned = re.sub(r"[^a-z0-9]+", "-", cleaned)
    return cleaned.strip("-")


def normalize_number(value: str) -> str:
    if not value:
        return ""
    return value.split("/")[0].strip().lstrip("0") or value.split("/")[0].strip()


def fetch_v2_set_id(base_url: str, set_name: str, retries: int, backoff: float, api_key: str, debug: bool) -> Optional[str]:
    if not set_name:
        return None
    query = urllib.parse.urlencode({"search": set_name, "limit": 50, "offset": 0})
    url = f"{base_url}/api/v2/sets?{query}"
    payload, error = fetch_json(url, retries, backoff, api_key)
    if debug:
        logger.info("[graded] v2 sets url=%s err=%s payload_keys=%s", url, error, list((payload or {}).keys()))
    if error == "HTTP 401":
        raise HTTPException(status_code=401, detail="PokemonPriceTracker API key rejected")
    data = (payload or {}).get("data") or []
    normalized = set_name.strip().lower()
    for entry in data:
        name = str(entry.get("name") or "").strip().lower()
        if name == normalized and entry.get("id"):
            return str(entry["id"])
    if data and data[0].get("id"):
        return str(data[0]["id"])
    return None


def extract_graded_block(payload: dict) -> dict:
    if not payload:
        return {}
    if isinstance(payload.get("graded"), dict):
        return payload["graded"]
    if isinstance(payload.get("gradedPrices"), dict):
        return payload["gradedPrices"]
    if isinstance(payload.get("graded_prices"), dict):
        return payload["graded_prices"]
    prices = payload.get("prices")
    if isinstance(prices, dict) and isinstance(prices.get("graded"), dict):
        return prices["graded"]
    return {}


def normalize_grade_key(grader: str, grade: str) -> str:
    grader_key = str(grader).strip().lower()
    grade_key = str(grade).strip().replace(" ", "").replace("-", "").replace("_", "").lower()
    return f"{grader_key}{grade_key}"


def extract_sales_by_grade(payload: dict) -> dict:
    if not payload:
        return {}
    sales = payload.get("salesByGrade")
    if isinstance(sales, dict):
        return sales
    ebay = payload.get("ebay")
    if isinstance(ebay, dict) and isinstance(ebay.get("salesByGrade"), dict):
        return ebay["salesByGrade"]
    return {}


def compute_sales_average(sales: object, mode: str, max_days: int) -> Optional[float]:
    if not sales:
        return None
    if isinstance(sales, dict):
        # Prefer provided averages if present.
        if sales.get("smartMarketPrice") and isinstance(sales["smartMarketPrice"], dict):
            price = sales["smartMarketPrice"].get("price")
            if isinstance(price, (int, float)):
                return float(price)
        if isinstance(sales.get("averagePrice"), (int, float)):
            return float(sales["averagePrice"])
        if isinstance(sales.get("medianPrice"), (int, float)):
            return float(sales["medianPrice"])
        return None
    if not isinstance(sales, list):
        return None
    now = datetime.utcnow()
    entries = []
    for entry in sales:
        if not isinstance(entry, dict):
            continue
        price = entry.get("price") or entry.get("salePrice") or entry.get("amount")
        ts = entry.get("date") or entry.get("soldAt") or entry.get("timestamp")
        if price is None or ts is None:
            continue
        try:
            price_value = float(price)
        except (TypeError, ValueError):
            continue
        sale_time = None
        if isinstance(ts, (int, float)):
            try:
                sale_time = datetime.utcfromtimestamp(ts)
            except Exception:
                sale_time = None
        elif isinstance(ts, str):
            try:
                sale_time = datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=None)
            except ValueError:
                sale_time = None
        if sale_time is None:
            continue
        entries.append({"price": price_value, "ts": sale_time})
    if not entries:
        return None
    entries.sort(key=lambda row: row["ts"], reverse=True)
    if mode == "last3":
        entries = entries[:3]
    else:
        cutoff = now - timedelta(days=max_days)
        entries = [row for row in entries if row["ts"] >= cutoff]
    if not entries:
        return None
    return sum(row["price"] for row in entries) / len(entries)


def ensure_price_source(db: Session, source_type: str, name: str):
    source = db.query(PriceSource).filter(PriceSource.type == source_type).first()
    if source:
        return source
    source = PriceSource(name=name, type=source_type, config_json={})
    db.add(source)
    db.commit()
    return source


@router.post("/prices")
def graded_prices(payload: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    graded_ids = payload.get("graded_ids") or []
    if not isinstance(graded_ids, list) or not graded_ids:
        return {"prices": []}

    latest_rows = (
        db.query(LatestPrice, PriceSource)
        .join(PriceSource, LatestPrice.source_id == PriceSource.id)
        .filter(LatestPrice.entity_type == "graded", LatestPrice.entity_id.in_(graded_ids))
        .all()
    )
    latest_map = {}
    for price, source in latest_rows:
        latest_map[price.entity_id] = {
            "graded_id": price.entity_id,
            "market": price.market,
            "source": source.name,
            "source_type": source.type,
        }

    return {"prices": list(latest_map.values())}


@router.post("/fetch-price")
def fetch_graded_price(payload: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    card_id = payload.get("card_id")
    grader = payload.get("grader")
    grade = payload.get("grade")
    if not card_id or not grader or not grade:
        raise HTTPException(status_code=400, detail="card_id, grader, and grade are required")

    api_key = os.environ.get("POKEMONPRICETRACKER_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="POKEMONPRICETRACKER_API_KEY is not set")
    debug = os.environ.get("DEBUG_GRADED_LOOKUP") == "1"
    if debug:
        logger.info(
            "[graded] start card_id=%s grader=%s grade=%s",
            payload.get("card_id"),
            payload.get("grader"),
            payload.get("grade"),
        )

    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    set_row = db.query(Set).filter(Set.id == card.set_id).first()
    if not set_row:
        raise HTTPException(status_code=404, detail="Set not found")

    graded = db.query(GradedItem).filter(
        GradedItem.user_id == current_user.id,
        GradedItem.card_id == card_id,
    ).first()
    if graded:
        graded.grader = grader
        graded.grade = str(grade)
    else:
        graded = GradedItem(
            user_id=current_user.id,
            card_id=card_id,
            grader=grader,
            grade=str(grade),
        )
        db.add(graded)
    db.commit()
    db.refresh(graded)

    price_key = price_key_for_grade(grader, grade)
    if not price_key:
        raise HTTPException(status_code=400, detail="Unsupported grader/grade for pricing")

    retries = int(os.environ.get("PRICE_RETRIES", "2"))
    backoff = float(os.environ.get("PRICE_BACKOFF", "1.2"))
    base_url = os.environ.get("POKEMONPRICETRACKER_BASE_URL", "https://www.pokemonpricetracker.com")
    allow_fetch_all = os.environ.get("POKEMONPRICETRACKER_FETCH_ALL") == "1"
    include_ebay = os.environ.get("POKEMONPRICETRACKER_INCLUDE_EBAY") == "1"
    set_metadata_path = os.environ.get("SET_METADATA_PATH", "/data/sets/en.json")
    set_name_overrides = load_set_metadata(set_metadata_path)
    number_value = str(card.number).split("/")[0].strip()
    resolved_set_name = (set_row.name or "").strip()
    if set_name_overrides.get(set_row.code):
        resolved_set_name = set_name_overrides.get(set_row.code)
    elif not resolved_set_name or resolved_set_name == set_row.code:
        resolved_set_name = set_name_overrides.get(set_row.code, resolved_set_name)

    external = db.query(ExternalId).filter(
        ExternalId.entity_type == "card",
        ExternalId.entity_id == card.id,
        ExternalId.source == "pokemonpricetracker",
    ).first()
    card_ref = external.external_id if external else None
    if debug and card_ref:
        logger.info("[graded] using cached card_ref=%s", card_ref)
    # Skip v1 endpoints to reduce API usage and rate limit hits; use v2 only.
    if card_ref:
        detail_url = f"{base_url}/api/v2/cards?cardId={urllib.parse.quote(str(card_ref))}&limit=1&includeEbay={'true' if include_ebay else 'false'}"
        detail_payload, detail_error = fetch_json(detail_url, retries, backoff, api_key)
        if debug:
            logger.info("[graded] v2 detail url=%s err=%s", detail_url, detail_error)
        detail_data = (detail_payload or {}).get("data") or []
        detail_entry = detail_data[0] if detail_data else {}
        graded_prices = extract_graded_block(detail_entry)
        if graded_prices:
            grader_key = str(grader).strip().lower()
            grade_key = str(grade).strip().replace(" ", "").replace("-", "").replace("_", ".")
            market_value = (graded_prices.get(grader_key) or {}).get(grade_key)
            if market_value is not None:
                try:
                    market_value = float(market_value)
                except (TypeError, ValueError):
                    raise HTTPException(status_code=400, detail="Invalid price format")
                source = ensure_price_source(db, "pokemonpricetracker", "PokemonPriceTracker")
                existing = db.query(LatestPrice).filter(
                    LatestPrice.entity_type == "graded",
                    LatestPrice.entity_id == graded.id,
                    LatestPrice.source_id == source.id,
                ).first()
                if existing and existing.updated_at:
                    age_seconds = (datetime.utcnow() - existing.updated_at).total_seconds()
                    if age_seconds < 3600:
                        return {
                            "graded_id": graded.id,
                            "market": existing.market,
                            "source": source.name,
                            "source_type": source.type,
                            "cached": True,
                        }
                updated_at = datetime.utcnow()
                latest = existing or LatestPrice(
                    entity_type="graded",
                    entity_id=graded.id,
                    source_id=source.id,
                )
                if existing is None:
                    db.add(latest)
                latest.currency = "USD"
                latest.market = market_value
                latest.updated_at = updated_at
                db.add(PriceHistory(
                    entity_type="graded",
                    entity_id=graded.id,
                    source_id=source.id,
                    ts=updated_at,
                    market=market_value,
                ))
                db.commit()
                return {
                    "graded_id": graded.id,
                    "market": market_value,
                    "source": source.name,
                    "source_type": source.type,
                    "cached": False,
                }
        sales_by_grade = extract_sales_by_grade(detail_entry)
        if debug:
            logger.info("[graded] salesByGrade keys=%s", list(sales_by_grade.keys()))
        if sales_by_grade:
            grade_key = normalize_grade_key(grader, grade)
            sales = sales_by_grade.get(grade_key) or []
            mode = os.environ.get("GRADED_SALES_MODE", "last3")
            max_days = int(os.environ.get("GRADED_SALES_MAX_DAYS", "30"))
            average = compute_sales_average(sales, mode, max_days)
            if average is not None:
                source = ensure_price_source(db, "pokemonpricetracker_ebay", "PokemonPriceTracker (eBay)")
                updated_at = datetime.utcnow()
                latest = db.query(LatestPrice).filter(
                    LatestPrice.entity_type == "graded",
                    LatestPrice.entity_id == graded.id,
                    LatestPrice.source_id == source.id,
                ).first()
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
                return {
                    "graded_id": graded.id,
                    "market": average,
                    "source": source.name,
                    "source_type": source.type,
                    "cached": False,
                }
        if include_ebay:
            search_params = {
                "setName": resolved_set_name,
                "cardNumber": normalize_number(number_value),
                "search": card.name,
                "limit": 1,
                "offset": 0,
                "includeEbay": "true",
                "language": "english",
            }
            search_url = f"{base_url}/api/v2/cards?{urllib.parse.urlencode({k: v for k, v in search_params.items() if v})}"
            search_payload, search_error = fetch_json(search_url, retries, backoff, api_key)
            if debug:
                logger.info("[graded] v2 search url=%s err=%s", search_url, search_error)
            search_data = (search_payload or {}).get("data") or []
            search_entry = search_data[0] if search_data else {}
            sales_by_grade = extract_sales_by_grade(search_entry)
            if debug:
                logger.info("[graded] search salesByGrade keys=%s", list(sales_by_grade.keys()))
            if sales_by_grade:
                grade_key = normalize_grade_key(grader, grade)
                sales = sales_by_grade.get(grade_key) or []
                mode = os.environ.get("GRADED_SALES_MODE", "last3")
                max_days = int(os.environ.get("GRADED_SALES_MAX_DAYS", "30"))
                average = compute_sales_average(sales, mode, max_days)
                if average is not None:
                    source = ensure_price_source(db, "pokemonpricetracker_ebay", "PokemonPriceTracker (eBay)")
                    updated_at = datetime.utcnow()
                    latest = db.query(LatestPrice).filter(
                        LatestPrice.entity_type == "graded",
                        LatestPrice.entity_id == graded.id,
                        LatestPrice.source_id == source.id,
                    ).first()
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
                    return {
                        "graded_id": graded.id,
                        "market": average,
                        "source": source.name,
                        "source_type": source.type,
                        "cached": False,
                    }
        if debug:
            logger.info("[graded] cached card_ref had no graded price; keeping cache")
        card_ref = None

    search_entry = None
    if not card_ref:
        normalized_number = normalize_number(number_value)
        set_slug = slugify_set_name(resolved_set_name or set_row.code)
        set_id = fetch_v2_set_id(base_url, resolved_set_name, retries, backoff, api_key, debug)
        if set_id:
            set_slug = set_id
        if debug:
            logger.info(
                "[graded] resolved set_name=%s set_slug=%s number=%s",
                resolved_set_name,
                set_slug,
                normalized_number,
            )
        card_number_full = str(card.number).split("/")[0].strip()
        query_variants = [
            {"setName": resolved_set_name, "cardNumber": normalized_number, "search": card.name},
            {"setName": resolved_set_name, "cardNumber": card_number_full, "search": card.name},
            {"setId": set_slug, "cardNumber": normalized_number},
        ]
        data = []
        for params in query_variants:
            params.update({
                "limit": 50,
                "offset": 0,
                "fetchAllInSet": "false",
                "language": "english",
                "includeEbay": "true" if include_ebay else "false",
            })
            v2_url = f"{base_url}/api/v2/cards?{urllib.parse.urlencode({k: v for k, v in params.items() if v})}"
            v2_payload, v2_error = fetch_json(v2_url, retries, backoff, api_key)
            if debug:
                meta = (v2_payload or {}).get("metadata")
                logger.info("[graded] v2 url=%s err=%s meta=%s", v2_url, v2_error, meta)
            if v2_error == "HTTP 401":
                raise HTTPException(status_code=401, detail="PokemonPriceTracker API key rejected")
            if v2_error == "HTTP 429":
                raise HTTPException(status_code=429, detail="PokemonPriceTracker rate limit exceeded")
            data = (v2_payload or {}).get("data") or []
            if data:
                break
        if not data and allow_fetch_all and set_slug:
            fetch_all_params = {
                "setId": set_slug,
                "fetchAllInSet": "true",
                "limit": 500,
                "offset": 0,
                "includeEbay": "true" if include_ebay else "false",
            }
            fetch_all_url = f"{base_url}/api/v2/cards?{urllib.parse.urlencode(fetch_all_params)}"
            fetch_all_payload, fetch_all_error = fetch_json(fetch_all_url, retries, backoff, api_key)
            if debug:
                print(f"[graded] v2 fetchAll url={fetch_all_url} err={fetch_all_error} payload_keys={list((fetch_all_payload or {}).keys())}")
            data = (fetch_all_payload or {}).get("data") or []
        match = None
        for entry in data:
            entry_number = normalize_number(str(entry.get("cardNumber") or ""))
            entry_name = str(entry.get("name") or "").strip().lower()
            if entry_number == normalized_number and (not entry_name or entry_name == card.name.strip().lower()):
                match = entry
                break
        if not match:
            for entry in data:
                entry_number = normalize_number(str(entry.get("cardNumber") or ""))
                if entry_number == normalized_number or str(entry.get("cardNumber") or "") == card_number_full:
                    match = entry
                    break
        if not match:
            for entry in data:
                entry_name = str(entry.get("name") or "").strip().lower()
                if card.name.strip().lower() in entry_name:
                    match = entry
                    break
        if not match and len(data) == 1:
            match = data[0]
        if debug and not match:
            sample = []
            for entry in data[:3]:
                sample.append({
                    "id": entry.get("id"),
                    "name": entry.get("name"),
                    "cardNumber": entry.get("cardNumber"),
                })
            logger.info(
                "[graded] v2 no match normalized_number=%s card_name=%s sample=%s",
                normalized_number,
                card.name,
                sample,
            )
        if debug and match:
            logger.info(
                "[graded] v2 matched id=%s name=%s number=%s",
                match.get("id"),
                match.get("name"),
                match.get("cardNumber"),
            )
        if match and match.get("id"):
            card_ref = str(match["id"])
            db.add(ExternalId(
                entity_type="card",
                entity_id=card.id,
                source="pokemonpricetracker",
                external_id=card_ref,
            ))
            db.commit()
        search_entry = match

    if search_entry:
        sales_by_grade = extract_sales_by_grade(search_entry)
        if debug:
            logger.info("[graded] search salesByGrade keys=%s", list(sales_by_grade.keys()))
        if sales_by_grade:
            grade_key = normalize_grade_key(grader, grade)
            sales = sales_by_grade.get(grade_key) or []
            mode = os.environ.get("GRADED_SALES_MODE", "last3")
            max_days = int(os.environ.get("GRADED_SALES_MAX_DAYS", "30"))
            average = compute_sales_average(sales, mode, max_days)
            if average is not None:
                source = ensure_price_source(db, "pokemonpricetracker_ebay", "PokemonPriceTracker (eBay)")
                updated_at = datetime.utcnow()
                latest = db.query(LatestPrice).filter(
                    LatestPrice.entity_type == "graded",
                    LatestPrice.entity_id == graded.id,
                    LatestPrice.source_id == source.id,
                ).first()
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
                return {
                    "graded_id": graded.id,
                    "market": average,
                    "source": source.name,
                    "source_type": source.type,
                    "cached": False,
                }

    if not card_ref:
        if debug:
            logger.info("[graded] no card_ref found")
        raise HTTPException(status_code=404, detail="Card reference not found in PokemonPriceTracker response")

    url = f"{base_url}/api/v2/cards?cardId={urllib.parse.quote(str(card_ref))}&limit=1&includeEbay={'true' if include_ebay else 'false'}"
    payload_data, price_error = fetch_json(url, retries, backoff, api_key)
    if debug:
        logger.info("[graded] v2 graded url=%s err=%s payload_keys=%s", url, price_error, list((payload_data or {}).keys()))
    if not payload_data:
        raise HTTPException(status_code=404, detail="Price not found")

    data = (payload_data or {}).get("data") or []
    entry = data[0] if data else {}
    graded_prices = extract_graded_block(entry)
    grader_key = str(grader).strip().lower()
    grade_key = str(grade).strip().replace(" ", "").replace("-", "").replace("_", ".")
    market_value = (graded_prices.get(grader_key) or {}).get(grade_key)
    if market_value is None:
        sales_by_grade = extract_sales_by_grade(entry)
        if not sales_by_grade and search_entry:
            sales_by_grade = extract_sales_by_grade(search_entry)
        if debug:
            logger.info("[graded] salesByGrade keys=%s", list(sales_by_grade.keys()))
        if sales_by_grade:
            grade_key = normalize_grade_key(grader, grade)
            sales = sales_by_grade.get(grade_key) or []
            mode = os.environ.get("GRADED_SALES_MODE", "last3")
            max_days = int(os.environ.get("GRADED_SALES_MAX_DAYS", "30"))
            average = compute_sales_average(sales, mode, max_days)
            if average is not None:
                market_value = average
                source = ensure_price_source(db, "pokemonpricetracker_ebay", "PokemonPriceTracker (eBay)")
                updated_at = datetime.utcnow()
                latest = db.query(LatestPrice).filter(
                    LatestPrice.entity_type == "graded",
                    LatestPrice.entity_id == graded.id,
                    LatestPrice.source_id == source.id,
                ).first()
                if not latest:
                    latest = LatestPrice(
                        entity_type="graded",
                        entity_id=graded.id,
                        source_id=source.id,
                    )
                    db.add(latest)
                latest.currency = "USD"
                latest.market = market_value
                latest.updated_at = updated_at
                db.add(PriceHistory(
                    entity_type="graded",
                    entity_id=graded.id,
                    source_id=source.id,
                    ts=updated_at,
                    market=market_value,
                ))
                db.commit()
                return {
                    "graded_id": graded.id,
                    "market": market_value,
                    "source": source.name,
                    "source_type": source.type,
                    "cached": False,
                }
            available = ", ".join(sorted(sales_by_grade.keys()))
            raise HTTPException(status_code=404, detail=f"Grade price not available. Available grades: {available}")
        if debug:
            logger.info(
                "[graded] grade missing grader=%s grade=%s graded_keys=%s",
                grader_key,
                grade_key,
                list(graded_prices.keys()),
            )
        raise HTTPException(status_code=404, detail="Grade price not available")
    try:
        market_value = float(market_value)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid price format")

    source = ensure_price_source(db, "pokemonpricetracker", "PokemonPriceTracker")
    existing = db.query(LatestPrice).filter(
        LatestPrice.entity_type == "graded",
        LatestPrice.entity_id == graded.id,
        LatestPrice.source_id == source.id,
    ).first()
    if existing and existing.updated_at:
        age_seconds = (datetime.utcnow() - existing.updated_at).total_seconds()
        if age_seconds < 3600:
            return {
                "graded_id": graded.id,
                "market": existing.market,
                "source": source.name,
                "source_type": source.type,
                "cached": True,
            }
    updated_at = datetime.utcnow()
    latest = existing or LatestPrice(
        entity_type="graded",
        entity_id=graded.id,
        source_id=source.id,
    )
    if existing is None:
        db.add(latest)
    latest.currency = "USD"
    latest.market = market_value
    latest.updated_at = updated_at
    db.add(PriceHistory(
        entity_type="graded",
        entity_id=graded.id,
        source_id=source.id,
        ts=updated_at,
        market=market_value,
    ))
    db.commit()
    return {
        "graded_id": graded.id,
        "market": market_value,
        "source": source.name,
        "source_type": source.type,
        "cached": False,
    }

@router.patch("/{graded_id}", response_model=GradedOut)
def update_graded(graded_id: int, payload: GradedCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    graded = db.query(GradedItem).filter(GradedItem.id == graded_id, GradedItem.user_id == current_user.id).first()
    if not graded:
        raise HTTPException(status_code=404, detail="Graded item not found")
    for key, value in payload.model_dump().items():
        setattr(graded, key, value)
    db.commit()
    db.refresh(graded)
    return graded


@router.get("/{graded_id}")
def graded_detail(graded_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    graded = db.query(GradedItem).filter(GradedItem.id == graded_id, GradedItem.user_id == current_user.id).first()
    if not graded:
        raise HTTPException(status_code=404, detail="Graded item not found")
    tag_details = db.query(TagDetail).filter(TagDetail.graded_item_id == graded_id).first()
    return {
        "graded": GradedOut.model_validate(graded),
        "tag_details": tag_details.subgrades_json if tag_details else None,
    }
