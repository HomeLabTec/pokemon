import glob
import json
import os
from datetime import date, datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import Card, ExternalId, Set


def load_dataset(path: str):
    if os.path.isdir(path):
        payloads: List[Dict[str, Any]] = []
        set_codes: Dict[str, Dict[str, Any]] = {}
        files = sorted(glob.glob(os.path.join(path, "*.json")))
        if not files:
            raise SystemExit(f"No .json files found in directory: {path}")
        for file_path in files:
            with open(file_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            set_code = os.path.splitext(os.path.basename(file_path))[0]
            if isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
                for item in data["data"]:
                    if isinstance(item, dict) and "set" not in item and "set_id" not in item and "set_code" not in item:
                        item["set_code"] = set_code
                    payloads.append(item)
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "set" not in item and "set_id" not in item and "set_code" not in item:
                        item["set_code"] = set_code
                    payloads.append(item)
            else:
                raise SystemExit(f"Unsupported JSON structure in {file_path}")
            if set_code not in set_codes:
                set_codes[set_code] = {"code": set_code, "name": set_code}
        return {"sets": list(set_codes.values()), "cards": payloads}
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_date(value: Any) -> Optional[date]:
    if not value:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
    return None


def normalize_internal(data: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    return data.get("sets", []), data.get("cards", [])


def normalize_ptcg_cards(items: Iterable[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    sets_by_code: Dict[str, Dict[str, Any]] = {}
    cards: List[Dict[str, Any]] = []
    for card in items:
        set_info = card.get("set") or {}
        set_code = set_info.get("id") or card.get("set_id") or card.get("set")
        if set_code and set_code not in sets_by_code:
            set_images = set_info.get("images") or {}
            sets_by_code[set_code] = {
                "code": set_code,
                "name": set_info.get("name") or set_code,
                "series": set_info.get("series"),
                "release_date": set_info.get("releaseDate"),
                "total_cards": set_info.get("printedTotal") or set_info.get("total"),
                "symbol": set_images.get("symbol"),
            }
        rules = card.get("rules")
        if isinstance(rules, list):
            text = "\n".join(rules)
        else:
            text = rules or card.get("flavorText")
        cards.append({
            "id": card.get("id"),
            "set_code": set_code,
            "number": card.get("number"),
            "name": card.get("name"),
            "rarity": card.get("rarity"),
            "supertype": card.get("supertype"),
            "subtypes": card.get("subtypes"),
            "types": card.get("types"),
            "hp": card.get("hp"),
            "artist": card.get("artist"),
            "text": text,
        })
    return list(sets_by_code.values()), cards


def detect_and_normalize(data: Any) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], str]:
    if isinstance(data, dict):
        if "sets" in data and "cards" in data:
            sets, cards = normalize_internal(data)
            return sets, cards, "internal"
        if "data" in data and isinstance(data["data"], list):
            items = data["data"]
            if items and isinstance(items[0], dict) and "set" in items[0]:
                sets, cards = normalize_ptcg_cards(items)
                return sets, cards, "ptcg_cards"
            if items and isinstance(items[0], dict) and "printedTotal" in items[0]:
                return items, [], "ptcg_sets"
    if isinstance(data, list):
        if data and isinstance(data[0], dict) and "set" in data[0]:
            sets, cards = normalize_ptcg_cards(data)
            return sets, cards, "ptcg_cards"
        if data and isinstance(data[0], dict) and "printedTotal" in data[0]:
            return data, [], "ptcg_sets"
    return [], [], "unknown"


def main():
    dataset_path = os.environ.get("CATALOG_PATH", "/data/catalog.json")
    if not os.path.exists(dataset_path):
        raise SystemExit(f"Catalog file not found: {dataset_path}")
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    data = load_dataset(dataset_path)
    sets, cards, format_name = detect_and_normalize(data)
    if not sets and not cards:
        raise SystemExit("Catalog format not recognized. Expected an object with 'sets' and 'cards' or a PTCG cards dataset.")
    if not cards:
        raise SystemExit("Catalog contains sets only. This app requires card data too; download the full cards dataset or provide a catalog with both sets and cards.")

    for set_row in sets:
        set_code = set_row.get("code") or set_row.get("id")
        if not set_code:
            continue
        existing = db.query(Set).filter(Set.code == set_code).first()
        if not existing:
            db.add(Set(
                code=set_code,
                name=set_row.get("name") or set_code,
                series=set_row.get("series"),
                release_date=parse_date(set_row.get("release_date") or set_row.get("releaseDate")),
                total_cards=set_row.get("total_cards") or set_row.get("total") or set_row.get("printedTotal"),
                symbol_url=set_row.get("symbol") or (set_row.get("images") or {}).get("symbol"),
            ))
    db.commit()

    set_codes = {((row.get("code") or row.get("id")) or "") for row in sets}
    set_codes.discard("")
    set_rows = db.query(Set).filter(Set.code.in_(set_codes)).all()
    set_code_to_id = {row.code: row.id for row in set_rows}

    for card in cards:
        card_id = card.get("id")
        external_id = None
        if isinstance(card_id, str):
            if card_id.isdigit():
                card_id = int(card_id)
            else:
                external_id = card_id
                card_id = None
        set_id = card.get("set_id")
        if set_id is None:
            set_id = set_code_to_id.get(card.get("set_code"))
        if not set_id:
            continue
        if card_id is not None:
            existing = db.query(Card).filter(Card.id == card_id).first()
        elif external_id:
            existing = db.query(ExternalId).filter(
                ExternalId.entity_type == "card",
                ExternalId.source == "ptcg",
                ExternalId.external_id == external_id,
            ).first()
            if existing:
                continue
            existing = None
        else:
            existing = None
        if existing:
            continue
        card_row = Card(
            id=card_id,
            set_id=set_id,
            number=card.get("number"),
            name=card.get("name"),
            rarity=card.get("rarity"),
            supertype=card.get("supertype"),
            subtypes=card.get("subtypes"),
            types=card.get("types"),
            hp=card.get("hp"),
            artist=card.get("artist"),
            text=card.get("text"),
            created_at=datetime.utcnow(),
        )
        db.add(card_row)
        if external_id:
            db.flush()
            db.add(ExternalId(
                entity_type="card",
                entity_id=card_row.id,
                source="ptcg",
                external_id=external_id,
            ))
    db.commit()
    print(f"Imported {len(sets)} sets and {len(cards)} cards (format={format_name})")


if __name__ == "__main__":
    main()
