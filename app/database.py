from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _migrate_users_table() -> None:
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("users")}
    alterations = [
        ("full_name", "ALTER TABLE users ADD COLUMN full_name VARCHAR"),
        ("google_id", "ALTER TABLE users ADD COLUMN google_id VARCHAR"),
        ("auth_provider", "ALTER TABLE users ADD COLUMN auth_provider VARCHAR DEFAULT 'email'"),
        ("is_verified", "ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT 0"),
        ("otp_hash", "ALTER TABLE users ADD COLUMN otp_hash VARCHAR"),
        ("otp_expires_at", "ALTER TABLE users ADD COLUMN otp_expires_at DATETIME"),
    ]

    with engine.begin() as conn:
        for name, sql in alterations:
            if name not in columns:
                conn.execute(text(sql))

        if "is_verified" not in columns or "auth_provider" not in columns:
            pass
        else:
            conn.execute(
                text(
                    """
                    UPDATE users
                    SET is_verified = 1
                    WHERE is_verified = 0
                      AND auth_provider = 'email'
                      AND google_id IS NULL
                      AND otp_hash IS NULL
                      AND hashed_password IS NOT NULL
                    """
                )
            )


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _migrate_users_table()
