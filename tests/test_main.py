"""Tests for the main FastAPI application.

This module tests all endpoints, middleware, authentication, and utility functions
in the main.py FastAPI application including request/response handling and error cases.
"""

import json
import hmac
import hashlib
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from main import (
    app, verify_hmac_signature, create_jwt_token, verify_jwt_token,
    check_rate_limit, IframeLoginRequest, IframeLoginResponse, 
    ChatMessageRequest, ChatMessageResponse
)


class TestUtilityFunctions:
    """Test utility functions in main.py."""

    @pytest.mark.asyncio
    async def test_check_rate_limit_always_allows(self):
        """Test that fallback rate limiting always allows requests."""
        result = await check_rate_limit("test_key", 10, 1)
        assert result is True

    def test_verify_hmac_signature_valid(self):
        """Test HMAC signature verification with valid signature."""
        context = "test_context_data"
        secret = "test_secret"
        
        # Create valid signature
        expected_signature = hmac.new(
            secret.encode(),
            context.encode(),
            hashlib.sha256
        ).hexdigest()
        
        with patch.dict('os.environ', {'FUB_EMBED_SECRET': secret}):
            result = verify_hmac_signature(context, expected_signature)
            assert result is True

    def test_verify_hmac_signature_invalid(self):
        """Test HMAC signature verification with invalid signature."""
        context = "test_context_data"
        secret = "test_secret"
        invalid_signature = "invalid_signature"
        
        with patch.dict('os.environ', {'FUB_EMBED_SECRET': secret}):
            result = verify_hmac_signature(context, invalid_signature)
            assert result is False

    def test_verify_hmac_signature_exception_handling(self):
        """Test HMAC signature verification handles exceptions."""
        # Test with None values that would cause exceptions
        result = verify_hmac_signature(None, "signature")
        assert result is False

    def test_create_jwt_token_default_expiration(self):
        """Test JWT token creation with default expiration."""
        account_id = 123
        fub_account_id = "fub_123"
        
        with patch.dict('os.environ', {'JWT_SECRET': 'test_secret'}):
            token = create_jwt_token(account_id, fub_account_id)
            
            # Verify token can be decoded
            decoded = jwt.decode(token, 'test_secret', algorithms=['HS256'])
            assert decoded['account_id'] == account_id
            assert decoded['fub_account_id'] == fub_account_id
            assert 'exp' in decoded

    def test_create_jwt_token_custom_expiration(self):
        """Test JWT token creation with custom expiration."""
        account_id = 123
        fub_account_id = "fub_123"
        expires_delta = timedelta(hours=2)
        
        with patch.dict('os.environ', {'JWT_SECRET': 'test_secret'}):
            token = create_jwt_token(account_id, fub_account_id, expires_delta)
            
            decoded = jwt.decode(token, 'test_secret', algorithms=['HS256'])
            assert decoded['account_id'] == account_id
            assert decoded['fub_account_id'] == fub_account_id

    def test_verify_jwt_token_valid(self):
        """Test JWT token verification with valid token."""
        payload = {
            'account_id': 123,
            'fub_account_id': 'fub_123',
            'exp': datetime.utcnow() + timedelta(hours=1)
        }
        
        with patch.dict('os.environ', {'JWT_SECRET': 'test_secret'}):
            token = jwt.encode(payload, 'test_secret', algorithm='HS256')
            result = verify_jwt_token(token)
            
            assert result['account_id'] == 123
            assert result['fub_account_id'] == 'fub_123'

    def test_verify_jwt_token_invalid(self):
        """Test JWT token verification with invalid token."""
        invalid_token = "invalid.token.here"
        
        with patch.dict('os.environ', {'JWT_SECRET': 'test_secret'}):
            with pytest.raises(HTTPException) as exc_info:
                verify_jwt_token(invalid_token)
            assert exc_info.value.status_code == 401


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

    def test_chat_message_request_valid(self):
        """Test ChatMessageRequest model with valid data."""
        data = {
            "message": "Hello, how can I help?",
            "lead_context": {"name": "John Doe", "email": "john@example.com"}
        }
        request = ChatMessageRequest(**data)
        assert request.message == "Hello, how can I help?"
        assert request.lead_context == {"name": "John Doe", "email": "john@example.com"}

    def test_chat_message_response_valid(self):
        """Test ChatMessageResponse model with valid data."""
        data = {
            "response": "I can help you with follow-up suggestions."
        }
        response = ChatMessageResponse(**data)
        assert response.response == "I can help you with follow-up suggestions."


class TestAPIEndpoints:
    """Test FastAPI endpoints using TestClient."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "FUB Follow-up Assistant API"
        assert data["version"] == "1.0.0"

    @patch('main.asyncpg.connect')
    def test_setup_database_success(self, mock_connect, client):
        """Test database setup endpoint success."""
        mock_conn = AsyncMock()
        mock_connect.return_value.__aenter__.return_value = mock_conn
        mock_conn.execute.return_value = None
        
        with patch.dict('os.environ', {'DATABASE_URL': 'postgresql://test'}):
            response = client.post("/api/v1/setup-db")
            
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    @patch('main.asyncpg.connect')
    def test_test_database_success(self, mock_connect, client):
        """Test database test endpoint success."""
        mock_conn = AsyncMock()
        mock_connect.return_value.__aenter__.return_value = mock_conn
        mock_conn.fetchval.return_value = 1
        
        with patch.dict('os.environ', {'DATABASE_URL': 'postgresql://test'}):
            response = client.get("/api/v1/test-db")
            
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    @patch('main.verify_hmac_signature')
    @patch('main.get_account_by_fub_id')
    @patch('main.create_or_update_account')
    def test_iframe_login_success(self, mock_create_account, mock_get_account, 
                                mock_verify_hmac, client):
        """Test iframe login endpoint success."""
        # Setup mocks
        mock_verify_hmac.return_value = True
        mock_get_account.return_value = None  # New account
        mock_create_account.return_value = {
            'account_id': 123,
            'fub_account_id': 'fub_123',
            'subscription_status': 'trialing'
        }
        
        request_data = {
            "context": '{"accountId": "fub_123"}',
            "signature": "valid_signature"
        }
        
        with patch.dict('os.environ', {'JWT_SECRET': 'test_secret'}):
            response = client.post("/api/v1/auth/iframe-login", json=request_data)
            
        assert response.status_code == 200
        data = response.json()
        assert data["account_id"] == 123
        assert data["fub_account_id"] == "fub_123"
        assert "token" in data

    @patch('main.verify_hmac_signature')
    def test_iframe_login_invalid_signature(self, mock_verify_hmac, client):
        """Test iframe login with invalid signature."""
        mock_verify_hmac.return_value = False
        
        request_data = {
            "context": '{"accountId": "fub_123"}',
            "signature": "invalid_signature"
        }
        
        response = client.post("/api/v1/auth/iframe-login", json=request_data)
        assert response.status_code == 401

    def test_iframe_login_invalid_context(self, client):
        """Test iframe login with invalid JSON context."""
        request_data = {
            "context": "invalid_json",
            "signature": "signature"
        }
        
        response = client.post("/api/v1/auth/iframe-login", json=request_data)
        assert response.status_code == 400

    def test_create_fub_note_not_implemented(self, client):
        """Test FUB note creation endpoint (not implemented)."""
        response = client.post("/api/v1/fub/note")
        assert response.status_code == 200
        data = response.json()
        assert "not implemented" in data["message"].lower()

    def test_chat_message_no_auth(self, client):
        """Test chat message endpoint without authentication."""
        request_data = {
            "message": "Test message",
            "lead_context": {}
        }
        
        response = client.post("/api/v1/chat/message", json=request_data)
        assert response.status_code == 401


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @patch('main.asyncpg.connect')
    def test_database_connection_error(self, mock_connect, client):
        """Test database connection error handling."""
        mock_connect.side_effect = Exception("Database connection failed")
        
        response = client.get("/api/v1/test-db")
        assert response.status_code == 500

    @patch('main.verify_hmac_signature')
    def test_iframe_login_missing_account_id(self, mock_verify_hmac, client):
        """Test iframe login with missing accountId in context."""
        mock_verify_hmac.return_value = True
        
        request_data = {
            "context": '{"some_other_field": "value"}',  # Missing accountId
            "signature": "valid_signature"
        }
        
        response = client.post("/api/v1/auth/iframe-login", json=request_data)
        assert response.status_code == 400

    def test_invalid_json_request(self, client):
        """Test handling of invalid JSON in request body."""
        response = client.post("/api/v1/auth/iframe-login", 
                             data="invalid json", 
                             headers={"Content-Type": "application/json"})
        assert response.status_code == 422


class TestMiddleware:
    """Test middleware functionality."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_request_logging_middleware(self, client):
        """Test that request logging middleware works."""
        # Test that middleware doesn't break requests
        response = client.get("/health")
        assert response.status_code == 200
        
        # Test that X-Frame-Options header is removed (for iframe embedding)
        assert "x-frame-options" not in response.headers
        assert "X-Frame-Options" not in response.headers 