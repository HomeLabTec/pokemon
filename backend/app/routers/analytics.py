from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.models import PortfolioBreakdown, PortfolioSnapshot, User

router = APIRouter()


@router.get("/portfolio")
def portfolio(range: str = "30d", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    snapshots = (
        db.query(PortfolioSnapshot)
        .filter(PortfolioSnapshot.user_id == current_user.id)
        .order_by(PortfolioSnapshot.ts.desc())
        .limit(500)
        .all()
    )
    return {"range": range, "data": [
        {"ts": s.ts, "total": s.total_value, "raw": s.raw_value, "graded": s.graded_value}
        for s in snapshots
    ]}


@router.get("/breakdown")
def breakdown(type: str, range: str = "30d", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = (
        db.query(PortfolioBreakdown)
        .filter(PortfolioBreakdown.user_id == current_user.id, PortfolioBreakdown.breakdown_type == type)
        .order_by(PortfolioBreakdown.ts.desc())
        .limit(500)
        .all()
    )
    return {"range": range, "data": [{"key": r.key, "value": r.value, "ts": r.ts} for r in rows]}


@router.get("/top-movers")
def top_movers(range: str = "7d"):
    return {"range": range, "data": []}
