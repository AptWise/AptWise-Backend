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
    """Create a new user in the database with optional OAuth data."""
    session = get_session()
    if not session:
        raise RuntimeError("Database connection not available")

    query = text("""
    INSERT INTO users (
        email, name, password, linkedin_url, github_url,
        linkedin_id, linkedin_access_token, github_id, github_access_token,
        profile_picture_url, is_linkedin_connected, is_github_connected
    )
    VALUES (
        :email, :name, :password, :linkedin_url, :github_url,
        :linkedin_id, :linkedin_access_token, :github_id, :github_access_token,
        :profile_picture_url, :is_linkedin_connected, :is_github_connected
    )
    """)

    try:
        session.execute(
            query,
            {
                "email": user_data["email"],
                "name": user_data["name"],
                "password": user_data["password"],
                "linkedin_url": user_data.get("linkedin_url", None),
                "github_url": user_data.get("github_url", None),
                # OAuth fields
                "linkedin_id": user_data.get("linkedin_id", None),
                "linkedin_access_token":
                user_data.get("linkedin_access_token", None),
                "github_id": user_data.get("github_id", None),
                "github_access_token":
                user_data.get("github_access_token", None),
                "profile_picture_url":
                user_data.get("profile_picture_url", None),
                "is_linkedin_connected":
                user_data.get("is_linkedin_connected", False),
                "is_github_connected":
                user_data.get("is_github_connected", False)
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
    INSERT INTO users (email, name, password, linkedin_url,\
        github_url, linkedin_id, linkedin_access_token, \
        profile_picture_url, is_linkedin_connected)
    VALUES (:email, :name, :password, :linkedin_url, \
        :github_url, :linkedin_id, :linkedin_access_token,\
        :profile_picture_url, :is_linkedin_connected)
    """)

    try:
        session.execute(
            query,            {
                "email": user_data["email"],
                "name": user_data["name"],
                "password": user_data.get("password", ""),
                "linkedin_url": user_data.get("linkedin_url", None),
                "github_url": user_data.get("github_url", None),
                "linkedin_id": user_data["linkedin_id"],
                "linkedin_access_token": user_data["linkedin_access_token"],
                "profile_picture_url": user_data.get(
                    "profile_picture_url", None
                ),
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


def update_user_linkedin_connection(
    email: str, linkedin_data: Dict[str, Any]
) -> bool:
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
                "linkedin_access_token":
                    linkedin_data["linkedin_access_token"],
                "profile_picture_url": linkedin_data.get(
                    "profile_picture_url", None
                ),
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
                      github_id, github_access_token, profile_picture_url,
                      is_github_connected)
    VALUES (:email, :name, :password, :linkedin_url, :github_url,
            :github_id, :github_access_token, :profile_picture_url,
            :is_github_connected)
    """)

    try:
        session.execute(
            query,
            {
                "email": user_data["email"],
                "name": user_data["name"],
                "password": user_data.get(
                    "password", ""
                ),  # Empty password for GitHub users
                "linkedin_url": user_data.get("linkedin_url", None),
                "github_url": user_data.get("github_url", None),
                "github_id": user_data["github_id"],
                "github_access_token": user_data["github_access_token"],
                "profile_picture_url": user_data.get(
                    "profile_picture_url", None
                ),
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


def update_user_github_connection(email: str,
                                  github_data: Dict[str, Any]) -> bool:
    """Update existing user with GitHub OAuth data."""
    session = get_session()
    if not session:
        raise RuntimeError("Database connection not available")

    query = text("""
    UPDATE users
    SET github_id = :github_id,
        github_access_token = :github_access_token,
        github_url = :github_url,
        profile_picture_url = \
        COALESCE(:profile_picture_url, profile_picture_url),
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
                "profile_picture_url":
                    github_data.get("profile_picture_url", None),
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


def create_user_skills(email: str, skills: List[str]) -> bool:
    """Create user skills entries with default proficiency of 3."""
    if not skills:
        return True  # No skills to insert

    session = get_session()
    if not session:
        raise RuntimeError("Database connection not available")

    try:
        # Insert each skill as a separate record
        for skill in skills:
            query = text("""
            INSERT INTO user_skills (email, skill, proficiency)
            VALUES (:email, :skill, :proficiency)
            """)

            session.execute(query, {
                "email": email,
                "skill": skill,
                "proficiency": "3"  # Default proficiency as string
            })

        session.commit()
        session.close()
        return True
    except Exception as e:
        session.rollback()
        session.close()
        print(f"Error creating user skills: {e}")
        return False


def get_user_skills(email: str) -> List[Dict[str, str]]:
    """Get all skills for a user."""
    session = get_session()
    if not session:
        raise RuntimeError("Database connection not available")

    query = text("SELECT skill, proficiency FROM user_skills \
                 WHERE email = :email")
    result = session.execute(query, {"email": email})
    skills = result.fetchall()
    session.close()

    return [{
        "skill": skill.skill,
        "proficiency": skill.proficiency
        } for skill in skills]


def update_user_skill_proficiency(email: str,
                                  skill: str,
                                  proficiency: str) -> bool:
    """Update proficiency for a specific user skill."""
    session = get_session()
    if not session:
        raise RuntimeError("Database connection not available")

    query = text("""
    UPDATE user_skills
    SET proficiency = :proficiency
    WHERE email = :email AND skill = :skill
    """)

    try:
        result = session.execute(query, {
            "email": email,
            "skill": skill,
            "proficiency": proficiency
        })
        session.commit()
        session.close()
        return result.rowcount > 0
    except Exception as e:
        session.rollback()
        session.close()
        print(f"Error updating user skill proficiency: {e}")
        return False


def delete_user_skill(email: str, skill: str) -> bool:
    """Delete a specific skill for a user."""
    session = get_session()
    if not session:
        raise RuntimeError("Database connection not available")

    query = text("DELETE FROM user_skills \
                 WHERE email = :email AND \
                 skill = :skill")

    try:
        result = session.execute(query, {"email": email, "skill": skill})
        session.commit()
        session.close()
        return result.rowcount > 0
    except Exception as e:
        session.rollback()
        session.close()
        print(f"Error deleting user skill: {e}")
        return False


def delete_all_user_skills(email: str) -> bool:
    """Delete all skills for a user (used when deleting user account)."""
    session = get_session()
    if not session:
        raise RuntimeError("Database connection not available")

    query = text("DELETE FROM user_skills WHERE email = :email")

    try:
        session.execute(query, {"email": email})
        session.commit()
        session.close()
        return True
    except Exception as e:
        session.rollback()
        session.close()
        print(f"Error deleting all user skills: {e}")
        return False


def update_user_profile(email: str, name: str = None, linkedin_url: str = None,
                        github_url: str = None, password: str = None) -> bool:
    """Update user profile information."""
    session = get_session()
    if not session:
        raise RuntimeError("Database connection not available")

    # Build dynamic update query based on provided fields
    update_fields = []
    params = {"email": email}

    if name is not None:
        update_fields.append("name = :name")
        params["name"] = name

    if linkedin_url is not None:
        update_fields.append("linkedin_url = :linkedin_url")
        params["linkedin_url"] = linkedin_url

    if github_url is not None:
        update_fields.append("github_url = :github_url")
        params["github_url"] = github_url

    if password is not None:
        update_fields.append("password = :password")
        params["password"] = password

    if not update_fields:
        session.close()
        return True  # Nothing to update

    query = text(f"UPDATE users SET \
                {', '.join(update_fields)} \
                WHERE email = :email")

    try:
        session.execute(query, params)
        session.commit()
        session.close()
        return True
    except Exception as e:
        session.rollback()
        session.close()
        print(f"Error updating user profile: {e}")
        return False


def add_user_skill(email: str, skill: str, proficiency: str = "3") -> bool:
    """Add a new skill for a user."""
    session = get_session()
    if not session:
        raise RuntimeError("Database connection not available")

    # Check if skill already exists for user
    check_query = text("SELECT COUNT(*) \
                       FROM user_skills WHERE \
                       email = :email AND skill = :skill")
    result = session.execute(check_query, {"email": email, "skill": skill})
    count = result.scalar()

    if count > 0:
        session.close()
        return False  # Skill already exists

    # Add new skill
    query = text("INSERT INTO user_skills \
                (email, skill, proficiency) \
                VALUES (:email, :skill, :proficiency)")

    try:
        session.execute(query, {
            "email": email,
            "skill": skill,
            "proficiency": proficiency
        })
        session.commit()
        session.close()
        return True
    except Exception as e:
        session.rollback()
        session.close()
        print(f"Error adding user skill: {e}")
        return False


def remove_user_skill(email: str, skill: str) -> bool:
    """Remove a specific skill for a user."""
    return delete_user_skill(email, skill)  # Reuse existing function


def create_user_interview(email: str,
                          title: str,
                          interview_text: str
                          ) -> Optional[Dict[str, Any]]:
    """Create a new user interview record."""
    session = get_session()
    if not session:
        raise RuntimeError("Database connection not available")

    try:
        query = text("""
        INSERT INTO user_interviews (email, title, interview_text)
        VALUES (:email, :title, :interview_text)
        RETURNING id, email, title, interview_text, created_at
        """)

        result = session.execute(query, {
            "email": email,
            "title": title,
            "interview_text": interview_text
        })

        interview = result.fetchone()
        session.commit()
        session.close()

        if interview:
            return {
                "id": interview.id,
                "email": interview.email,
                "title": interview.title,
                "interview_text": interview.interview_text,
                "created_at": interview.created_at.isoformat()
            }
        return None

    except Exception as e:
        session.rollback()
        session.close()
        print(f"Error creating user interview: {e}")
        return None


def get_user_interviews(email: str) -> List[Dict[str, Any]]:
    """Get all interviews for a user by email."""
    session = get_session()
    if not session:
        raise RuntimeError("Database connection not available")

    try:
        query = text("""
        SELECT id, email, title, interview_text, created_at
        FROM user_interviews
        WHERE email = :email
        ORDER BY created_at DESC
        """)

        result = session.execute(query, {"email": email})
        interviews = result.fetchall()
        session.close()

        return [
            {
                "id": interview.id,
                "email": interview.email,
                "title": interview.title,
                "interview_text": interview.interview_text,
                "created_at": interview.created_at.isoformat()
            }
            for interview in interviews
        ]

    except Exception as e:
        session.close()
        print(f"Error fetching user interviews: {e}")
        return []


def get_user_interview_by_id(interview_id: int,
                             email: str
                             ) -> Optional[Dict[str, Any]]:
    """Get a specific interview by ID and email (for security)."""
    session = get_session()
    if not session:
        raise RuntimeError("Database connection not available")

    try:
        query = text("""
        SELECT id, email, title, interview_text, created_at
        FROM user_interviews
        WHERE id = :interview_id AND email = :email
        """)

        result = session.execute(query, {
            "interview_id": interview_id,
            "email": email
        })

        interview = result.fetchone()
        session.close()

        if interview:
            return {
                "id": interview.id,
                "email": interview.email,
                "title": interview.title,
                "interview_text": interview.interview_text,
                "created_at": interview.created_at.isoformat()
            }
        return None

    except Exception as e:
        session.close()
        print(f"Error fetching user interview: {e}")
        return None


def delete_user_interview(interview_id: int, email: str) -> bool:
    """Delete a specific interview by ID and email (for security)."""
    session = get_session()
    if not session:
        raise RuntimeError("Database connection not available")

    try:
        query = text("""
        DELETE FROM user_interviews
        WHERE id = :interview_id AND email = :email
        """)

        result = session.execute(query, {
            "interview_id": interview_id,
            "email": email
        })

        session.commit()
        session.close()

        return result.rowcount > 0

    except Exception as e:
        session.rollback()
        session.close()
        print(f"Error deleting user interview: {e}")
        return False


def create_user_evaluation(email: str,
                           interview_id: int,
                           evaluation_text: str
                           ) -> Optional[Dict[str, Any]]:
    """Create a new user evaluation record."""
    session = get_session()
    if not session:
        raise RuntimeError("Database connection not available")

    try:
        query = text("""
        INSERT INTO user_evaluation (email, interview_id, evaluation_text)
        VALUES (:email, :interview_id, :evaluation_text)
        RETURNING id, email, interview_id, evaluation_text, created_at
        """)

        result = session.execute(query, {
            "email": email,
            "interview_id": interview_id,
            "evaluation_text": evaluation_text
        })

        evaluation = result.fetchone()
        session.commit()
        session.close()

        if evaluation:
            return {
                "id": evaluation.id,
                "email": evaluation.email,
                "interview_id": evaluation.interview_id,
                "evaluation_text": evaluation.evaluation_text,
                "created_at": evaluation.created_at.isoformat()
            }
        return None

    except Exception as e:
        session.rollback()
        session.close()
        print(f"Error creating user evaluation: {e}")
        return None


def get_user_evaluation_by_interview_id(interview_id: int,
                                        email: str
                                        ) -> Optional[Dict[str, Any]]:
    """Get evaluation for a specific interview by ID and email."""
    session = get_session()
    if not session:
        raise RuntimeError("Database connection not available")

    try:
        query = text("""
        SELECT id, email, interview_id, evaluation_text, created_at
        FROM user_evaluation
        WHERE interview_id = :interview_id AND email = :email
        """)

        result = session.execute(query, {
            "interview_id": interview_id,
            "email": email
        })

        evaluation = result.fetchone()
        session.close()

        if evaluation:
            return {
                "id": evaluation.id,
                "email": evaluation.email,
                "interview_id": evaluation.interview_id,
                "evaluation_text": evaluation.evaluation_text,
                "created_at": evaluation.created_at.isoformat()
            }
        return None

    except Exception as e:
        session.close()
        print(f"Error fetching user evaluation: {e}")
        return None


def get_user_evaluations(email: str) -> List[Dict[str, Any]]:
    """Get all evaluations for a user by email."""
    session = get_session()
    if not session:
        raise RuntimeError("Database connection not available")

    try:
        query = text("""
        SELECT ue.id, ue.email, ue.interview_id, ue.evaluation_text,
               ue.created_at, ui.title as interview_title
        FROM user_evaluation ue
        JOIN user_interviews ui ON ue.interview_id = ui.id
        WHERE ue.email = :email
        ORDER BY ue.created_at DESC
        """)

        result = session.execute(query, {"email": email})
        evaluations = result.fetchall()
        session.close()

        return [
            {
                "id": evaluation.id,
                "email": evaluation.email,
                "interview_id": evaluation.interview_id,
                "evaluation_text": evaluation.evaluation_text,
                "created_at": evaluation.created_at.isoformat(),
                "interview_title": evaluation.interview_title
            }
            for evaluation in evaluations
        ]

    except Exception as e:
        session.close()
        print(f"Error fetching user evaluations: {e}")
        return []
