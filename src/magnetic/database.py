"""Database initialization and session management."""

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import logging

from magnetic.config.settings import Config
from magnetic.models.base import Base
from magnetic.models.trip import Trip, ItineraryDay, Activity, Accommodation, Budget

logger = logging.getLogger(__name__)

# Create the SQLAlchemy engine
logger.info("Creating database engine...")
engine = create_engine(Config.get_instance().DATABASE_URL, echo=True)
logger.info(f"Created database engine with URL: {Config.get_instance().DATABASE_URL}")

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
logger.info("Created SessionLocal factory")

def get_db() -> Generator[Session, None, None]:
    """Get a database session."""
    logger.info("Entering get_db()")
    db = SessionLocal()
    logger.info(f"Created new database session: {db}")
    try:
        logger.info("Yielding database session")
        yield db
        logger.info("After yield in get_db()")
        db.commit()
        logger.info("Committed database session")
    except Exception as e:
        logger.error(f"Exception in get_db(): {str(e)}")
        db.rollback()
        raise
    finally:
        logger.info("Closing database session")
        db.close()

def init_db() -> None:
    """Initialize the database by creating all tables."""
    logger.info("Starting database initialization")
    
    # Import all models to ensure they're registered with SQLAlchemy
    logger.info("Registered models:")
    for model in [Trip, ItineraryDay, Activity, Accommodation, Budget]:
        logger.info(f"- {model.__name__}")
    
    logger.info("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    
    # Verify tables were created
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    logger.info(f"Tables in database: {tables}")
    
    logger.info("Database initialization complete") 