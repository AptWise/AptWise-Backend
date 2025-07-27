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


class AssessmentDimension(BaseModel):
    """Model for individual assessment dimensions
        (Accurateness, Confidence, Completeness)."""
    score: int = Field(..., ge=1, le=100, description="Dimension score")
    feedback: str = Field(..., description="Dimension-specific feedback")


class IndividualAnswerAssessment(BaseModel):
    """Model for individual answer assessment with reference comparison."""
    question_number: int = \
        Field(..., description="Question number in the interview")
    question: str = Field(..., description="The interview question")
    user_answer: str = Field(..., description="Candidate's answer")
    reference_answer: str = \
        Field(..., description="Reference answer from knowledge base")
    accurateness: AssessmentDimension = \
        Field(..., description="Accurateness assessment")
    confidence: AssessmentDimension = \
        Field(..., description="Confidence assessment")
    completeness: AssessmentDimension = \
        Field(..., description="Completeness assessment")
    overall_answer_score: int = \
        Field(..., ge=1, le=100, description="Overall score for this answer")


class DetailedFeedback(BaseModel):
    """Model for detailed feedback."""
    positive_highlights: List[str] = \
        Field(...,
              description="Positive moments from the interview")
    improvement_suggestions: List[str] = \
        Field(...,
              description="Actionable improvement suggestions")


class SkillAssessment(BaseModel):
    """Model for individual skill assessment."""
    score: int = Field(..., ge=1, le=100, description="Skill score")
    feedback: str = Field(..., description="Skill-specific feedback")


class EvaluationMetric(BaseModel):
    """Model for evaluation metrics (Correctness, Completeness, Confidence)."""
    score: int = Field(..., ge=1, le=100, description="Metric score")
    feedback: str = Field(..., description="Metric-specific feedback")


class QuestionEvaluation(BaseModel):
    """Model for question evaluation metrics."""
    correctness: EvaluationMetric = \
        Field(..., description="Correctness assessment")
    completeness: EvaluationMetric = \
        Field(..., description="Completeness assessment")
    confidence: EvaluationMetric = \
        Field(..., description="Confidence assessment")


class DetailedBreakdown(BaseModel):
    """Model for detailed question breakdown."""
    question_number: int = \
        Field(..., description="Question \
        number in the interview")
    question: str = Field(..., description="The interview question")
    user_answer: str = Field(..., description="Candidate's answer")
    evaluation: QuestionEvaluation = \
        Field(..., description="Question evaluation metrics")


class EvaluationResult(BaseModel):
    """Model for evaluation results with \
       support for both new and legacy formats."""

    # New format fields (primary)
    final_score: Optional[int] = \
        Field(None, ge=1, le=100,
              description="Final interview score")
    overall_feedback: Optional[str] = \
        Field(None, description="Overall \
        performance feedback")
    skill_performance_summary: Optional[Dict[str, SkillAssessment]] = Field(
        None, description="Individual skill assessments"
    )
    detailed_breakdown: Optional[List[DetailedBreakdown]] = Field(
        None, description="Question-by-question analysis"
    )

    # Legacy format fields (for backward compatibility)
    overall_score: Optional[int] = \
        Field(None, ge=1, le=100,
              description="Overall interview score")
    performance_summary: Optional[str] = \
        Field(None, description="Overall \
            performance summary")
    individual_answer_assessments: \
        Optional[List[IndividualAnswerAssessment]] = Field(
            None, description="Individual answer \
            assessments with reference comparison"
        )
    technical_competency: Optional[TechnicalCompetency] = None
    communication_skills: Optional[CommunicationSkills] = None
    problem_solving: Optional[ProblemSolving] = None
    cultural_fit: Optional[CulturalFit] = None
    detailed_feedback: Optional[DetailedFeedback] = None

    # Common fields
    strengths: List[str] = Field(default_factory=list,
                                 description="Candidate strengths")
    areas_for_improvement: List[str] = Field(
        default_factory=list, description="Areas for improvement"
    )
    next_steps: Optional[List[str]] = Field(None,
                                            description="Recommended \
                                                next steps")
    interview_grade: Optional[str] = Field(None,
                                           description="Letter grade \
                                               for the interview")
    reference_coverage_score: Optional[int] = Field(
        None, ge=1, le=100, description="How well answers covered \
            reference knowledge"
    )


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
