import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import LatestPrice


def main():
    mode = os.environ.get("SEED_MODE", "tracked")
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    db = Session()
    print(f"Seeding prices for mode={mode}")
    # Placeholder for pricing provider integration.
    return


if __name__ == "__main__":
    main()
