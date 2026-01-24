import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import Card, CardImage


def main():
    mode = os.environ.get("PREFETCH_MODE", "owned")
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    db = Session()
    total = db.query(Card).count()
    print(f"Prefetch mode={mode} cards={total}")
    # Placeholder: actual download handled by worker integration.
    return


if __name__ == "__main__":
    main()
