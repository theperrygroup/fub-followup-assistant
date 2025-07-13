"""Stripe webhook routes for handling billing events.

This module processes Stripe webhook events for subscription management,
payment processing, and account status updates.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from loguru import logger
from sqlmodel import Session

from routes.auth import get_db_session
from services.stripe_service import StripeService


router = APIRouter(prefix="/stripe", tags=["stripe"])


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    session: Session = Depends(get_db_session)
) -> dict:
    """Handle Stripe webhook events.
    
    This endpoint processes various Stripe events including:
    - checkout.session.completed
    - customer.subscription.updated
    - customer.subscription.deleted
    - invoice.payment_succeeded
    - invoice.payment_failed
    
    Args:
        request: FastAPI request object containing webhook payload.
        session: Database session.
        
    Returns:
        Success response.
        
    Raises:
        HTTPException: If webhook verification fails or event processing fails.
    """
    try:
        # Get raw payload and signature
        payload = await request.body()
        signature = request.headers.get("stripe-signature")
        
        if not signature:
            logger.error("Missing Stripe signature header")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing signature header"
            )
        
        # Initialize Stripe service
        stripe_service = StripeService()
        
        # Verify webhook signature and parse event
        try:
            event = stripe_service.verify_webhook_signature(payload, signature)
        except ValueError as e:
            logger.error(f"Webhook signature verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid signature"
            )
        
        # Process the webhook event
        await stripe_service.handle_webhook_event(session, event)
        
        logger.info(f"Successfully processed Stripe webhook event: {event.get('type')}")
        
        return {"status": "success"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stripe webhook processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        ) 