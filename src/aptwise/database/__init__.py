"""
Database package for the application.
"""

from ..config.db_config import get_session, engine, metadata
from .db_auth_services import (
    get_user_by_email, create_user, delete_user, get_all_users,
    get_user_by_linkedin_id, create_user_with_linkedin,
    update_user_linkedin_connection, disconnect_user_linkedin,
    get_user_by_github_id, create_user_with_github,
    update_user_github_connection, disconnect_user_github,
    create_user_skills, get_user_skills, update_user_skill_proficiency,
    delete_user_skill, delete_all_user_skills, update_user_profile,
    add_user_skill, remove_user_skill, create_user_interview,
    get_user_interviews, get_user_interview_by_id, delete_user_interview,
    create_user_evaluation, get_user_evaluation_by_interview_id,
    get_user_evaluations, update_user_skills_from_evaluation
)
from .database_preset_functions import (
    generate_unique_preset_id,
    get_user_interview_presets,
    create_interview_preset,
    delete_interview_preset,
    get_interview_preset_by_id,
    update_interview_preset
)

__all__ = [
    "get_session",
    "engine",
    "metadata",
    "get_user_by_email",
    "create_user",
    "delete_user",
    "get_all_users",
    "get_user_by_linkedin_id",
    "create_user_with_linkedin",
    "update_user_linkedin_connection",
    "disconnect_user_linkedin",
    "get_user_by_github_id",
    "create_user_with_github",
    "update_user_github_connection",
    "disconnect_user_github",
    "create_user_skills",
    "get_user_skills",
    "update_user_skill_proficiency",
    "delete_user_skill",
    "delete_all_user_skills",
    "update_user_profile",
    "add_user_skill",
    "remove_user_skill",
    "update_user_skills_from_evaluation",
    "remove_user_skill",
    "create_user_interview",
    "get_user_interviews",
    "get_user_interview_by_id",
    "delete_user_interview",
    "create_user_evaluation",
    "get_user_evaluation_by_interview_id",
    "get_user_evaluations",
    "generate_unique_preset_id",
    "get_user_interview_presets",
    "create_interview_preset",
    "delete_interview_preset",
    "get_interview_preset_by_id",
    "update_interview_preset"
]
