"""Stripe service for handling billing and subscription management.

This module provides functionality for processing Stripe webhooks,
managing customer subscriptions, and handling payment events.
"""

from typing import Optional

import stripe
from loguru import logger
from sqlmodel import Session

from config import settings
from models import Account, SubscriptionStatus
from utils import get_account_by_fub_id


class StripeService:
    """Service for handling Stripe billing operations."""
    
    def __init__(self):
        """Initialize the Stripe service."""
        stripe.api_key = settings.stripe_secret_key
    
    async def handle_webhook_event(self, session: Session, event: dict) -> None:
        """Handle incoming Stripe webhook events.
        
        Args:
            session: Database session.
            event: Stripe webhook event data.
        """
        event_type = event.get("type")
        
        try:
            if event_type == "checkout.session.completed":
                await self._handle_checkout_completed(session, event)
            elif event_type == "customer.subscription.updated":
                await self._handle_subscription_updated(session, event)
            elif event_type == "customer.subscription.deleted":
                await self._handle_subscription_deleted(session, event)
            elif event_type == "invoice.payment_succeeded":
                await self._handle_payment_succeeded(session, event)
            elif event_type == "invoice.payment_failed":
                await self._handle_payment_failed(session, event)
            else:
                logger.info(f"Unhandled Stripe event type: {event_type}")
                
        except Exception as e:
            logger.error(f"Error handling Stripe webhook event {event_type}: {e}")
            raise
    
    async def _handle_checkout_completed(self, session: Session, event: dict) -> None:
        """Handle successful checkout completion.
        
        Args:
            session: Database session.
            event: Stripe event data.
        """
        checkout_session = event["data"]["object"]
        customer_id = checkout_session.get("customer")
        fub_account_id = checkout_session.get("metadata", {}).get("fub_account_id")
        
        if not fub_account_id:
            logger.error("No fub_account_id in checkout session metadata")
            return
        
        # Update account with Stripe customer ID and activate subscription
        account = get_account_by_fub_id(session, fub_account_id)
        if account:
            account.stripe_customer_id = customer_id
            account.subscription_status = SubscriptionStatus.ACTIVE
            session.commit()
            logger.info(f"Activated subscription for account {fub_account_id}")
        else:
            logger.error(f"Account not found for fub_account_id: {fub_account_id}")
    
    async def _handle_subscription_updated(self, session: Session, event: dict) -> None:
        """Handle subscription status changes.
        
        Args:
            session: Database session.
            event: Stripe event data.
        """
        subscription = event["data"]["object"]
        customer_id = subscription.get("customer")
        status = subscription.get("status")
        
        # Find account by Stripe customer ID
        account = session.query(Account).filter(Account.stripe_customer_id == customer_id).first()
        
        if account:
            # Map Stripe status to our enum
            status_mapping = {
                "active": SubscriptionStatus.ACTIVE,
                "canceled": SubscriptionStatus.CANCELLED,
                "incomplete": SubscriptionStatus.INCOMPLETE,
                "past_due": SubscriptionStatus.PAST_DUE,
                "trialing": SubscriptionStatus.TRIALING,
                "unpaid": SubscriptionStatus.UNPAID,
            }
            
            new_status = status_mapping.get(status, SubscriptionStatus.CANCELLED)
            account.subscription_status = new_status
            session.commit()
            
            logger.info(f"Updated subscription status for customer {customer_id} to {new_status}")
        else:
            logger.error(f"Account not found for Stripe customer: {customer_id}")
    
    async def _handle_subscription_deleted(self, session: Session, event: dict) -> None:
        """Handle subscription cancellation.
        
        Args:
            session: Database session.
            event: Stripe event data.
        """
        subscription = event["data"]["object"]
        customer_id = subscription.get("customer")
        
        # Find account by Stripe customer ID
        account = session.query(Account).filter(Account.stripe_customer_id == customer_id).first()
        
        if account:
            account.subscription_status = SubscriptionStatus.CANCELLED
            session.commit()
            logger.info(f"Cancelled subscription for customer {customer_id}")
        else:
            logger.error(f"Account not found for Stripe customer: {customer_id}")
    
    async def _handle_payment_succeeded(self, session: Session, event: dict) -> None:
        """Handle successful payment.
        
        Args:
            session: Database session.
            event: Stripe event data.
        """
        invoice = event["data"]["object"]
        customer_id = invoice.get("customer")
        
        # Find account and ensure subscription is active
        account = session.query(Account).filter(Account.stripe_customer_id == customer_id).first()
        
        if account and account.subscription_status != SubscriptionStatus.ACTIVE:
            account.subscription_status = SubscriptionStatus.ACTIVE
            session.commit()
            logger.info(f"Reactivated subscription for customer {customer_id} after payment")
    
    async def _handle_payment_failed(self, session: Session, event: dict) -> None:
        """Handle failed payment.
        
        Args:
            session: Database session.
            event: Stripe event data.
        """
        invoice = event["data"]["object"]
        customer_id = invoice.get("customer")
        
        # Find account and mark as past due
        account = session.query(Account).filter(Account.stripe_customer_id == customer_id).first()
        
        if account:
            account.subscription_status = SubscriptionStatus.PAST_DUE
            session.commit()
            logger.info(f"Marked subscription as past due for customer {customer_id}")
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> dict:
        """Verify Stripe webhook signature and parse event.
        
        Args:
            payload: Raw webhook payload.
            signature: Stripe signature header.
            
        Returns:
            Parsed Stripe event.
            
        Raises:
            ValueError: If signature verification fails.
        """
        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                settings.stripe_webhook_secret
            )
            return event
        except ValueError as e:
            logger.error(f"Invalid Stripe webhook signature: {e}")
            raise
        except Exception as e:
            logger.error(f"Error parsing Stripe webhook: {e}")
            raise
    
    def create_checkout_session(
        self,
        fub_account_id: str,
        success_url: str,
        cancel_url: str
    ) -> stripe.checkout.Session:
        """Create a Stripe Checkout session for subscription.
        
        Args:
            fub_account_id: Follow Up Boss account ID.
            success_url: URL to redirect on success.
            cancel_url: URL to redirect on cancellation.
            
        Returns:
            Stripe Checkout session.
        """
        try:
            session = stripe.checkout.Session.create(
                mode="subscription",
                line_items=[
                    {
                        "price": settings.stripe_price_id_monthly,
                        "quantity": 1,
                    }
                ],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={"fub_account_id": fub_account_id}
            )
            return session
        except Exception as e:
            logger.error(f"Error creating Stripe checkout session: {e}")
            raise
    
    def create_customer_portal_session(self, customer_id: str, return_url: str) -> stripe.billing_portal.Session:
        """Create a Stripe customer portal session.
        
        Args:
            customer_id: Stripe customer ID.
            return_url: URL to return to after portal session.
            
        Returns:
            Stripe customer portal session.
        """
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url
            )
            return session
        except Exception as e:
            logger.error(f"Error creating customer portal session: {e}")
            raise 