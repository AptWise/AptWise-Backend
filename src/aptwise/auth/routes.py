"""
Authentication routes for user registration, login, and logout.
"""
from fastapi import APIRouter, HTTPException, Depends, Response, status
from typing import Optional
from .models import UserCreate, UserLogin, UserResponse
from .utils import (create_access_token, set_access_cookies,
                    unset_jwt_cookies, get_current_user, hash_password)
from ..config import users

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/create-account", response_model=UserResponse)
async def create_account(user_data: UserCreate, response: Response):
    """Create a new user account."""
    # Check if email already exists
    for user in users:
        if user["email"] == user_data.email:
            raise HTTPException(status_code=400,
                                detail="Email already registered")

    # Hash the password
    hashed_password = hash_password(user_data.password)

    # Create new user record
    new_user = {
        "name": user_data.name,
        "email": user_data.email,
        "password": hashed_password,
        "linkedin_url": user_data.linkedin_url,
        "github_url": user_data.github_url
    }

    # Add user to the list
    users.append(new_user)

    # Create access token with JWT
    access_token = create_access_token(data={"sub": user_data.email})
    set_access_cookies(response, access_token)

    # Return user data (without password)
    return {
        "name": new_user["name"],
        "email": new_user["email"],
        "linkedin_url": new_user["linkedin_url"],
        "github_url": new_user["github_url"]
    }


@router.post("/login")
async def login(user_data: UserLogin, response: Response):
    """Authenticate a user."""
    hashed_password = hash_password(user_data.password)
    for user in users:
        if user["email"] == user_data.email and \
                user["password"] == hashed_password:
            # Create access token with JWT
            access_token = create_access_token(data={"sub": user_data.email})
            # Set the JWT cookies
            set_access_cookies(response, access_token)
            return {"status": "success", "message": "Login successful"}

    raise HTTPException(status_code=401, detail="Invalid email or password")


@router.post("/logout")
async def logout(response: Response):
    """Log out a user by clearing the JWT cookie."""
    unset_jwt_cookies(response)
    return {"status": "success", "message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: Optional[str] =
                                Depends(get_current_user)):
    """Get current user information."""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"})

    # Find user in database
    for user in users:
        if user["email"] == current_user:
            return {
                "name": user["name"],
                "email": user["email"],
                "linkedin_url": user["linkedin_url"],
                "github_url": user["github_url"]
            }

    raise HTTPException(status_code=404, detail="User not found")
