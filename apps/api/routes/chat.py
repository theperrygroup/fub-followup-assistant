"""Chat routes for AI-powered lead follow-up assistance.

This module provides the main chat endpoint that handles user questions
about leads and returns AI-generated follow-up advice.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from loguru import logger
from pydantic import BaseModel, Field
from sqlmodel import Session

from models import Account, SubscriptionStatus
from routes.auth import get_current_account, get_db_session
from services.chat_service import ChatService
from utils import check_rate_limit


router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Request model for chat endpoint.
    
    Attributes:
        person_id: Follow Up Boss person ID.
        question: User's question about the lead.
    """
    person_id: str = Field(..., description="Follow Up Boss person ID")
    question: str = Field(..., max_length=1000, description="Question about the lead")


class ChatResponse(BaseModel):
    """Response model for chat endpoint.
    
    Attributes:
        answer: AI-generated response.
        person_id: Follow Up Boss person ID.
    """
    answer: str = Field(..., description="AI-generated follow-up advice")
    person_id: str = Field(..., description="Follow Up Boss person ID")


async def check_subscription_active(account: Account) -> None:
    """Check if account has active subscription.
    
    Args:
        account: Account to check.
        
    Raises:
        HTTPException: If subscription is not active.
    """
    if account.subscription_status != SubscriptionStatus.ACTIVE:
        logger.warning(f"Inactive subscription for account {account.fub_account_id}: {account.subscription_status}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Subscription required. Current status: {account.subscription_status.value}"
        )


async def apply_rate_limiting(request: Request, account: Account) -> None:
    """Apply rate limiting to chat requests.
    
    Args:
        request: FastAPI request object.
        account: Current account.
        
    Raises:
        HTTPException: If rate limit is exceeded.
    """
    # Account-based rate limiting (10 requests per minute)
    account_rate_limit_key = f"account:{account.id}"
    if not await check_rate_limit(account_rate_limit_key, max_requests=10, window_minutes=1):
        logger.warning(f"Account rate limit exceeded for account {account.fub_account_id}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account rate limit exceeded. Please wait before making another request."
        )
    
    # IP-based rate limiting (100 requests per minute)
    client_ip = request.client.host if request.client else "unknown"
    ip_rate_limit_key = f"ip:{client_ip}"
    if not await check_rate_limit(ip_rate_limit_key, max_requests=100, window_minutes=1):
        logger.warning(f"IP rate limit exceeded for IP {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="IP rate limit exceeded. Please wait before making another request."
        )


@router.post("", response_model=ChatResponse)
async def chat(
    request: Request,
    chat_request: ChatRequest,
    account: Account = Depends(get_current_account),
    session: Session = Depends(get_db_session)
) -> ChatResponse:
    """Handle chat request and generate AI response.
    
    This endpoint processes user questions about leads and returns
    AI-generated follow-up advice based on lead data from Follow Up Boss.
    
    Rate limits:
    - 10 requests per minute per account
    - 100 requests per minute per IP address
    
    Args:
        request: FastAPI request object.
        chat_request: Chat request with person ID and question.
        account: Current authenticated account.
        session: Database session.
        
    Returns:
        AI-generated response with follow-up advice.
        
    Raises:
        HTTPException: If subscription is inactive or rate limit exceeded.
    """
    try:
        # Check subscription status
        await check_subscription_active(account)
        
        # Apply rate limiting
        await apply_rate_limiting(request, account)
        
        # Validate input
        if not chat_request.question.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question cannot be empty"
            )
        
        if not chat_request.person_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Person ID cannot be empty"
            )
        
        # Generate AI response
        chat_service = ChatService()
        answer = await chat_service.generate_response(
            session=session,
            account=account,
            person_id=chat_request.person_id,
            question=chat_request.question
        )
        
        logger.info(f"Chat response generated for account {account.fub_account_id}, person {chat_request.person_id}")
        
        return ChatResponse(
            answer=answer,
            person_id=chat_request.person_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate response"
        ) 