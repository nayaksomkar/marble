"""
SQLite engine, session factory, and Base.
Uses StaticPool to allow sharing across threads (needed by FastAPI).
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool
from config import settings
from logging_config import logger

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a session, commits on success, rolls back on error."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"DB error: {e}")
        raise
    finally:
        db.close()


def get_db_session():
    """Open a plain session for use outside of FastAPI dependency injection."""
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database ready")