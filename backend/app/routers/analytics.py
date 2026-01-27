from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.models import GradedItem, Holding, LatestPrice, PortfolioBreakdown, PortfolioSnapshot, User

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


@router.post("/portfolio/snapshot")
def snapshot_portfolio(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    holdings = db.query(Holding).filter(Holding.user_id == current_user.id).all()
    if not holdings:
        return {"status": "no_holdings"}

    card_ids = list({holding.card_id for holding in holdings})
    graded_items = db.query(GradedItem).filter(GradedItem.user_id == current_user.id).all()
    graded_by_card = {graded.card_id: graded for graded in graded_items}
    graded_ids = [graded.id for graded in graded_items]

    card_prices = db.query(LatestPrice).filter(
        LatestPrice.entity_type == "card",
        LatestPrice.entity_id.in_(card_ids),
    ).all()
    graded_prices = []
    if graded_ids:
        graded_prices = db.query(LatestPrice).filter(
            LatestPrice.entity_type == "graded",
            LatestPrice.entity_id.in_(graded_ids),
        ).all()

    def build_price_map(rows):
        price_map = {}
        for row in rows:
            if row.market is None:
                continue
            current = price_map.get(row.entity_id)
            if current is None or row.market > current:
                price_map[row.entity_id] = row.market
        return price_map

    card_price_map = build_price_map(card_prices)
    graded_price_map = build_price_map(graded_prices)

    raw_value = 0.0
    graded_value = 0.0
    for holding in holdings:
        qty = float(holding.quantity or 0)
        graded = graded_by_card.get(holding.card_id)
        if graded and graded_price_map.get(graded.id) is not None:
            graded_value += graded_price_map[graded.id] * qty
        else:
            price = card_price_map.get(holding.card_id)
            if price is not None:
                raw_value += price * qty

    total_value = raw_value + graded_value
    snapshot = PortfolioSnapshot(
        user_id=current_user.id,
        total_value=total_value,
        raw_value=raw_value,
        graded_value=graded_value,
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return {"status": "ok", "snapshot": {"ts": snapshot.ts, "total": snapshot.total_value}}


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
