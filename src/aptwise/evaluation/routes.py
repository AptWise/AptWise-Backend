"""
API routes for interview evaluation.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from .models import EvaluationRequest, EvaluationResponse
from .evaluation_service import evaluation_service
from ..auth.utils import get_current_user

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


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
