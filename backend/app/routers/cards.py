import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.models import Card, CardImage, LatestPrice, PriceHistory, PriceSource, Set
from app.schemas import CardOut, SetOut

router = APIRouter()


@router.get("/sets", response_model=list[SetOut])
def list_sets(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return db.query(Set).order_by(Set.release_date.desc().nullslast()).all()


@router.get("/sets/{set_id}/cards", response_model=list[CardOut])
def list_set_cards(set_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return db.query(Card).filter(Card.set_id == set_id).order_by(Card.number).all()


@router.get("/cards/search", response_model=list[CardOut])
def search_cards(
    q: str = "",
    rarity: str | None = None,
    artist: str | None = None,
    set_id: int | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(Card)
    if q:
        query = query.filter(Card.name.ilike(f"%{q}%"))
    if rarity:
        query = query.filter(Card.rarity == rarity)
    if artist:
        query = query.filter(Card.artist == artist)
    if set_id:
        query = query.filter(Card.set_id == set_id)
    return query.limit(100).all()


@router.get("/cards/{card_id}")
def card_detail(card_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    card = db.query(Card).filter(Card.id == card_id).first()
    images = db.query(CardImage).filter(CardImage.card_id == card_id).all()
    latest = db.query(LatestPrice, PriceSource).join(PriceSource, LatestPrice.source_id == PriceSource.id).filter(
        LatestPrice.entity_type == "card",
        LatestPrice.entity_id == card_id,
    ).all()
    history = db.query(PriceHistory).filter(PriceHistory.entity_type == "card", PriceHistory.entity_id == card_id).order_by(PriceHistory.ts.desc()).limit(200).all()
    return {
        "card": CardOut.model_validate(card),
        "images": [{"kind": img.kind, "local_path": img.local_path} for img in images],
        "latest_prices": [
            {
                "market": price.market,
                "updated_at": price.updated_at,
                "source": source.name,
                "source_type": source.type,
            }
            for price, source in latest
        ],
        "price_history": [{"ts": h.ts, "market": h.market} for h in history],
    }


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


def ensure_price_source(db: Session, source_type: str, name: str, config: dict):
    source = db.query(PriceSource).filter(PriceSource.type == source_type).first()
    if source:
        return source
    source = PriceSource(name=name, type=source_type, config_json=config)
    db.add(source)
    db.commit()
    return source


@router.post("/cards/prices")
def card_prices(payload: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    card_ids = payload.get("card_ids") or []
    fetch_remote = bool(payload.get("fetch_remote", True))
    if not isinstance(card_ids, list) or not card_ids:
        return {"prices": []}

    latest_rows = (
        db.query(LatestPrice, PriceSource)
        .join(PriceSource, LatestPrice.source_id == PriceSource.id)
        .filter(LatestPrice.entity_type == "card", LatestPrice.entity_id.in_(card_ids))
        .all()
    )
    latest_map = {}
    for price, source in latest_rows:
        latest_map[price.entity_id] = {
            "card_id": price.entity_id,
            "market": price.market,
            "source": source.name,
            "source_type": source.type,
        }

    missing_ids = [card_id for card_id in card_ids if card_id not in latest_map]
    if not missing_ids or not fetch_remote:
        return {"prices": list(latest_map.values())}

    retries = int(os.environ.get("PRICE_RETRIES", "2"))
    backoff = float(os.environ.get("PRICE_BACKOFF", "1.2"))
    tcgdex_base = os.environ.get("PRICE_BASE_URL", "https://api.tcgdex.net/v2/en")
    tcgcsv_base = os.environ.get("TCGCSV_BASE_URL", "https://tcgcsv.com")

    tcgdex_source = ensure_price_source(db, "tcgdex_tcgplayer", "TCGplayer via TCGdex", {"base_url": tcgdex_base})
    tcgcsv_source = ensure_price_source(db, "tcgcsv_tcgplayer", "TCGplayer via TCGCSV", {"base_url": tcgcsv_base})

    cards = (
        db.query(Card, Set)
        .join(Set, Card.set_id == Set.id)
        .filter(Card.id.in_(missing_ids))
        .all()
    )

    for card, set_row in cards:
        # Try TCGdex
        tcgdex_url = f"{tcgdex_base}/cards/{set_row.code}-{card.number}"
        payload_data, _ = fetch_json(tcgdex_url, retries, backoff)
        if payload_data:
            pricing = payload_data.get("pricing") or {}
            tcgplayer = pricing.get("tcgplayer") or {}
            variant = pick_variant(tcgplayer)
            if variant:
                updated_at = datetime.utcnow()
                latest = LatestPrice(
                    entity_type="card",
                    entity_id=card.id,
                    source_id=tcgdex_source.id,
                    currency=str(tcgplayer.get("unit") or "USD"),
                    market=variant.get("marketPrice"),
                    low=variant.get("lowPrice"),
                    mid=variant.get("midPrice"),
                    high=variant.get("highPrice"),
                    updated_at=updated_at,
                )
                db.add(latest)
                db.add(PriceHistory(
                    entity_type="card",
                    entity_id=card.id,
                    source_id=tcgdex_source.id,
                    ts=updated_at,
                    market=latest.market,
                    low=latest.low,
                    mid=latest.mid,
                    high=latest.high,
                ))
                latest_map[card.id] = {
                    "card_id": card.id,
                    "market": latest.market,
                    "source": tcgdex_source.name,
                    "source_type": tcgdex_source.type,
                }
                continue

        # Fallback to TCGCSV (group match by set name)
        groups_payload, _ = fetch_json(f"{tcgcsv_base}/tcgplayer/3/groups", retries, backoff)
        groups = (groups_payload or {}).get("results") or []
        group_id = None
        set_name = (set_row.name or "").lower()
        for group in groups:
            name = str(group.get("name") or "").lower()
            if name == set_name:
                group_id = group.get("groupId")
                break
        if not group_id:
            continue
        products_payload, _ = fetch_json(f"{tcgcsv_base}/tcgplayer/3/{group_id}/products", retries, backoff)
        prices_payload, _ = fetch_json(f"{tcgcsv_base}/tcgplayer/3/{group_id}/prices", retries, backoff)
        products = (products_payload or {}).get("results") or []
        prices = (prices_payload or {}).get("results") or []
        product_map = {p.get("productId"): p for p in products if isinstance(p, dict)}
        number_key = str(card.number).split("/")[0].strip().lower()
        matching_ids = []
        for product in product_map.values():
            name = str(product.get("name") or "").lower()
            if name.endswith(f"#{number_key}"):
                matching_ids.append(product.get("productId"))
        if not matching_ids:
            continue
        product_id = matching_ids[0]
        price_entries = [p for p in prices if p.get("productId") == product_id]
        if not price_entries:
            continue
        entry = price_entries[0]
        updated_at = datetime.utcnow()
        latest = LatestPrice(
            entity_type="card",
            entity_id=card.id,
            source_id=tcgcsv_source.id,
            currency="USD",
            market=entry.get("marketPrice"),
            low=entry.get("lowPrice"),
            mid=entry.get("midPrice"),
            high=entry.get("highPrice"),
            updated_at=updated_at,
        )
        db.add(latest)
        db.add(PriceHistory(
            entity_type="card",
            entity_id=card.id,
            source_id=tcgcsv_source.id,
            ts=updated_at,
            market=latest.market,
            low=latest.low,
            mid=latest.mid,
            high=latest.high,
        ))
        latest_map[card.id] = {
            "card_id": card.id,
            "market": latest.market,
            "source": tcgcsv_source.name,
            "source_type": tcgcsv_source.type,
        }

    db.commit()
    return {"prices": list(latest_map.values())}
