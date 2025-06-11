"""
Authentication API for AptWise backend.
Contains endpoints for user login and account creation.
"""
from fastapi import FastAPI, HTTPException, Request
import hashlib
import uvicorn
import re
from typing import List, Dict, Optional, Any

app = FastAPI()

# In-memory storage for user data
users = []

# Email validation regex pattern
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
# URL validation regex pattern
URL_PATTERN = r'^https?://(?:www\.)?[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+(?:[/?].*)?$'


def validate_email(email: str) -> bool:
    """Validate email format using regex."""
    if not email or not isinstance(email, str):
        return False
    return bool(re.match(EMAIL_PATTERN, email))


def validate_url(url: str) -> bool:
    """Validate URL format using regex."""
    if not url or not isinstance(url, str):
        return False
    return bool(re.match(URL_PATTERN, url))


def hash_password(password: str) -> str:
    """Hash the password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


@app.post("/create-account")
async def create_account(request: Request):
    """Create a new user account."""
    # Parse request body
    try:
        user_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    
    # Validate required fields
    required_fields = ["name", "email", "password"]
    for field in required_fields:
        if field not in user_data or not user_data[field]:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    # Validate email format
    if not validate_email(user_data["email"]):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    # Validate URL formats if provided
    for url_field in ["linkedin_url", "github_url"]:
        if url_field in user_data and user_data[url_field] and not validate_url(user_data[url_field]):
            raise HTTPException(status_code=400, detail=f"Invalid {url_field} format")
    
    # Check if email already exists
    for user in users:
        if user["email"] == user_data["email"]:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash the password
    hashed_password = hash_password(user_data["password"])
    
    # Create new user record
    new_user = {
        "name": user_data["name"],
        "email": user_data["email"],
        "password": hashed_password,
        "linkedin_url": user_data.get("linkedin_url"),
        "github_url": user_data.get("github_url")
    }
    
    # Add user to the list
    users.append(new_user)
    
    # Return the user data without password
    return {
        "name": new_user["name"],
        "email": new_user["email"],
        "linkedin_url": new_user["linkedin_url"],
        "github_url": new_user["github_url"]
    }


@app.post("/login")
async def login(request: Request):
    """Authenticate a user."""
    try:
        user_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    
    # Validate required fields
    required_fields = ["email", "password"]
    for field in required_fields:
        if field not in user_data or not user_data[field]:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    # Validate email format
    if not validate_email(user_data["email"]):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    hashed_password = hash_password(user_data["password"])
    
    for user in users:
        if user["email"] == user_data["email"] and user["password"] == hashed_password:
            return {"status": "success", "message": "Login successful"}
    
    raise HTTPException(status_code=401, detail="Invalid email or password")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
