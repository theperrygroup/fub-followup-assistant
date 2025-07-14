"""Tests for Stripe webhook routes.

This module tests all Stripe webhook endpoints including billing events,
subscription management, and payment processing.
"""

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from main import app
from routes.stripe_webhook import stripe_webhook


class TestStripeWebhookEndpoint:
    """Test Stripe webhook endpoint functionality."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @patch('routes.stripe_webhook.StripeService')
    def test_stripe_webhook_success(self, mock_stripe_service_class, client):
        """Test successful Stripe webhook processing."""
        # Mock Stripe service
        mock_stripe_service = Mock()
        mock_stripe_service.process_webhook.return_value = {"status": "processed"}
        mock_stripe_service_class.return_value = mock_stripe_service
        
        # Mock webhook payload
        webhook_payload = {
            "id": "evt_test_123",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_123",
                    "customer": "cus_test_123",
                    "subscription": "sub_test_123"
                }
            }
        }
        
        headers = {"stripe-signature": "t=1234567890,v1=test_signature"}
        response = client.post("/stripe/webhook", 
                             json=webhook_payload, 
                             headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_stripe_webhook_missing_signature(self, client):
        """Test Stripe webhook without signature header."""
        webhook_payload = {
            "id": "evt_test_123",
            "type": "checkout.session.completed"
        }
        
        response = client.post("/stripe/webhook", json=webhook_payload)
        assert response.status_code == 400
        assert "Missing Stripe signature" in response.json()["detail"]

    @patch('routes.stripe_webhook.StripeService')
    def test_stripe_webhook_invalid_signature(self, mock_stripe_service_class, client):
        """Test Stripe webhook with invalid signature."""
        # Mock Stripe service to raise signature verification error
        mock_stripe_service = Mock()
        mock_stripe_service.process_webhook.side_effect = ValueError("Invalid signature")
        mock_stripe_service_class.return_value = mock_stripe_service
        
        webhook_payload = {
            "id": "evt_test_123",
            "type": "checkout.session.completed"
        }
        
        headers = {"stripe-signature": "invalid_signature"}
        response = client.post("/stripe/webhook", 
                             json=webhook_payload, 
                             headers=headers)
        
        assert response.status_code == 400
        assert "signature" in response.json()["detail"].lower()

    @patch('routes.stripe_webhook.StripeService')
    def test_stripe_webhook_processing_error(self, mock_stripe_service_class, client):
        """Test Stripe webhook when processing raises error."""
        # Mock Stripe service to raise processing error
        mock_stripe_service = Mock()
        mock_stripe_service.process_webhook.side_effect = Exception("Database error")
        mock_stripe_service_class.return_value = mock_stripe_service
        
        webhook_payload = {
            "id": "evt_test_123",
            "type": "customer.subscription.updated"
        }
        
        headers = {"stripe-signature": "t=1234567890,v1=test_signature"}
        response = client.post("/stripe/webhook", 
                             json=webhook_payload, 
                             headers=headers)
        
        assert response.status_code == 500
        assert "webhook processing" in response.json()["detail"].lower()

    @patch('routes.stripe_webhook.StripeService')
    def test_stripe_webhook_checkout_completed(self, mock_stripe_service_class, client):
        """Test Stripe webhook for checkout.session.completed event."""
        mock_stripe_service = Mock()
        mock_stripe_service.process_webhook.return_value = {
            "event_type": "checkout.session.completed",
            "customer_id": "cus_test_123",
            "subscription_id": "sub_test_123"
        }
        mock_stripe_service_class.return_value = mock_stripe_service
        
        webhook_payload = {
            "id": "evt_checkout_123",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_123",
                    "customer": "cus_test_123",
                    "subscription": "sub_test_123",
                    "payment_status": "paid"
                }
            }
        }
        
        headers = {"stripe-signature": "t=1234567890,v1=test_signature"}
        response = client.post("/stripe/webhook", 
                             json=webhook_payload, 
                             headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    @patch('routes.stripe_webhook.StripeService')
    def test_stripe_webhook_subscription_updated(self, mock_stripe_service_class, client):
        """Test Stripe webhook for customer.subscription.updated event."""
        mock_stripe_service = Mock()
        mock_stripe_service.process_webhook.return_value = {
            "event_type": "customer.subscription.updated",
            "subscription_status": "active"
        }
        mock_stripe_service_class.return_value = mock_stripe_service
        
        webhook_payload = {
            "id": "evt_sub_update_123",
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_test_123",
                    "customer": "cus_test_123",
                    "status": "active"
                }
            }
        }
        
        headers = {"stripe-signature": "t=1234567890,v1=test_signature"}
        response = client.post("/stripe/webhook", 
                             json=webhook_payload, 
                             headers=headers)
        
        assert response.status_code == 200

    @patch('routes.stripe_webhook.StripeService')
    def test_stripe_webhook_subscription_deleted(self, mock_stripe_service_class, client):
        """Test Stripe webhook for customer.subscription.deleted event."""
        mock_stripe_service = Mock()
        mock_stripe_service.process_webhook.return_value = {
            "event_type": "customer.subscription.deleted",
            "subscription_status": "cancelled"
        }
        mock_stripe_service_class.return_value = mock_stripe_service
        
        webhook_payload = {
            "id": "evt_sub_delete_123",
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "id": "sub_test_123",
                    "customer": "cus_test_123",
                    "status": "canceled"
                }
            }
        }
        
        headers = {"stripe-signature": "t=1234567890,v1=test_signature"}
        response = client.post("/stripe/webhook", 
                             json=webhook_payload, 
                             headers=headers)
        
        assert response.status_code == 200

    @patch('routes.stripe_webhook.StripeService')
    def test_stripe_webhook_payment_succeeded(self, mock_stripe_service_class, client):
        """Test Stripe webhook for invoice.payment_succeeded event."""
        mock_stripe_service = Mock()
        mock_stripe_service.process_webhook.return_value = {
            "event_type": "invoice.payment_succeeded",
            "payment_status": "succeeded"
        }
        mock_stripe_service_class.return_value = mock_stripe_service
        
        webhook_payload = {
            "id": "evt_payment_123",
            "type": "invoice.payment_succeeded",
            "data": {
                "object": {
                    "id": "in_test_123",
                    "customer": "cus_test_123",
                    "subscription": "sub_test_123",
                    "amount_paid": 2000,
                    "status": "paid"
                }
            }
        }
        
        headers = {"stripe-signature": "t=1234567890,v1=test_signature"}
        response = client.post("/stripe/webhook", 
                             json=webhook_payload, 
                             headers=headers)
        
        assert response.status_code == 200

    @patch('routes.stripe_webhook.StripeService')
    def test_stripe_webhook_payment_failed(self, mock_stripe_service_class, client):
        """Test Stripe webhook for invoice.payment_failed event."""
        mock_stripe_service = Mock()
        mock_stripe_service.process_webhook.return_value = {
            "event_type": "invoice.payment_failed",
            "payment_status": "failed"
        }
        mock_stripe_service_class.return_value = mock_stripe_service
        
        webhook_payload = {
            "id": "evt_payment_fail_123",
            "type": "invoice.payment_failed",
            "data": {
                "object": {
                    "id": "in_test_123",
                    "customer": "cus_test_123",
                    "subscription": "sub_test_123",
                    "amount_due": 2000,
                    "status": "open"
                }
            }
        }
        
        headers = {"stripe-signature": "t=1234567890,v1=test_signature"}
        response = client.post("/stripe/webhook", 
                             json=webhook_payload, 
                             headers=headers)
        
        assert response.status_code == 200

    def test_stripe_webhook_invalid_json(self, client):
        """Test Stripe webhook with invalid JSON payload."""
        headers = {"stripe-signature": "t=1234567890,v1=test_signature"}
        response = client.post("/stripe/webhook", 
                             data="invalid json", 
                             headers={**headers, "Content-Type": "application/json"})
        
        assert response.status_code == 422

    def test_stripe_webhook_empty_payload(self, client):
        """Test Stripe webhook with empty payload."""
        headers = {"stripe-signature": "t=1234567890,v1=test_signature"}
        response = client.post("/stripe/webhook", 
                             json={}, 
                             headers=headers)
        
        assert response.status_code == 400


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @patch('routes.stripe_webhook.StripeService')
    def test_stripe_webhook_service_instantiation_error(self, mock_stripe_service_class, client):
        """Test webhook when Stripe service instantiation fails."""
        # Mock Stripe service class to raise error on instantiation
        mock_stripe_service_class.side_effect = Exception("Service initialization failed")
        
        webhook_payload = {
            "id": "evt_test_123",
            "type": "checkout.session.completed"
        }
        
        headers = {"stripe-signature": "t=1234567890,v1=test_signature"}
        response = client.post("/stripe/webhook", 
                             json=webhook_payload, 
                             headers=headers)
        
        assert response.status_code == 500

    @patch('routes.stripe_webhook.StripeService')
    def test_stripe_webhook_timeout_error(self, mock_stripe_service_class, client):
        """Test webhook when processing times out."""
        # Mock Stripe service to raise timeout error
        mock_stripe_service = Mock()
        mock_stripe_service.process_webhook.side_effect = TimeoutError("Request timeout")
        mock_stripe_service_class.return_value = mock_stripe_service
        
        webhook_payload = {
            "id": "evt_test_123",
            "type": "checkout.session.completed"
        }
        
        headers = {"stripe-signature": "t=1234567890,v1=test_signature"}
        response = client.post("/stripe/webhook", 
                             json=webhook_payload, 
                             headers=headers)
        
        assert response.status_code == 500


class TestIntegration:
    """Test integration scenarios."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @patch('routes.stripe_webhook.StripeService')
    def test_complete_webhook_processing_workflow(self, mock_stripe_service_class, client):
        """Test complete webhook processing workflow."""
        # Setup Stripe service with detailed processing
        mock_stripe_service = Mock()
        mock_stripe_service.process_webhook.return_value = {
            "event_id": "evt_test_123",
            "event_type": "checkout.session.completed",
            "customer_id": "cus_test_123",
            "subscription_id": "sub_test_123",
            "account_updated": True,
            "status": "processed"
        }
        mock_stripe_service_class.return_value = mock_stripe_service
        
        # Realistic webhook payload
        webhook_payload = {
            "id": "evt_test_123",
            "object": "event",
            "api_version": "2020-08-27",
            "created": 1234567890,
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_123",
                    "object": "checkout.session",
                    "customer": "cus_test_123",
                    "customer_email": "customer@example.com",
                    "payment_status": "paid",
                    "subscription": "sub_test_123",
                    "mode": "subscription"
                }
            },
            "livemode": False,
            "pending_webhooks": 1,
            "request": {
                "id": "req_test_123",
                "idempotency_key": None
            }
        }
        
        headers = {"stripe-signature": "t=1234567890,v1=valid_signature"}
        response = client.post("/stripe/webhook", 
                             json=webhook_payload, 
                             headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        # Verify service was called with correct parameters
        mock_stripe_service.process_webhook.assert_called_once()

    @patch('routes.stripe_webhook.StripeService')
    def test_webhook_idempotency(self, mock_stripe_service_class, client):
        """Test webhook idempotency handling."""
        mock_stripe_service = Mock()
        mock_stripe_service.process_webhook.return_value = {
            "status": "already_processed",
            "idempotent": True
        }
        mock_stripe_service_class.return_value = mock_stripe_service
        
        webhook_payload = {
            "id": "evt_duplicate_123",
            "type": "checkout.session.completed",
            "data": {"object": {"id": "cs_test_123"}}
        }
        
        headers = {"stripe-signature": "t=1234567890,v1=test_signature"}
        
        # Send same webhook twice
        for _ in range(2):
            response = client.post("/stripe/webhook", 
                                 json=webhook_payload, 
                                 headers=headers)
            assert response.status_code == 200

    @patch('routes.stripe_webhook.StripeService')
    def test_webhook_multiple_event_types(self, mock_stripe_service_class, client):
        """Test processing multiple different webhook event types."""
        mock_stripe_service = Mock()
        mock_stripe_service_class.return_value = mock_stripe_service
        
        event_types = [
            "checkout.session.completed",
            "customer.subscription.updated", 
            "customer.subscription.deleted",
            "invoice.payment_succeeded",
            "invoice.payment_failed"
        ]
        
        headers = {"stripe-signature": "t=1234567890,v1=test_signature"}
        
        for event_type in event_types:
            # Mock different responses for different event types
            mock_stripe_service.process_webhook.return_value = {
                "event_type": event_type,
                "status": "processed"
            }
            
            webhook_payload = {
                "id": f"evt_{event_type.replace('.', '_')}_123",
                "type": event_type,
                "data": {"object": {"id": "obj_test_123"}}
            }
            
            response = client.post("/stripe/webhook", 
                                 json=webhook_payload, 
                                 headers=headers)
            
            assert response.status_code == 200
            
        # Verify service was called for each event type
        assert mock_stripe_service.process_webhook.call_count == len(event_types) 