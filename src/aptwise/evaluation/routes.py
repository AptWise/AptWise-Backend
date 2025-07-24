"""
API routes for interview evaluation.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from .models import EvaluationRequest, EvaluationResponse
from .evaluation_service import evaluation_service
from ..auth.utils import get_current_user
from ..database import (
    create_user_evaluation, get_user_evaluation_by_interview_id,
    get_user_evaluations
)
from pydantic import BaseModel
from typing import Optional, List, Dict
import json

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


class StoreEvaluationRequest(BaseModel):
    interview_id: int
    evaluation_data: dict


class EvaluationStorageResponse(BaseModel):
    success: bool
    message: str
    evaluation_id: Optional[int] = None


class UserEvaluationResponse(BaseModel):
    id: int
    interview_id: int
    evaluation_text: str
    created_at: str
    interview_title: Optional[str] = None


class EvaluationMetricsResponse(BaseModel):
    """Response model for evaluation metrics extraction."""
    success: bool
    overall_score: Optional[int] = None
    interview_grade: Optional[str] = None
    reference_coverage_score: Optional[int] = None
    dimension_scores: Optional[Dict] = None
    assessment_averages: Optional[Dict] = None
    individual_answers: Optional[List[Dict]] = None
    strengths: Optional[List[str]] = None
    areas_for_improvement: Optional[List[str]] = None
    next_steps: Optional[List[str]] = None
    total_questions_assessed: Optional[int] = None
    error: Optional[str] = None


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_interview(
    request: EvaluationRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Evaluate an interview using AI analysis.

    Args:
        request: Evaluation request containing interview data and conversation
        current_user: Currently authenticated user

    Returns:
        Evaluation results with scores and feedback
    """
    try:
        # Perform the evaluation
        evaluation_result = evaluation_service.evaluate_interview(
            interview_data=request.interview_data,
            conversation_history=request.conversation_history
        )

        if not evaluation_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Evaluation failed: \
                    {evaluation_result.get('error', 'Unknown error')}"
            )

        return EvaluationResponse(**evaluation_result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate interview: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for evaluation service."""
    try:
        # Simple check to ensure the service is working
        return {
            "status": "healthy",
            "service": "evaluation",
            "message": "Evaluation service is running"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation service health check failed: {str(e)}"
        )


@router.post("/metrics", response_model=EvaluationMetricsResponse)
async def extract_evaluation_metrics(
    request: EvaluationRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Extract structured evaluation metrics for frontend display.

    Args:
        request: Evaluation request containing interview data and conversation
        current_user: Currently authenticated user

    Returns:
        Structured metrics including Accurateness, Confidence,
        and Completeness scores
   """
    try:
        # Perform the evaluation
        evaluation_result = evaluation_service.evaluate_interview(
            interview_data=request.interview_data,
            conversation_history=request.conversation_history
        )

        # Extract metrics using the utility method
        metrics = evaluation_service.extract_assessment_metrics(
            evaluation_result
        )

        return EvaluationMetricsResponse(**metrics)

    except Exception as e:
        return EvaluationMetricsResponse(
            success=False,
            error=f"Failed to extract evaluation metrics: {str(e)}"
        )


@router.post("/summary")
async def get_evaluation_summary(
    request: EvaluationRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Get a brief text summary of the evaluation.

    Args:
        request: Evaluation request containing interview data and conversation
        current_user: Currently authenticated user

    Returns:
        Human-readable evaluation summary
    """
    try:
        # Perform the evaluation
        evaluation_result = evaluation_service.evaluate_interview(
            interview_data=request.interview_data,
            conversation_history=request.conversation_history
        )

        # Get summary using the utility method
        summary = evaluation_service.get_evaluation_summary(evaluation_result)

        return {
            "success": True,
            "summary": summary,
            "evaluation_completed": evaluation_result.get("success", False)
        }

    except Exception as e:
        return {
            "success": False,
            "summary": "Could not generate evaluation summary.",
            "error": str(e)
        }


@router.post("/store", response_model=EvaluationStorageResponse)
async def store_evaluation(
    request: StoreEvaluationRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Store evaluation data for a specific interview.

    Args:
        request: Request containing interview_id and evaluation_data
        current_user: Currently authenticated user

    Returns:
        Response indicating success or failure of storage
    """
    try:
        # Convert evaluation data to JSON string for storage
        evaluation_text = json.dumps(request.evaluation_data)

        # Store the evaluation in the database
        evaluation = create_user_evaluation(
            email=current_user,
            interview_id=request.interview_id,
            evaluation_text=evaluation_text
        )

        if evaluation:
            return EvaluationStorageResponse(
                success=True,
                message="Evaluation stored successfully",
                evaluation_id=evaluation["id"]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store evaluation"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store evaluation: {str(e)}"
        )


@router.get("/interview/{interview_id}", response_model=UserEvaluationResponse)
async def get_evaluation_for_interview(
    interview_id: int,
    current_user: str = Depends(get_current_user)
):
    """
    Get evaluation for a specific interview.

    Args:
        interview_id: ID of the interview
        current_user: Currently authenticated user

    Returns:
        Evaluation data for the specified interview
    """
    try:
        evaluation = get_user_evaluation_by_interview_id(
            interview_id=interview_id,
            email=current_user
        )

        if not evaluation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation not found for this interview"
            )

        return UserEvaluationResponse(
            id=evaluation["id"],
            interview_id=evaluation["interview_id"],
            evaluation_text=evaluation["evaluation_text"],
            created_at=evaluation["created_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve evaluation: {str(e)}"
        )


@router.get("/user", response_model=List[UserEvaluationResponse])
async def get_user_evaluations_list(
    current_user: str = Depends(get_current_user)
):
    """
    Get all evaluations for the current user.

    Args:
        current_user: Currently authenticated user

    Returns:
        List of all evaluations for the user
    """
    try:
        evaluations = get_user_evaluations(email=current_user)

        return [
            UserEvaluationResponse(
                id=evaluation["id"],
                interview_id=evaluation["interview_id"],
                evaluation_text=evaluation["evaluation_text"],
                created_at=evaluation["created_at"],
                interview_title=evaluation.get("interview_title")
            )
            for evaluation in evaluations
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user evaluations: {str(e)}"
        )
