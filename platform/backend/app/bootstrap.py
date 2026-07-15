"""Create the first production administrator without adding demonstration data."""
from sqlalchemy import func, select

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import Role, User


def bootstrap() -> None:
    with SessionLocal() as db:
        if db.scalar(select(func.count()).select_from(User)):
            return

        name = settings.initial_admin_name.strip()
        email = settings.initial_admin_email.strip().lower()
        password = settings.initial_admin_password
        if not name or not email or len(password) < 12:
            message = (
                "The database has no users. Set INITIAL_ADMIN_NAME, "
                "INITIAL_ADMIN_EMAIL, and INITIAL_ADMIN_PASSWORD (at least 12 characters)."
            )
            if settings.environment == "production":
                raise RuntimeError(message)
            print(f"WARNING: {message}")
            return

        db.add(User(name=name, email=email, password_hash=hash_password(password), role=Role.admin))
        db.commit()
        print(f"Created initial administrator: {email}")


if __name__ == "__main__":
    bootstrap()
