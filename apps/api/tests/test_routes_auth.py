"""Tests for authentication routes."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from main import app


class TestAuthRoutes:
    """Test authentication route endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @patch('routes.auth.verify_hmac_signature')
    @patch('routes.auth.get_account_by_fub_id')
    @patch('routes.auth.create_or_update_account')
    @patch('routes.auth.create_jwt_token')
    def test_iframe_login_success(self, mock_create_jwt, mock_create_account,
                                mock_get_account, mock_verify_hmac, client):
        """Test successful iframe login."""
        # Setup mocks
        mock_verify_hmac.return_value = True
        mock_get_account.return_value = None
        mock_create_account.return_value = {
            'account_id': 123,
            'fub_account_id': 'fub_123',
            'subscription_status': 'trialing'
        }
        mock_create_jwt.return_value = "jwt_token"
        
        request_data = {
            "context": '{"accountId": "fub_123"}',
            "signature": "valid_signature"
        }
        
        response = client.post("/api/v1/auth/iframe-login", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["account_id"] == 123
        assert data["fub_account_id"] == "fub_123"
        assert "token" in data

    @patch('routes.auth.verify_hmac_signature')
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
