"""
FastAPI routes for interview presets.
"""
from typing import Optional
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
    InterviewPresetDeleteResponse
)

router = APIRouter(prefix="/interview", tags=["interview"])


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
