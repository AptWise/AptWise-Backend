"""
Authentication routes for user registration, login, and logout.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Response, status
from .models import UserCreate, UserLogin, UserResponse
from .utils import (create_access_token, set_access_cookies,
                    unset_jwt_cookies, get_current_user, hash_password)
from ..database import get_user_by_email, create_user, delete_user

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/create-account", response_model=UserResponse)
async def create_account(user_data: UserCreate, response: Response):
    """Create a new user account."""    # Check if email already exists
    existing_user = get_user_by_email(user_data.email)
    if existing_user:
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
        }    # Add user to database
    success = create_user(new_user)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable"
        )

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
    # Try to find user in database
    user = get_user_by_email(user_data.email)

    if user and user["password"] == hashed_password:
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
    db_user = get_user_by_email(current_user)
    if db_user:
        return {
            "name": db_user["name"],
            "email": db_user["email"],
            "linkedin_url": db_user["linkedin_url"],
            "github_url": db_user["github_url"]
        }

    raise HTTPException(status_code=404, detail="User not found")


@router.delete("/delete-account")
async def delete_account(response: Response, current_user: Optional[str] =
                         Depends(get_current_user)):
    """Delete a user account."""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    # Delete from database
    db_success = delete_user(current_user)

    if db_success:
        unset_jwt_cookies(response)  # Log the user out
        return {"status": "success", "message": "Account deleted successfully"}

    # If we couldn't delete the user,
    # it might not exist or there was a database error
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Could not delete user account"
    )
