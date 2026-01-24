from sqlalchemy import create_engine

from app.config import settings
from app.db import Base
from app import models


def main():
    engine = create_engine(settings.database_url)
    Base.metadata.create_all(bind=engine)
    print("Database tables created")


if __name__ == "__main__":
    main()
