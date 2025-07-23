"""
Pydantic models for authentication.
"""
import re
from typing import Optional, List
from pydantic import BaseModel, field_validator
from ..config import EMAIL_PATTERN, URL_PATTERN


class UserCreate(BaseModel):
    name: str
    email: str
    password: Optional[str] = None  # Optional for OAuth-only users
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    skills: Optional[List[str]] = []  # List of skills for the user
    # OAuth data (optional, for users registering via OAuth)
    linkedin_id: Optional[str] = None
    linkedin_access_token: Optional[str] = None
    github_id: Optional[str] = None
    github_access_token: Optional[str] = None
    profile_picture_url: Optional[str] = None
    is_linkedin_connected: Optional[bool] = False
    is_github_connected: Optional[bool] = False
    is_oauth_only: Optional[bool] = False  # Indicates OAuth-only registration

    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v):
        if not re.match(EMAIL_PATTERN, v):
            raise ValueError('Invalid email format')
        return v

    @field_validator('linkedin_url', 'github_url')
    @classmethod
    def validate_url_format(cls, v):
        # Convert empty strings to None
        if v == '':
            v = None
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
    linkedin_id: Optional[str] = None
    github_id: Optional[str] = None
    profile_picture_url: Optional[str] = None
    is_linkedin_connected: bool = False
    is_github_connected: bool = False


class LinkedInUserProfile(BaseModel):
    linkedin_id: str
    email: str
    first_name: str
    last_name: str
    full_name: str
    profile_picture_url: Optional[str] = None


class LinkedInAuthRequest(BaseModel):
    code: str
    state: str


class GitHubUserProfile(BaseModel):
    github_id: str
    username: str
    email: str
    name: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    blog: Optional[str] = None
    location: Optional[str] = None
    public_repos: int = 0
    followers: int = 0
    following: int = 0
    github_url: Optional[str] = None


class GitHubAuthRequest(BaseModel):
    code: str
    state: str


class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None

    @field_validator('linkedin_url', 'github_url')
    @classmethod
    def validate_url_format(cls, v):
        # Convert empty strings to None
        if v == '':
            v = None
        if v is not None and not re.match(URL_PATTERN, v):
            raise ValueError('Invalid URL format')
        return v


class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str


class SkillAdd(BaseModel):
    skill: str


class SkillRemove(BaseModel):
    skill: str


class UserInterviewCreate(BaseModel):
    title: str
    interview_text: str


class UserInterviewResponse(BaseModel):
    id: int
    title: str
    email: str
    interview_text: str
    created_at: str

    class Config:
        from_attributes = True
