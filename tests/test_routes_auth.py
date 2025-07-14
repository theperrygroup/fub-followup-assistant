"""Tests for authentication routes.

This module tests all authentication endpoints including iframe login,
token refresh, and JWT management functionality.
"""

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlmodel import Session

from main import app
from routes.auth import (
    IframeLoginRequest, IframeLoginResponse, TokenRefreshResponse,
    get_db_session, get_current_account, iframe_login, refresh_token
)
from models import Account, SubscriptionStatus


class TestPydanticModels:
    """Test Pydantic request/response models."""

    def test_iframe_login_request_valid(self):
        """Test IframeLoginRequest model with valid data."""
        data = {
            "context": "test_context",
            "signature": "test_signature"
        }
        request = IframeLoginRequest(**data)
        assert request.context == "test_context"
        assert request.signature == "test_signature"

    def test_iframe_login_response_valid(self):
        """Test IframeLoginResponse model with valid data."""
        data = {
            "account_id": 123,
            "fub_account_id": "fub_123",
            "subscription_status": "active",
            "token": "jwt_token"
        }
        response = IframeLoginResponse(**data)
        assert response.account_id == 123
        assert response.fub_account_id == "fub_123"
        assert response.subscription_status == "active"
        assert response.token == "jwt_token"

    def test_token_refresh_response_valid(self):
        """Test TokenRefreshResponse model with valid data."""
        data = {"token": "new_jwt_token"}
        response = TokenRefreshResponse(**data)
        assert response.token == "new_jwt_token"


class TestDependencies:
    """Test FastAPI dependency functions."""

    @patch('routes.auth.create_engine')
    def test_get_db_session(self, mock_create_engine):
        """Test database session dependency."""
        from routes.auth import get_db_session
        
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        # Test that generator yields session
        gen = get_db_session()
        session = next(gen)
        assert isinstance(session, Session)

    @patch('routes.auth.verify_jwt_token')
    @patch('routes.auth.get_account_by_fub_id')
    def test_get_current_account_valid_token(self, mock_get_account, mock_verify_jwt):
        """Test getting current account with valid JWT token."""
        # Setup mocks
        mock_verify_jwt.return_value = {"fub_account_id": "fub_123"}
        mock_account = Account(
            fub_account_id="fub_123",
            subscription_status=SubscriptionStatus.active
        )
        mock_get_account.return_value = mock_account
        mock_session = Mock()
        
        # Create mock request with Authorization header
        mock_request = Mock()
        mock_request.headers = {"authorization": "Bearer valid_token"}
        
        result = get_current_account(mock_request, mock_session)
        assert result == mock_account
        mock_verify_jwt.assert_called_once_with("valid_token")
        mock_get_account.assert_called_once_with(mock_session, "fub_123")

    @patch('routes.auth.verify_jwt_token')
    def test_get_current_account_invalid_token(self, mock_verify_jwt):
        """Test getting current account with invalid JWT token."""
        mock_verify_jwt.return_value = None
        mock_session = Mock()
        mock_request = Mock()
        mock_request.headers = {"authorization": "Bearer invalid_token"}
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_account(mock_request, mock_session)
        
        assert exc_info.value.status_code == 401
        assert "Invalid token" in exc_info.value.detail

    def test_get_current_account_no_auth_header(self):
        """Test getting current account without authorization header."""
        mock_session = Mock()
        mock_request = Mock()
        mock_request.headers = {}
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_account(mock_request, mock_session)
        
        assert exc_info.value.status_code == 401
        assert "Authorization header required" in exc_info.value.detail

    @patch('routes.auth.verify_jwt_token')
    @patch('routes.auth.get_account_by_fub_id')
    def test_get_current_account_account_not_found(self, mock_get_account, mock_verify_jwt):
        """Test getting current account when account doesn't exist."""
        mock_verify_jwt.return_value = {"fub_account_id": "fub_123"}
        mock_get_account.return_value = None
        mock_session = Mock()
        mock_request = Mock()
        mock_request.headers = {"authorization": "Bearer valid_token"}
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_account(mock_request, mock_session)
        
        assert exc_info.value.status_code == 404
        assert "Account not found" in exc_info.value.detail


class TestIframeLoginEndpoint:
    """Test iframe login endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @patch('routes.auth.verify_hmac_signature')
    @patch('routes.auth.get_account_by_fub_id')
    @patch('routes.auth.create_or_update_account')
    @patch('routes.auth.create_jwt_token')
    def test_iframe_login_success_new_account(self, mock_create_jwt, mock_create_account,
                                            mock_get_account, mock_verify_hmac, client):
        """Test successful iframe login with new account creation."""
        # Setup mocks
        mock_verify_hmac.return_value = True
        mock_get_account.return_value = None  # Account doesn't exist
        mock_account = Account(
            account_id=123,
            fub_account_id="fub_123",
            subscription_status=SubscriptionStatus.trialing
        )
        mock_create_account.return_value = mock_account
        mock_create_jwt.return_value = "jwt_token"
        
        request_data = {
            "context": '{"accountId": "fub_123"}',
            "signature": "valid_signature"
        }
        
        response = client.post("/auth/iframe-login", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["account_id"] == 123
        assert data["fub_account_id"] == "fub_123"
        assert data["subscription_status"] == "trialing"
        assert data["token"] == "jwt_token"

    @patch('routes.auth.verify_hmac_signature')
    @patch('routes.auth.get_account_by_fub_id')
    @patch('routes.auth.create_jwt_token')
    def test_iframe_login_success_existing_account(self, mock_create_jwt, mock_get_account,
                                                 mock_verify_hmac, client):
        """Test successful iframe login with existing account."""
        # Setup mocks
        mock_verify_hmac.return_value = True
        mock_account = Account(
            account_id=456,
            fub_account_id="fub_456",
            subscription_status=SubscriptionStatus.active
        )
        mock_get_account.return_value = mock_account
        mock_create_jwt.return_value = "existing_jwt_token"
        
        request_data = {
            "context": '{"accountId": "fub_456"}',
            "signature": "valid_signature"
        }
        
        response = client.post("/auth/iframe-login", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["account_id"] == 456
        assert data["fub_account_id"] == "fub_456"
        assert data["subscription_status"] == "active"
        assert data["token"] == "existing_jwt_token"

    @patch('routes.auth.verify_hmac_signature')
    def test_iframe_login_invalid_signature(self, mock_verify_hmac, client):
        """Test iframe login with invalid HMAC signature."""
        mock_verify_hmac.return_value = False
        
        request_data = {
            "context": '{"accountId": "fub_123"}',
            "signature": "invalid_signature"
        }
        
        response = client.post("/auth/iframe-login", json=request_data)
        assert response.status_code == 401
        assert "Invalid signature" in response.json()["detail"]

    def test_iframe_login_invalid_context_json(self, client):
        """Test iframe login with invalid JSON context."""
        request_data = {
            "context": "invalid_json",
            "signature": "signature"
        }
        
        response = client.post("/auth/iframe-login", json=request_data)
        assert response.status_code == 400
        assert "Invalid context JSON" in response.json()["detail"]

    @patch('routes.auth.verify_hmac_signature')
    def test_iframe_login_missing_account_id(self, mock_verify_hmac, client):
        """Test iframe login with missing accountId in context."""
        mock_verify_hmac.return_value = True
        
        request_data = {
            "context": '{"some_other_field": "value"}',  # Missing accountId
            "signature": "valid_signature"
        }
        
        response = client.post("/auth/iframe-login", json=request_data)
        assert response.status_code == 400
        assert "accountId not found" in response.json()["detail"]

    @patch('routes.auth.verify_hmac_signature')
    @patch('routes.auth.get_account_by_fub_id')
    @patch('routes.auth.create_or_update_account')
    def test_iframe_login_account_creation_failure(self, mock_create_account, mock_get_account,
                                                  mock_verify_hmac, client):
        """Test iframe login when account creation fails."""
        mock_verify_hmac.return_value = True
        mock_get_account.return_value = None
        mock_create_account.return_value = None  # Account creation failed
        
        request_data = {
            "context": '{"accountId": "fub_123"}',
            "signature": "valid_signature"
        }
        
        response = client.post("/auth/iframe-login", json=request_data)
        assert response.status_code == 500
        assert "Failed to create account" in response.json()["detail"]


class TestTokenRefreshEndpoint:
    """Test token refresh endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @patch('routes.auth.should_refresh_token')
    @patch('routes.auth.create_jwt_token')
    @patch('routes.auth.get_current_account')
    def test_token_refresh_success(self, mock_get_account, mock_create_jwt, 
                                 mock_should_refresh, client):
        """Test successful token refresh."""
        # Setup mocks
        mock_account = Account(
            account_id=123,
            fub_account_id="fub_123",
            subscription_status=SubscriptionStatus.active
        )
        mock_get_account.return_value = mock_account
        mock_should_refresh.return_value = True
        mock_create_jwt.return_value = "new_jwt_token"
        
        headers = {"Authorization": "Bearer old_token"}
        response = client.get("/auth/refresh", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["token"] == "new_jwt_token"

    @patch('routes.auth.should_refresh_token')
    @patch('routes.auth.get_current_account')
    def test_token_refresh_not_needed(self, mock_get_account, mock_should_refresh, client):
        """Test token refresh when refresh is not needed."""
        mock_account = Account(
            account_id=123,
            fub_account_id="fub_123",
            subscription_status=SubscriptionStatus.active
        )
        mock_get_account.return_value = mock_account
        mock_should_refresh.return_value = False
        
        headers = {"Authorization": "Bearer recent_token"}
        response = client.get("/auth/refresh", headers=headers)
        
        assert response.status_code == 400
        assert "Token refresh not needed" in response.json()["detail"]

    def test_token_refresh_no_auth(self, client):
        """Test token refresh without authentication."""
        response = client.get("/auth/refresh")
        assert response.status_code == 401


class TestRouteIntegration:
    """Test route integration scenarios."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @patch('routes.auth.verify_hmac_signature')
    @patch('routes.auth.get_account_by_fub_id')
    @patch('routes.auth.create_or_update_account')
    @patch('routes.auth.create_jwt_token')
    @patch('routes.auth.should_refresh_token')
    def test_login_then_refresh_workflow(self, mock_should_refresh, mock_create_jwt,
                                       mock_create_account, mock_get_account,
                                       mock_verify_hmac, client):
        """Test complete workflow: login then refresh token."""
        # Setup login mocks
        mock_verify_hmac.return_value = True
        mock_get_account.return_value = None
        mock_account = Account(
            account_id=123,
            fub_account_id="fub_123",
            subscription_status=SubscriptionStatus.active
        )
        mock_create_account.return_value = mock_account
        mock_create_jwt.return_value = "initial_token"
        
        # Step 1: Login
        login_data = {
            "context": '{"accountId": "fub_123"}',
            "signature": "valid_signature"
        }
        login_response = client.post("/auth/iframe-login", json=login_data)
        assert login_response.status_code == 200
        
        # Step 2: Setup refresh mocks
        mock_should_refresh.return_value = True
        mock_create_jwt.return_value = "refreshed_token"
        
        with patch('routes.auth.get_current_account', return_value=mock_account):
            refresh_response = client.get("/auth/refresh", 
                                        headers={"Authorization": "Bearer initial_token"})
            assert refresh_response.status_code == 200
            assert refresh_response.json()["token"] == "refreshed_token"


class TestErrorHandling:
    """Test error handling in authentication routes."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @patch('routes.auth.verify_hmac_signature')
    def test_iframe_login_hmac_verification_exception(self, mock_verify_hmac, client):
        """Test iframe login when HMAC verification raises exception."""
        mock_verify_hmac.side_effect = Exception("HMAC verification error")
        
        request_data = {
            "context": '{"accountId": "fub_123"}',
            "signature": "signature"
        }
        
        response = client.post("/auth/iframe-login", json=request_data)
        assert response.status_code == 500

    @patch('routes.auth.get_current_account')
    def test_token_refresh_account_exception(self, mock_get_account, client):
        """Test token refresh when account lookup raises exception."""
        mock_get_account.side_effect = Exception("Database error")
        
        headers = {"Authorization": "Bearer token"}
        response = client.get("/auth/refresh", headers=headers)
        assert response.status_code == 500

    def test_invalid_request_format(self, client):
        """Test handling of malformed request data."""
        response = client.post("/auth/iframe-login", 
                             data="invalid json", 
                             headers={"Content-Type": "application/json"})
        assert response.status_code == 422 