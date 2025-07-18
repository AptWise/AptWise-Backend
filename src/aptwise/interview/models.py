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


# AI Interview Models
class InterviewMessage(BaseModel):
    """Model for interview message."""
    role: str = Field(..., description="Message role (user/assistant)")
    content: str = Field(..., description="Message content")
    timestamp: Optional[str] = Field(None, description="Message timestamp")


class InterviewQuestionRequest(BaseModel):
    """Model for interview question request."""
    user_details: dict = Field(..., description="User details")
    skills: List[str] = Field(..., description="Interview skills")
    conversation_history: List[InterviewMessage] = Field(
        default=[], description="Previous conversation messages"
    )
    search_context: Optional[str] = Field(
        None, description="Search context from previous \
                           response for topic selection"
    )


class InterviewQuestionResponse(BaseModel):
    """Model for interview question response."""
    question: str = Field(..., description="Generated interview question")
    success: bool = \
        Field(...,
              description="Whether the request was successful")
    message: Optional[str] = Field(None, description="Status message")
    search_context: Optional[str] = Field(
        None, description="Search context for next question topic selection"
    )
    evaluation: Optional[dict] = Field(
        None, description="Evaluation metrics from AI response"
    )


# AI Preset Generation Models
class InterviewPresetGenerationRequest(BaseModel):
    """Model for AI preset generation request."""
    description: str = \
        Field(...,
              description="Description of the \
              interview preset to generate")
    user_skills: Optional[List[str]] = Field(
        None, description="User's existing skills to consider"
    )


class InterviewPresetGenerationResponse(BaseModel):
    """Model for AI preset generation response."""
    success: bool = \
        Field(...,
              description="Whether the generation was successful")
    preset_name: Optional[str] = \
        Field(None,
              description="Generated preset name")
    description: Optional[str] = \
        Field(None,
              description="Generated description")
    company: Optional[str] = \
        Field(None,
              description="Generated company name")
    role: Optional[str] = Field(None,
                                description="Generated role")
    skills: Optional[List[str]] = \
        Field(None,
              description="Generated skills list")
    error: Optional[str] = \
        Field(None,
              description="Error message if generation failed")
    raw_response: Optional[str] = \
        Field(None,
              description="Raw AI response for debugging")
