"""
Database package for the application.
"""

from ..config.db_config import get_session, engine, metadata
from .db_auth_services import (
    get_user_by_email, create_user, delete_user, get_all_users,
    get_user_by_linkedin_id, create_user_with_linkedin,
    update_user_linkedin_connection, disconnect_user_linkedin,
    get_user_by_github_id, create_user_with_github,
    update_user_github_connection, disconnect_user_github
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
    "disconnect_user_github"
]
