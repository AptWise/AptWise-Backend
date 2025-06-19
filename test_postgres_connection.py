"""
Simple script to test PostgreSQL connection.
"""
import traceback
import psycopg2
from sqlalchemy import create_engine, text

def test_connection():
    try:        # PostgreSQL connection details
        host = "127.0.0.1"
        port = "5432"
        database = "aptwisedb"
        user = "aptwise"
        password = "aptwise"
        
        # Try to connect to PostgreSQL using psycopg2
        print(f"Attempting to connect to PostgreSQL at {host}:{port}...")
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        
        # If we get here, connection was successful
        print("Successfully connected to PostgreSQL using psycopg2!")
        
        # Get PostgreSQL version using psycopg2
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        print(f"PostgreSQL version: {db_version[0]}")
        cursor.close()
        conn.close()
        
        # Also test with SQLAlchemy
        print("Testing connection with SQLAlchemy...")
        engine = create_engine(f"postgresql://{user}:{password}@{host}:{port}/{database}")
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"SQLAlchemy connection successful - PostgreSQL version: {version}")
        
        return True
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_connection()
    if success:
        print("PostgreSQL connection test passed!")
    else:
        print("PostgreSQL connection test failed!")
