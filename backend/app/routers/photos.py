import os
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, File, UploadFile
from PIL import Image
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.dependencies import get_current_user
from app.models import User, UserPhoto

router = APIRouter()


@router.post("/upload")
def upload_photo(
    card_id: int | None = None,
    graded_item_id: int | None = None,
    caption: str | None = None,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in {".jpg", ".jpeg", ".png"}:
        return {"error": "Unsupported file type"}
    uploads_dir = os.path.join(settings.media_root, "uploads", str(current_user.id))
    thumbs_dir = os.path.join(uploads_dir, "thumbs")
    os.makedirs(uploads_dir, exist_ok=True)
    os.makedirs(thumbs_dir, exist_ok=True)
    filename = f"{uuid4().hex}{ext}"
    file_path = os.path.join(uploads_dir, filename)
    with open(file_path, "wb") as out:
        out.write(file.file.read())
    thumb_path = os.path.join(thumbs_dir, filename)
    with Image.open(file_path) as img:
        img.thumbnail((320, 320))
        img.save(thumb_path)
    photo = UserPhoto(
        user_id=current_user.id,
        card_id=card_id,
        graded_item_id=graded_item_id,
        local_path=file_path,
        thumb_path=thumb_path,
        caption=caption,
        created_at=datetime.utcnow(),
    )
    db.add(photo)
    db.commit()
    return {"status": "uploaded", "photo_id": photo.id}
