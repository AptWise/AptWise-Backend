"""
Authentication API for AptWise backend.
Contains endpoints for user login and account creation with JWT authentication.
"""
from fastapi import FastAPI, HTTPException, Depends, Response, status, Cookie
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, field_validator
from typing import Optional
import uvicorn
import re
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
import hashlib

app = FastAPI()

# In-memory storage for user data
users = []

# Email validation regex pattern
EMAIL_PATTERN = \
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
# URL validation regex pattern
URL_PATTERN = \
    r'^https?://(?:www\.)?[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+(?:[/?].*)?$'

# JWT Settings
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 30  # 30 days

# OAuth2 password bearer for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)

# Cookie name for storing the JWT token
COOKIE_NAME = "access_token"


def create_access_token(data: dict,
                        expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) \
            + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
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
        secure=True,  # Set to True in production with HTTPS
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


# Pydantic models
class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None

    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v):
        if not re.match(EMAIL_PATTERN, v):
            raise ValueError('Invalid email format')
        return v

    @field_validator('linkedin_url', 'github_url')
    @classmethod
    def validate_url_format(cls, v):
        if v is not None and not re.match(URL_PATTERN, v):
            raise ValueError('Invalid URL format')
        return v


class UserLogin(BaseModel):
    email: str
    password: str

    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v):
        if not re.match(EMAIL_PATTERN, v):
            raise ValueError('Invalid email format')
        return v


class UserResponse(BaseModel):
    name: str
    email: str
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None


def hash_password(password: str) -> str:
    """Hash the password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


@app.post("/create-account", response_model=UserResponse)
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
    # Set the JWT cookies
    set_access_cookies(response, access_token)
    # Return user data (without password)
    return {
        "name": new_user["name"],
        "email": new_user["email"],
        "linkedin_url": new_user["linkedin_url"],
        "github_url": new_user["github_url"]
    }


@app.post("/login")
async def login(user_data: UserLogin, response: Response):
    """Authenticate a user."""
    hashed_password = hash_password(user_data.password)
    for user in users:
        if user["email"] == user_data.email \
                and user["password"] == hashed_password:
            # Create access token with JWT
            access_token = create_access_token(data={"sub": user_data.email})
            # Set the JWT cookies
            set_access_cookies(response, access_token)
            return {"status": "success", "message": "Login successful"}
    raise HTTPException(status_code=401, detail="Invalid email or password")


@app.post("/logout")
async def logout(response: Response):
    """Log out a user by clearing the JWT cookie."""
    unset_jwt_cookies(response)
    return {"status": "success", "message": "Successfully logged out"}


@app.get("/protected")
async def protected(current_user: Optional[str] = Depends(get_current_user)):
    """A protected endpoint that requires JWT authentication."""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"user": current_user, "message": "You are authenticated"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
