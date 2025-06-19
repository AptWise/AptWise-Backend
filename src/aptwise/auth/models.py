"""
Pydantic models for authentication.
"""
import re
from typing import Optional
from pydantic import BaseModel, field_validator
from ..config import EMAIL_PATTERN, URL_PATTERN


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
