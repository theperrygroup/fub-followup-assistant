"""Follow Up Boss integration routes.

This module provides endpoints for interacting with Follow Up Boss,
including creating notes from AI responses.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from pydantic import BaseModel, Field
from sqlmodel import Session

from models import Account
from routes.auth import get_current_account, get_db_session
from services.fub_service import FubService
from auth import AuthenticationError


router = APIRouter(prefix="/fub", tags=["fub"])


class CreateNoteRequest(BaseModel):
    """Request model for creating a note in Follow Up Boss.
    
    Attributes:
        content: Note content to create.
        person_id: Follow Up Boss person ID.
    """
    content: str = Field(..., max_length=2000, description="Note content")
    person_id: str = Field(..., description="Follow Up Boss person ID")


class CreateNoteResponse(BaseModel):
    """Response model for note creation.
    
    Attributes:
        note_id: ID of the created note.
        person_id: Follow Up Boss person ID.
        success: Whether the note was created successfully.
    """
    note_id: str = Field(..., description="ID of the created note")
    person_id: str = Field(..., description="Follow Up Boss person ID")
    success: bool = Field(..., description="Success status")


@router.post("/note", response_model=CreateNoteResponse)
async def create_note(
    request: CreateNoteRequest,
    account: Account = Depends(get_current_account),
    session: Session = Depends(get_db_session)
) -> CreateNoteResponse:
    """Create a note in Follow Up Boss.
    
    This endpoint allows writing AI-generated responses or other content
    as notes in Follow Up Boss for the specified person.
    
    Args:
        request: Note creation request.
        account: Current authenticated account.
        session: Database session.
        
    Returns:
        Note creation response with note ID.
        
    Raises:
        HTTPException: If note creation fails or authentication error occurs.
    """
    try:
        # Validate input
        if not request.content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Note content cannot be empty"
            )
        
        if not request.person_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Person ID cannot be empty"
            )
        
        if not account.access_token or not account.refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account not properly authenticated with Follow Up Boss"
            )
        
        # Create note via FUB API
        fub_service = FubService()
        note_data, new_access_token, new_refresh_token = await fub_service.create_note(
            access_token=account.access_token,
            refresh_token=account.refresh_token,
            person_id=request.person_id,
            note_content=request.content
        )
        
        # Update tokens if they were refreshed
        if new_access_token != account.access_token:
            account.access_token = new_access_token
            account.refresh_token = new_refresh_token
            session.commit()
        
        note_id = note_data.get("id", "unknown")
        
        logger.info(f"Note created in FUB for account {account.fub_account_id}, person {request.person_id}")
        
        return CreateNoteResponse(
            note_id=str(note_id),
            person_id=request.person_id,
            success=True
        )
        
    except AuthenticationError as e:
        logger.error(f"FUB authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to authenticate with Follow Up Boss"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Note creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create note"
        ) 