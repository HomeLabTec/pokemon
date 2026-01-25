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
