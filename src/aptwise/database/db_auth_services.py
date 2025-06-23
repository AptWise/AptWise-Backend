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
        "github_url": user.github_url,
        "linkedin_id": getattr(user, 'linkedin_id', None),
        "linkedin_access_token": getattr(user, 'linkedin_access_token', None),
        "github_id": getattr(user, 'github_id', None),
        "github_access_token": getattr(user, 'github_access_token', None),
        "profile_picture_url": getattr(user, 'profile_picture_url', None),
        "is_linkedin_connected": getattr(user, 'is_linkedin_connected', False),
        "is_github_connected": getattr(user, 'is_github_connected', False)
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


def get_user_by_linkedin_id(linkedin_id: str) -> Optional[Dict[str, Any]]:
    """Get user by LinkedIn ID from the database."""
    session = get_session()
    if not session:
        raise RuntimeError("Database connection not available")

    query = text("SELECT * FROM users WHERE linkedin_id = :linkedin_id")
    result = session.execute(query, {"linkedin_id": linkedin_id})
    user = result.fetchone()
    session.close()

    if not user:
        return None

    return {
        "name": user.name,
        "email": user.email,
        "password": user.password,
        "linkedin_url": user.linkedin_url,
        "github_url": user.github_url,
        "linkedin_id": user.linkedin_id,
        "linkedin_access_token": user.linkedin_access_token,
        "profile_picture_url": user.profile_picture_url,
        "is_linkedin_connected": user.is_linkedin_connected
    }


def create_user_with_linkedin(user_data: Dict[str, Any]) -> bool:
    """Create a new user with LinkedIn OAuth data."""
    session = get_session()
    if not session:
        raise RuntimeError("Database connection not available")

    query = text("""
    INSERT INTO users (email, name, password, linkedin_url, github_url, 
                      linkedin_id, linkedin_access_token, profile_picture_url, is_linkedin_connected)
    VALUES (:email, :name, :password, :linkedin_url, :github_url, 
            :linkedin_id, :linkedin_access_token, :profile_picture_url, :is_linkedin_connected)
    """)

    try:
        session.execute(
            query,
            {
                "email": user_data["email"],
                "name": user_data["name"],
                "password": user_data.get("password", ""),  # Empty password for LinkedIn users
                "linkedin_url": user_data.get("linkedin_url", None),
                "github_url": user_data.get("github_url", None),
                "linkedin_id": user_data["linkedin_id"],
                "linkedin_access_token": user_data["linkedin_access_token"],
                "profile_picture_url": user_data.get("profile_picture_url", None),
                "is_linkedin_connected": True
            }
        )
        session.commit()
        session.close()
        return True
    except Exception as e:
        session.rollback()
        session.close()
        print(f"Error creating LinkedIn user: {e}")
        return False


def update_user_linkedin_connection(email: str, linkedin_data: Dict[str, Any]) -> bool:
    """Update existing user with LinkedIn OAuth data."""
    session = get_session()
    if not session:
        raise RuntimeError("Database connection not available")

    query = text("""
    UPDATE users 
    SET linkedin_id = :linkedin_id, 
        linkedin_access_token = :linkedin_access_token,
        profile_picture_url = :profile_picture_url,
        is_linkedin_connected = :is_linkedin_connected
    WHERE email = :email
    """)

    try:
        result = session.execute(
            query,
            {
                "email": email,
                "linkedin_id": linkedin_data["linkedin_id"],
                "linkedin_access_token": linkedin_data["linkedin_access_token"],
                "profile_picture_url": linkedin_data.get("profile_picture_url", None),
                "is_linkedin_connected": True
            }
        )
        session.commit()
        session.close()
        return result.rowcount > 0
    except Exception as e:
        session.rollback()
        session.close()
        print(f"Error updating user LinkedIn connection: {e}")
        return False


def disconnect_user_linkedin(email: str) -> bool:
    """Disconnect LinkedIn from user account."""
    session = get_session()
    if not session:
        raise RuntimeError("Database connection not available")

    query = text("""
    UPDATE users 
    SET linkedin_id = NULL, 
        linkedin_access_token = NULL,
        is_linkedin_connected = FALSE
    WHERE email = :email
    """)

    try:
        result = session.execute(query, {"email": email})
        session.commit()
        session.close()
        return result.rowcount > 0
    except Exception as e:
        session.rollback()
        session.close()
        print(f"Error disconnecting LinkedIn: {e}")
        return False


def get_user_by_github_id(github_id: str) -> Optional[Dict[str, Any]]:
    """Get user by GitHub ID from the database."""
    session = get_session()
    if not session:
        raise RuntimeError("Database connection not available")

    query = text("SELECT * FROM users WHERE github_id = :github_id")
    result = session.execute(query, {"github_id": github_id})
    user = result.fetchone()
    session.close()

    if not user:
        return None

    return {
        "name": user.name,
        "email": user.email,
        "password": user.password,
        "linkedin_url": user.linkedin_url,
        "github_url": user.github_url,
        "linkedin_id": getattr(user, 'linkedin_id', None),
        "linkedin_access_token": getattr(user, 'linkedin_access_token', None),
        "github_id": user.github_id,
        "github_access_token": user.github_access_token,
        "profile_picture_url": getattr(user, 'profile_picture_url', None),
        "is_linkedin_connected": getattr(user, 'is_linkedin_connected', False),
        "is_github_connected": user.is_github_connected
    }


def create_user_with_github(user_data: Dict[str, Any]) -> bool:
    """Create a new user with GitHub OAuth data."""
    session = get_session()
    if not session:
        raise RuntimeError("Database connection not available")

    query = text("""
    INSERT INTO users (email, name, password, linkedin_url, github_url, 
                      github_id, github_access_token, profile_picture_url, is_github_connected)
    VALUES (:email, :name, :password, :linkedin_url, :github_url, 
            :github_id, :github_access_token, :profile_picture_url, :is_github_connected)
    """)

    try:
        session.execute(
            query,
            {
                "email": user_data["email"],
                "name": user_data["name"],
                "password": user_data.get("password", ""),  # Empty password for GitHub users
                "linkedin_url": user_data.get("linkedin_url", None),
                "github_url": user_data.get("github_url", None),
                "github_id": user_data["github_id"],
                "github_access_token": user_data["github_access_token"],
                "profile_picture_url": user_data.get("profile_picture_url", None),
                "is_github_connected": True
            }
        )
        session.commit()
        session.close()
        return True
    except Exception as e:
        session.rollback()
        session.close()
        print(f"Error creating GitHub user: {e}")
        return False


def update_user_github_connection(email: str, github_data: Dict[str, Any]) -> bool:
    """Update existing user with GitHub OAuth data."""
    session = get_session()
    if not session:
        raise RuntimeError("Database connection not available")

    query = text("""
    UPDATE users 
    SET github_id = :github_id, 
        github_access_token = :github_access_token,
        github_url = :github_url,
        profile_picture_url = COALESCE(:profile_picture_url, profile_picture_url),
        is_github_connected = :is_github_connected
    WHERE email = :email
    """)

    try:
        result = session.execute(
            query,
            {
                "email": email,
                "github_id": github_data["github_id"],
                "github_access_token": github_data["github_access_token"],
                "github_url": github_data.get("github_url", None),
                "profile_picture_url": github_data.get("profile_picture_url", None),
                "is_github_connected": True
            }
        )
        session.commit()
        session.close()
        return result.rowcount > 0
    except Exception as e:
        session.rollback()
        session.close()
        print(f"Error updating user GitHub connection: {e}")
        return False


def disconnect_user_github(email: str) -> bool:
    """Disconnect GitHub from user account."""
    session = get_session()
    if not session:
        raise RuntimeError("Database connection not available")

    query = text("""
    UPDATE users 
    SET github_id = NULL, 
        github_access_token = NULL,
        is_github_connected = FALSE
    WHERE email = :email
    """)

    try:
        result = session.execute(query, {"email": email})
        session.commit()
        session.close()
        return result.rowcount > 0
    except Exception as e:
        session.rollback()
        session.close()
        print(f"Error disconnecting GitHub: {e}")
        return False
