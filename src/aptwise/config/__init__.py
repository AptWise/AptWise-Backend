"""
Configuration package for AptWise backend.
"""
from .cookie_config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    COOKIE_NAME,
    EMAIL_PATTERN,
    URL_PATTERN
)

from .db_config import get_session, engine

__all__ = [
    "SECRET_KEY",
    "ALGORITHM",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "COOKIE_NAME",
    "EMAIL_PATTERN",
    "URL_PATTERN",
    "get_session",
    "engine"
]
