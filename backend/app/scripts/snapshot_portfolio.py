from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import GradedItem, Holding, LatestPrice, PortfolioSnapshot, User


def build_price_map(rows):
    price_map = {}
    for row in rows:
        if row.market is None:
            continue
        current = price_map.get(row.entity_id)
        if current is None or row.market > current:
            price_map[row.entity_id] = row.market
    return price_map


def main():
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        users = db.query(User).all()
        now = datetime.utcnow()
        for user in users:
            holdings = db.query(Holding).filter(Holding.user_id == user.id).all()
            if not holdings:
                continue
            card_ids = list({holding.card_id for holding in holdings})
            graded_items = db.query(GradedItem).filter(GradedItem.user_id == user.id).all()
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
                user_id=user.id,
                ts=now,
                total_value=total_value,
                raw_value=raw_value,
                graded_value=graded_value,
            )
            db.add(snapshot)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
