from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.models import GradedItem, TagDetail, User
from app.schemas import GradedCreate, GradedOut

router = APIRouter()


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
