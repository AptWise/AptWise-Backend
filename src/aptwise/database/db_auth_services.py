"""
Database services for authentication.
"""
from typing import Optional, Dict, List, Any
from sqlalchemy import text
from ..config.db_config import get_session


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email from the database."""
    session = get_session()
    if not session:
        raise RuntimeError("Database connection not available")

    query = text("SELECT * FROM users WHERE email = :email")
    result = session.execute(query, {"email": email})
    user = result.fetchone()
    session.close()

    if not user:
        return None

    return {
        "name": user.name,
        "email": user.email,
        "password": user.password,
        "linkedin_url": user.linkedin_url,
        "github_url": user.github_url
    }


def create_user(user_data: Dict[str, Any]) -> bool:
    """Create a new user in the database."""
    session = get_session()
    if not session:
        raise RuntimeError("Database connection not available")

    query = text("""
    INSERT INTO users (email, name, password, linkedin_url, github_url)
    VALUES (:email, :name, :password, :linkedin_url, :github_url)
    """)

    try:
        session.execute(
            query,
            {
                "email": user_data["email"],
                "name": user_data["name"],
                "password": user_data["password"],
                "linkedin_url": user_data.get("linkedin_url", None),
                "github_url": user_data.get("github_url", None)
            }
        )
        session.commit()
        session.close()
        return True
    except Exception as e:
        session.rollback()
        session.close()
        print(f"Error creating user: {e}")
        return False


def delete_user(email: str) -> bool:
    """Delete a user from the database."""
    session = get_session()
    if not session:
        raise RuntimeError("Database connection not available")

    query = text("DELETE FROM users WHERE email = :email")

    try:
        session.execute(query, {"email": email})
        session.commit()
        session.close()
        return True
    except Exception as e:
        session.rollback()
        session.close()
        print(f"Error deleting user: {e}")
        return False


def get_all_users() -> List[Dict[str, Any]]:
    """Get all users from the database."""
    session = get_session()
    if not session:
        raise RuntimeError("Database connection not available")

    query = text("SELECT * FROM users")
    results = session.execute(query)
    rows = results.fetchall()
    session.close()

    users = []
    for user in rows:
        users.append({
            "name": user.name,
            "email": user.email,
            "password": user.password,
            "linkedin_url": user.linkedin_url,
            "github_url": user.github_url
        })

    return users
