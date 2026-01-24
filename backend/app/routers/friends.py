from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.models import Friendship, SharedCollection, User
from app.schemas import FriendshipAccept, FriendshipInvite

router = APIRouter()


@router.post("/invite")
def invite(payload: FriendshipInvite, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    friend = db.query(User).filter(User.email == payload.friend_email).first()
    if not friend:
        raise HTTPException(status_code=404, detail="Friend not found")
    existing = db.query(Friendship).filter(
        Friendship.user_id == current_user.id,
        Friendship.friend_user_id == friend.id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Invite already sent")
    invite = Friendship(user_id=current_user.id, friend_user_id=friend.id, status="pending")
    db.add(invite)
    db.commit()
    return {"status": "invited"}


@router.post("/accept")
def accept(payload: FriendshipAccept, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    invite = db.query(Friendship).filter(
        Friendship.user_id == payload.friend_user_id,
        Friendship.friend_user_id == current_user.id,
        Friendship.status == "pending",
    ).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    invite.status = "accepted"
    shared = SharedCollection(owner_user_id=current_user.id, viewer_user_id=payload.friend_user_id, permission="view")
    db.add(shared)
    db.commit()
    return {"status": "accepted"}


@router.get("/collections/{user_id}")
def view_collection(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if user_id == current_user.id:
        return {"user_id": user_id, "permission": "owner"}
    shared = db.query(SharedCollection).filter(
        SharedCollection.owner_user_id == user_id,
        SharedCollection.viewer_user_id == current_user.id,
    ).first()
    if not shared:
        raise HTTPException(status_code=403, detail="No access")
    return {"user_id": user_id, "permission": shared.permission}
