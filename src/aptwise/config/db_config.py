"""
Database configuration for PostgreSQL DB.
"""
import os
import traceback
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Use DATABASE_URL if provided, otherwise fall back to individual components
DATABASE_URL = os.getenv("DATABASE_URL")

try:
    print(f"Using DATABASE_URL: {DATABASE_URL}")
    print("Attempting to connect to PostgreSQL...")
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    metadata = MetaData()

    # Test the connection
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("Successfully connected to PostgreSQL database")
    except Exception as detailed_error:
        traceback.print_exc()
        raise detailed_error
except Exception as e:
    print(f"Error connecting to PostgreSQL: {e}")
    print(f"DATABASE_URL: {DATABASE_URL}")
    print("ERROR: Cannot connect to PostgreSQL.\
           Application requires a database connection.")
    engine = None
    SessionLocal = None

# Note: Tables are now managed by Alembic migrations


def get_session():
    """Return a new SQLAlchemy session."""
    if SessionLocal:
        db = SessionLocal()
        try:
            return db
        except Exception:
            db.close()
    return None


# Tables are now managed by Alembic migrations
