"""
Pydantic models for interview evaluation.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class EvaluationRequest(BaseModel):
    """Request model for interview evaluation."""
    interview_data: Dict[str, Any] = \
        Field(...,
              description="Interview metadata")
    conversation_history: List[Dict[str, str]] = \
        Field(...,
              description="List of conversation messages")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TechnicalCompetency(BaseModel):
    """Model for technical competency assessment."""
    score: int = Field(...,
                       ge=1,
                       le=100,
                       description="Technical competency score")
    feedback: str = Field(..., description="Detailed technical assessment")


class CommunicationSkills(BaseModel):
    """Model for communication skills assessment."""
    score: int = Field(...,
                       ge=1,
                       le=100,
                       description="Communication skills score")
    feedback: str = Field(...,
                          description="Communication assessment")


class ProblemSolving(BaseModel):
    """Model for problem solving assessment."""
    score: int = Field(..., ge=1, le=100, description="Problem solving score")
    feedback: str = Field(..., description="Problem solving assessment")


class CulturalFit(BaseModel):
    """Model for cultural fit assessment."""
    score: int = Field(..., ge=1, le=100, description="Cultural fit score")
    feedback: str = Field(..., description="Cultural fit assessment")


class DetailedFeedback(BaseModel):
    """Model for detailed feedback."""
    positive_highlights: List[str] = \
        Field(...,
              description="Positive moments from the interview")
    improvement_suggestions: List[str] = \
        Field(...,
              description="Actionable improvement suggestions")


class EvaluationResult(BaseModel):
    """Model for evaluation results."""
    overall_score: int = \
        Field(...,
              ge=1,
              le=100,
              description="Overall interview score")
    performance_summary: str = \
        Field(...,
              description="Overall performance summary")
    strengths: List[str] = Field(..., description="Candidate strengths")
    areas_for_improvement: List[str] = \
        Field(...,
              description="Areas for improvement")
    technical_competency: TechnicalCompetency
    communication_skills: CommunicationSkills
    problem_solving: ProblemSolving
    cultural_fit: CulturalFit
    detailed_feedback: DetailedFeedback
    next_steps: List[str] = Field(...,
                                  description="Recommended next steps")
    interview_grade: str = Field(...,
                                 description="Letter grade for the interview")


class EvaluationResponse(BaseModel):
    """Response model for interview evaluation."""
    success: bool = Field(..., description="Whether evaluation was successful")
    evaluation: Optional[EvaluationResult] = \
        Field(None,
              description="Evaluation results")
    evaluated_at: Optional[str] = Field(None,
                                        description="Evaluation timestamp")
    error: Optional[str] = \
        Field(None,
              description="Error message if evaluation failed")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
