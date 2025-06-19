"""
Authentication utilities for JWT and password handling.
"""
import hashlib
from typing import Optional
from datetime import datetime, timedelta, timezone
from fastapi import Response, Cookie
from jose import JWTError, jwt
from ..config import (SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES,
                      COOKIE_NAME)


def create_access_token(data: dict,
                        expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + \
            timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def set_access_cookies(response: Response, token: str) -> None:
    """Set the JWT token in cookies."""
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=False,  # Set to True in production with HTTPS
    )


def unset_jwt_cookies(response: Response) -> None:
    """Remove the JWT token from cookies."""
    response.delete_cookie(COOKIE_NAME)


async def get_current_user(token: Optional[str] =
                           Cookie(None, alias=COOKIE_NAME)) -> Optional[str]:
    """Get the current user from the JWT token in cookies."""
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return email
    except JWTError:
        return None


def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()
