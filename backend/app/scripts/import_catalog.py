import json
import os
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import Card, Set


def load_dataset(path: str):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def main():
    dataset_path = os.environ.get("CATALOG_PATH", "/data/catalog.json")
    if not os.path.exists(dataset_path):
        raise SystemExit(f"Catalog file not found: {dataset_path}")
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    data = load_dataset(dataset_path)
    sets = data.get("sets", [])
    cards = data.get("cards", [])

    for set_row in sets:
        existing = db.query(Set).filter(Set.code == set_row["code"]).first()
        if not existing:
            db.add(Set(
                code=set_row["code"],
                name=set_row["name"],
                series=set_row.get("series"),
                release_date=set_row.get("release_date"),
                total_cards=set_row.get("total_cards"),
                symbol_url=set_row.get("symbol"),
            ))
    db.commit()

    for card in cards:
        existing = db.query(Card).filter(Card.id == card["id"]).first()
        if existing:
            continue
        db.add(Card(
            id=card["id"],
            set_id=card["set_id"],
            number=card["number"],
            name=card["name"],
            rarity=card.get("rarity"),
            supertype=card.get("supertype"),
            subtypes=card.get("subtypes"),
            types=card.get("types"),
            hp=card.get("hp"),
            artist=card.get("artist"),
            text=card.get("text"),
            created_at=datetime.utcnow(),
        ))
    db.commit()
    print(f"Imported {len(sets)} sets and {len(cards)} cards")


if __name__ == "__main__":
    main()
