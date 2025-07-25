"""
Database configuration for PostgreSQL DB.
"""
import os
import traceback
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# PostgreSQL connection settings
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "aptwisedb")
DB_USER = os.getenv("DB_USER", "aptwise")
DB_PASSWORD = os.getenv("DB_PASSWORD", "aptwise")

# SQLAlchemy setup
url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
DATABASE_URL = url

try:
    print(f"Attempting to connect to PostgreSQL at {DB_HOST}:{DB_PORT}...")
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
    print(f"Connection details:\
           Host={DB_HOST}, Port={DB_PORT}, DB={DB_NAME}, User={DB_USER}")
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
