from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_admin
from app.models import JobRun
from app.schemas import AdminJobRequest

router = APIRouter()


@router.post("/catalog/import")
def catalog_import(payload: AdminJobRequest, db: Session = Depends(get_db), admin=Depends(require_admin)):
    run = JobRun(job_name="catalog_import", status="queued")
    db.add(run)
    db.commit()
    return {"status": "queued", "job_id": run.id}


@router.post("/images/prefetch")
def images_prefetch(payload: AdminJobRequest, db: Session = Depends(get_db), admin=Depends(require_admin)):
    run = JobRun(job_name="images_prefetch", status="queued", stats_json=payload.model_dump())
    db.add(run)
    db.commit()
    return {"status": "queued", "job_id": run.id}


@router.post("/pricing/run-now")
def pricing_run(db: Session = Depends(get_db), admin=Depends(require_admin)):
    run = JobRun(job_name="pricing_run", status="queued")
    db.add(run)
    db.commit()
    return {"status": "queued", "job_id": run.id}


@router.get("/jobs")
def jobs(db: Session = Depends(get_db), admin=Depends(require_admin)):
    runs = db.query(JobRun).order_by(JobRun.started_at.desc()).limit(200).all()
    return [
        {"id": r.id, "job_name": r.job_name, "status": r.status, "started_at": r.started_at, "finished_at": r.finished_at}
        for r in runs
    ]
