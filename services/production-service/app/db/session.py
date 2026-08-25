from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def _engine_options(database_url: str) -> dict:
    return {"connect_args": {"check_same_thread": False}} if database_url.startswith("sqlite") else {}


engine = create_engine(get_settings().database_url, pool_pre_ping=True, **_engine_options(get_settings().database_url))
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
