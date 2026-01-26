from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.models import Card, Holding, Set, User
from app.schemas import HoldingCreate, HoldingOut, HoldingUpdate

router = APIRouter()


@router.post("", response_model=HoldingOut)
def create_holding(payload: HoldingCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    holding = Holding(user_id=current_user.id, **payload.model_dump())
    db.add(holding)
    db.commit()
    db.refresh(holding)
    return holding


@router.patch("/{holding_id}", response_model=HoldingOut)
def update_holding(holding_id: int, payload: HoldingUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    holding = db.query(Holding).filter(Holding.id == holding_id, Holding.user_id == current_user.id).first()
    if not holding:
        raise HTTPException(status_code=404, detail="Holding not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(holding, key, value)
    holding.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(holding)
    return holding


@router.delete("/{holding_id}")
def delete_holding(holding_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    holding = db.query(Holding).filter(Holding.id == holding_id, Holding.user_id == current_user.id).first()
    if not holding:
        raise HTTPException(status_code=404, detail="Holding not found")
    db.delete(holding)
    db.commit()
    return {"status": "deleted"}


@router.get("/my")
def list_holdings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = (
        db.query(Holding, Card, Set)
        .join(Card, Holding.card_id == Card.id)
        .join(Set, Card.set_id == Set.id)
        .filter(Holding.user_id == current_user.id)
        .order_by(Holding.updated_at.desc(), Holding.created_at.desc())
        .all()
    )
    return [
        {
            "holding_id": holding.id,
            "quantity": holding.quantity,
            "condition": holding.condition,
            "is_for_trade": holding.is_for_trade,
            "is_wantlist": holding.is_wantlist,
            "is_watched": holding.is_watched,
            "notes": holding.notes,
            "card": {
                "id": card.id,
                "name": card.name,
                "number": card.number,
                "rarity": card.rarity,
            },
            "set": {
                "id": set_row.id,
                "code": set_row.code,
                "name": set_row.name,
            },
        }
        for holding, card, set_row in rows
    ]
