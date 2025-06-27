#!/usr/bin/env python3
"""Check database status and tables."""

from src.aptwise.config.db_config import engine
from sqlalchemy import text

def check_database():
    """Check database connection and tables."""
    try:
        with engine.connect() as conn:
            print("✅ Database connection successful")
            
            # Check tables
            result = conn.execute(text(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            ))
            tables = [row[0] for row in result.fetchall()]
            print(f"📋 Tables in database: {tables}")
            
            # Check if users table exists
            if 'users' in tables:
                print("✅ Users table exists")
                
                # Check users table structure
                result = conn.execute(text(
                    "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users'"
                ))
                columns = [(row[0], row[1]) for row in result.fetchall()]
                print(f"📝 Users table columns: {columns}")
                
                # Count users
                result = conn.execute(text("SELECT COUNT(*) FROM users"))
                count = result.fetchone()[0]
                print(f"👥 Number of users: {count}")
            else:
                print("❌ Users table does not exist")
                
            # Check alembic version
            if 'alembic_version' in tables:
                result = conn.execute(text("SELECT version_num FROM alembic_version"))
                version = result.fetchone()
                if version:
                    print(f"🔄 Alembic version: {version[0]}")
                else:
                    print("⚠️ No alembic version found")
            else:
                print("❌ Alembic version table does not exist")
                
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    check_database()
