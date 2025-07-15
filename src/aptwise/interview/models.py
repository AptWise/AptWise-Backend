"""
Pydantic models for interview presets.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class InterviewPresetBase(BaseModel):
    """Base model for interview presets."""
    preset_name: str = \
        Field(..., min_length=1, max_length=255,
              description="Name of the interview preset")
    description: str = \
        Field(..., min_length=1,
              description="Description of the interview preset")
    company: Optional[str] = \
        Field(None, max_length=255, description="Company name")
    role: Optional[str] = \
        Field(None, max_length=255, description="Job role")
    skills: List[str] = \
        Field(..., description="List of skills for the interview")


class InterviewPresetCreate(InterviewPresetBase):
    """Model for creating an interview preset."""
    pass


class InterviewPresetUpdate(InterviewPresetBase):
    """Model for updating an interview preset."""
    pass


class InterviewPresetResponse(InterviewPresetBase):
    """Model for interview preset response."""
    id: int = Field(..., description="Unique ID of the preset")
    created_at: Optional[str] = Field(None, description="Creation timestamp")

    class Config:
        from_attributes = True


class InterviewPresetListResponse(BaseModel):
    """Model for interview preset list response."""
    presets: List[InterviewPresetResponse] = \
        Field(..., description="List of interview presets")
    total: int = Field(..., description="Total number of presets")


class InterviewPresetDeleteResponse(BaseModel):
    """Model for interview preset deletion response."""
    success: bool = \
        Field(...,
              description="Whether the deletion was successful"
              )
    message: str = Field(..., description="Status message")
