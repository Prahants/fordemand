"""
database.py - SQLAlchemy Database 

Sets up the SQLite database engine, session factory, and base class
for ORM models. Uses dependency injection pattern for FastAPI.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite database file path (relative to project root)
SQLALCHEMY_DATABASE_URL = "sqlite:///./inventory.db"

# Create the SQLAlchemy engine
# check_same_thread=False is needed for SQLite with FastAPI (multi-threaded)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# SessionLocal class: each instance is a database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models to inherit from
Base = declarative_base()


def get_db():
    """
    Dependency injection function for FastAPI.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
