"""
Database services for interview presets.
"""
import random
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy import text
from ..config.db_config import get_session


def generate_unique_preset_id() -> int:
    """Generate a unique 9-digit integer ID\
          for interview presets (within PostgreSQL integer range)."""
    session = get_session()
    if not session:
        raise RuntimeError("Database connection not available")

    max_attempts = 100
    for attempt in range(max_attempts):
        # Generate 9-digit random integer ID (100,000,000 to 999,999,999)
        preset_id = random.randint(100000000, 999999999)

        # Check if ID already exists
        query = text("SELECT id FROM user_interview_presets WHERE id = :id")
        result = session.execute(query, {"id": preset_id})

        if not result.fetchone():
            session.close()
            return preset_id

    session.close()
    raise RuntimeError("Failed to generate \
                       unique preset ID after maximum attempts")


def get_user_interview_presets(user_email: str) -> List[Dict[str, Any]]:
    """Get all interview presets for a user."""
    session = get_session()
    if not session:
        raise RuntimeError("Database connection not available")

    try:
        query = text("""
            SELECT id, preset_name, description,
            company, role, skills, created_at
            FROM user_interview_presets
            WHERE email = :email
            ORDER BY created_at DESC
        """)

        result = session.execute(query, {"email": user_email})
        presets = result.fetchall()

        preset_list = []
        for preset in presets:
            preset_dict = {
                "id": preset.id,
                "preset_name": preset.preset_name,
                "description": preset.description,
                "company": preset.company,
                "role": preset.role,
                "skills": preset.skills,
                "created_at": preset.created_at.isoformat()
                if preset.created_at else None
            }
            preset_list.append(preset_dict)

        return preset_list

    except Exception as e:
        raise RuntimeError(f"Failed to retrieve interview presets: {str(e)}")
    finally:
        session.close()


def create_interview_preset(user_email: str,
                            preset_data: Dict[str, Any]) \
                            -> Dict[str, Any]:
    """Create a new interview preset for a user."""
    session = get_session()
    if not session:
        raise RuntimeError("Database connection not available")

    try:
        # Generate unique ID
        preset_id = generate_unique_preset_id()

        # Insert new preset
        query = text("""
            INSERT INTO user_interview_presets
            (id, email, preset_name, description,
            company, role, skills, created_at)
            VALUES (:id, :email, :preset_name,
            :description, :company, :role, :skills, :created_at)
            RETURNING id, preset_name,
            description, company, role, skills, created_at
        """)

        # Prepare skills array - ensure it's a list of strings
        skills = preset_data.get("skills", [])
        if not isinstance(skills, list):
            skills = [skills] if skills else []

        params = {
            "id": preset_id,
            "email": user_email,
            "preset_name": preset_data["preset_name"],
            "description": preset_data["description"],
            "company": preset_data.get("company"),
            "role": preset_data.get("role"),
            "skills": skills,
            "created_at": datetime.utcnow()
        }

        result = session.execute(query, params)
        session.commit()

        created_preset = result.fetchone()

        return {
            "id": created_preset.id,
            "preset_name": created_preset.preset_name,
            "description": created_preset.description,
            "company": created_preset.company,
            "role": created_preset.role,
            "skills": created_preset.skills,
            "created_at": created_preset.created_at.isoformat()
            if created_preset.created_at else None
        }

    except Exception as e:
        session.rollback()
        raise RuntimeError(f"Failed to create interview preset: {str(e)}")
    finally:
        session.close()


def delete_interview_preset(user_email: str, preset_id: int) -> bool:
    """Delete an interview preset for a user."""
    session = get_session()
    if not session:
        raise RuntimeError("Database connection not available")

    try:
        # Check if preset exists and belongs to user
        check_query = text("""
            SELECT id FROM user_interview_presets
            WHERE id = :preset_id AND email = :email
        """)

        result = session.execute(check_query, {
            "preset_id": preset_id,
            "email": user_email
        })

        if not result.fetchone():
            return False  # Preset doesn't exist or doesn't belong to user

        # Delete the preset
        delete_query = text("""
            DELETE FROM user_interview_presets
            WHERE id = :preset_id AND email = :email
        """)

        session.execute(delete_query, {
            "preset_id": preset_id,
            "email": user_email
        })
        session.commit()

        return True

    except Exception as e:
        session.rollback()
        raise RuntimeError(f"Failed to delete interview preset: {str(e)}")
    finally:
        session.close()


def get_interview_preset_by_id(user_email: str,
                               preset_id: int) \
                                -> Optional[Dict[str, Any]]:
    """Get a specific interview preset by ID for a user."""
    session = get_session()
    if not session:
        raise RuntimeError("Database connection not available")

    try:
        query = text("""
            SELECT id, preset_name, description,
            company, role, skills, created_at
            FROM user_interview_presets
            WHERE id = :preset_id AND email = :email
        """)

        result = session.execute(query, {
            "preset_id": preset_id,
            "email": user_email
        })

        preset = result.fetchone()

        if not preset:
            return None

        return {
            "id": preset.id,
            "preset_name": preset.preset_name,
            "description": preset.description,
            "company": preset.company,
            "role": preset.role,
            "skills": preset.skills,
            "created_at": preset.created_at.isoformat()
            if preset.created_at else None
        }

    except Exception as e:
        raise RuntimeError(f"Failed to retrieve interview preset: {str(e)}")
    finally:
        session.close()


def update_interview_preset(user_email: str,
                            preset_id: int,
                            preset_data: Dict[str, Any]) \
                            -> Optional[Dict[str, Any]]:
    """Update an interview preset for a user."""
    session = get_session()
    if not session:
        raise RuntimeError("Database connection not available")

    try:
        # Check if preset exists and belongs to user
        check_query = text("""
            SELECT id FROM user_interview_presets
            WHERE id = :preset_id AND email = :email
        """)

        result = session.execute(check_query, {
            "preset_id": preset_id,
            "email": user_email
        })

        if not result.fetchone():
            return None  # Preset doesn't exist or doesn't belong to user

        # Prepare skills array
        skills = preset_data.get("skills", [])
        if not isinstance(skills, list):
            skills = [skills] if skills else []

        # Update the preset
        update_query = text("""
            UPDATE user_interview_presets
            SET preset_name = :preset_name,
                description = :description,
                company = :company,
                role = :role,
                skills = :skills
            WHERE id = :preset_id AND email = :email
            RETURNING id, preset_name, description,
            company, role, skills, created_at
        """)

        params = {
            "preset_id": preset_id,
            "email": user_email,
            "preset_name": preset_data["preset_name"],
            "description": preset_data["description"],
            "company": preset_data.get("company"),
            "role": preset_data.get("role"),
            "skills": skills
        }

        result = session.execute(update_query, params)
        session.commit()

        updated_preset = result.fetchone()

        return {
            "id": updated_preset.id,
            "preset_name": updated_preset.preset_name,
            "description": updated_preset.description,
            "company": updated_preset.company,
            "role": updated_preset.role,
            "skills": updated_preset.skills,
            "created_at": updated_preset.created_at.isoformat()
            if updated_preset.created_at else None
        }

    except Exception as e:
        session.rollback()
        raise RuntimeError(f"Failed to update interview preset: {str(e)}")
    finally:
        session.close()
