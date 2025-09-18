from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for declarative models."""


engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_session():
    """Return a new database session."""

    return SessionLocal()


def init_db() -> None:
    """Create database tables."""

    import app.models.database  # noqa: F401  # Ensure models imported

    Base.metadata.create_all(bind=engine)
