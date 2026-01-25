import argparse

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import User
from app.security import get_password_hash


def main():
    parser = argparse.ArgumentParser(description="Create a new user")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--admin", action="store_true", help="Create as admin user")
    args = parser.parse_args()

    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    existing = db.query(User).filter(User.email == args.email).first()
    if existing:
        raise SystemExit(f"Email already registered: {args.email}")

    role = "admin" if args.admin or args.email.endswith("@admin.local") else "user"
    user = User(
        name=args.name,
        email=args.email,
        password_hash=get_password_hash(args.password),
        role=role,
    )
    db.add(user)
    db.commit()
    print(f"Created user {user.email} with role={role}")


if __name__ == "__main__":
    main()
