from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user

router = APIRouter()


@router.post("/csv")
def import_csv(file: UploadFile = File(...), db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return {"status": "received", "filename": file.filename}


@router.post("/paste")
def import_paste(payload: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return {"status": "received", "lines": len(payload.get("lines", []))}
