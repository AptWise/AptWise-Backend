"""
FastAPI routes for interview presets.
"""
from typing import Optional
import logging
from fastapi import APIRouter, HTTPException, Depends, status
from ..auth.utils import get_current_user
from ..database.database_preset_functions import (
    get_user_interview_presets,
    create_interview_preset,
    delete_interview_preset,
    get_interview_preset_by_id,
    update_interview_preset
)
from .models import (
    InterviewPresetCreate,
    InterviewPresetUpdate,
    InterviewPresetResponse,
    InterviewPresetListResponse,
    InterviewPresetDeleteResponse,
    InterviewQuestionRequest,
    InterviewQuestionResponse,
    InterviewPresetGenerationRequest,
    InterviewPresetGenerationResponse
)

router = APIRouter(prefix="/interview", tags=["interview"])
logger = logging.getLogger(__name__)


@router.get("/presets", response_model=InterviewPresetListResponse)
async def get_interview_presets(
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get all interview presets for the current user."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    try:
        presets = get_user_interview_presets(current_user)
        return InterviewPresetListResponse(
            presets=[InterviewPresetResponse(**preset) for preset in presets],
            total=len(presets)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/presets", response_model=InterviewPresetResponse)
async def create_preset(
    preset_data: InterviewPresetCreate,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Create a new interview preset for the current user."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    try:
        # Validate skills list
        if not preset_data.skills:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one skill is required"
            )

        # Create the preset
        created_preset = create_interview_preset(
            user_email=current_user,
            preset_data=preset_data.dict()
        )

        return InterviewPresetResponse(**created_preset)

    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create preset: {str(e)}"
        )


@router.get("/presets/{preset_id}", response_model=InterviewPresetResponse)
async def get_preset(
    preset_id: int,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get a specific interview preset by ID."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    try:
        preset = get_interview_preset_by_id(current_user, preset_id)
        if not preset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview preset not found"
            )

        return InterviewPresetResponse(**preset)

    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/presets/{preset_id}", response_model=InterviewPresetResponse)
async def update_preset(
    preset_id: int,
    preset_data: InterviewPresetUpdate,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Update an interview preset for the current user."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    try:
        # Validate skills list
        if not preset_data.skills:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one skill is required"
            )

        # Update the preset
        updated_preset = update_interview_preset(
            user_email=current_user,
            preset_id=preset_id,
            preset_data=preset_data.dict()
        )

        if not updated_preset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview preset not found"
            )

        return InterviewPresetResponse(**updated_preset)

    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update preset: {str(e)}"
        )


@router.delete("/presets/{preset_id}",
               response_model=InterviewPresetDeleteResponse)
async def delete_preset(
    preset_id: int,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Delete an interview preset for the current user."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    try:
        success = delete_interview_preset(current_user, preset_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview preset not found"
            )

        return InterviewPresetDeleteResponse(
            success=True,
            message="Interview preset deleted successfully"
        )

    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete preset: {str(e)}"
        )


# AI Interview Route
@router.post("/generate-question", response_model=InterviewQuestionResponse)
async def generate_interview_question(
    request: InterviewQuestionRequest,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Generate an interview question using AI."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    try:
        # Initialize AI service - import here to avoid circular imports
        from .ai_service import AIInterviewService

        # Initialize AI service
        ai_service = AIInterviewService()

        # Convert conversation history to the format expected by AI service
        conversation_messages = []
        for msg in request.conversation_history:
            conversation_messages.append({
                'role': msg.role,
                'content': msg.content
            })

        # Format conversation history
        conversation_history = ai_service.\
            format_conversation_history(conversation_messages)

        # Generate question
        result = ai_service.generate_interview_question(
            user_details=request.user_details,
            skills=request.skills,
            conversation_history=conversation_history,
            search_context=request.search_context
        )

        return InterviewQuestionResponse(
            question=result['question'],
            success=result['success'],
            message="Question generated successfully"
            if result['success'] else "Failed to generate question",
            search_context=result.get('search_context'),
            evaluation=result.get('evaluation')
        )

    except ImportError as e:
        logger.error(f"Failed to import AI service: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI service not available. \
            Please check Google Generative AI installation."
        )
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI service configuration error. \
            Please check environment variables."
        )
    except Exception as e:
        logger.error(f"Error generating interview question: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate question: {str(e)}"
        )


# AI Preset Generation Route
@router.post("/generate-preset",
             response_model=InterviewPresetGenerationResponse)
async def generate_interview_preset(
    request: InterviewPresetGenerationRequest,
    current_user: Optional[str] = Depends(get_current_user)
):
    """Generate an interview preset using AI."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    try:
        # Initialize AI preset service - import here to avoid circular imports
        from .preset_ai_service import AIPresetService

        # Initialize AI preset service
        ai_preset_service = AIPresetService()

        # Generate preset
        result = ai_preset_service.generate_interview_preset(
            description=request.description,
            user_skills=request.user_skills
        )

        return InterviewPresetGenerationResponse(**result)

    except ImportError as e:
        logger.error(f"Failed to import AI preset service: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI preset service not available. \
            Please check Google Generative AI installation."
        )
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI preset service configuration error. \
            Please check environment variables."
        )
    except Exception as e:
        logger.error(f"Error generating interview preset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate preset: {str(e)}"
        )
