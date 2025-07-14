"""Tests for the main FastAPI application."""

import pytest
from fastapi.testclient import TestClient
from main import app, verify_hmac_signature, create_jwt_token, verify_jwt_token


class TestBasicFunctionality:
    """Test basic FastAPI functionality."""

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

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "FUB Follow-up Assistant API"
        assert data["version"] == "1.0.0"

    def test_verify_hmac_signature_handles_none(self):
        """Test HMAC signature verification handles None gracefully."""
        result = verify_hmac_signature(None, "signature")
        assert result is False

    def test_verify_jwt_token_invalid(self):
        """Test JWT token verification with invalid token."""
        result = verify_jwt_token("invalid.token.here")
        assert result is None
