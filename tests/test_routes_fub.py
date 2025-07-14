"""Tests for Follow Up Boss integration routes.

This module tests all FUB endpoints including note creation and
integration with Follow Up Boss API.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from main import app
from routes.fub import CreateNoteRequest, CreateNoteResponse, create_note
from models import Account, SubscriptionStatus


class TestPydanticModels:
    """Test Pydantic request/response models."""

    def test_create_note_request_valid(self):
        """Test CreateNoteRequest model with valid data."""
        data = {
            "content": "This is a follow-up note content.",
            "person_id": "person_123"
        }
        request = CreateNoteRequest(**data)
        assert request.content == "This is a follow-up note content."
        assert request.person_id == "person_123"

    def test_create_note_request_max_length_validation(self):
        """Test CreateNoteRequest content max length validation."""
        long_content = "x" * 2001  # Exceeds 2000 character limit
        
        with pytest.raises(ValueError):
            CreateNoteRequest(content=long_content, person_id="person_123")

    def test_create_note_response_valid(self):
        """Test CreateNoteResponse model with valid data."""
        data = {
            "note_id": "note_456",
            "person_id": "person_123",
            "success": True
        }
        response = CreateNoteResponse(**data)
        assert response.note_id == "note_456"
        assert response.person_id == "person_123"
        assert response.success is True


class TestCreateNoteEndpoint:
    """Test create note endpoint functionality."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @patch('routes.fub.FubService')
    @patch('routes.fub.get_current_account')
    def test_create_note_success(self, mock_get_account, mock_fub_service_class, client):
        """Test successful note creation."""
        # Setup mocks
        mock_account = Account(
            account_id=123,
            fub_account_id="fub_123",
            subscription_status=SubscriptionStatus.active,
            fub_access_token="access_token_123"
        )
        mock_get_account.return_value = mock_account
        
        # Mock FUB service
        mock_fub_service = Mock()
        mock_fub_service.create_note.return_value = "note_456"
        mock_fub_service_class.return_value = mock_fub_service
        
        request_data = {
            "content": "Follow-up note: Lead showed interest in our premium package.",
            "person_id": "person_123"
        }
        
        headers = {"Authorization": "Bearer valid_token"}
        response = client.post("/fub/note", json=request_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["note_id"] == "note_456"
        assert data["person_id"] == "person_123"
        assert data["success"] is True

    @patch('routes.fub.get_current_account')
    def test_create_note_no_auth(self, mock_get_account, client):
        """Test create note endpoint without authentication."""
        mock_get_account.side_effect = HTTPException(status_code=401, detail="Unauthorized")
        
        request_data = {
            "content": "Test note content",
            "person_id": "person_123"
        }
        
        response = client.post("/fub/note", json=request_data)
        assert response.status_code == 401

    @patch('routes.fub.get_current_account')
    def test_create_note_missing_fub_token(self, mock_get_account, client):
        """Test create note when account has no FUB access token."""
        mock_account = Account(
            fub_account_id="fub_123",
            subscription_status=SubscriptionStatus.active,
            fub_access_token=None  # Missing access token
        )
        mock_get_account.return_value = mock_account
        
        request_data = {
            "content": "Test note content",
            "person_id": "person_123"
        }
        
        headers = {"Authorization": "Bearer valid_token"}
        response = client.post("/fub/note", json=request_data, headers=headers)
        assert response.status_code == 400
        assert "FUB access token" in response.json()["detail"]

    @patch('routes.fub.FubService')
    @patch('routes.fub.get_current_account')
    def test_create_note_fub_api_error(self, mock_get_account, mock_fub_service_class, client):
        """Test create note when FUB API returns error."""
        mock_account = Account(
            fub_account_id="fub_123",
            subscription_status=SubscriptionStatus.active,
            fub_access_token="access_token_123"
        )
        mock_get_account.return_value = mock_account
        
        # Mock FUB service to raise authentication error
        mock_fub_service = Mock()
        from auth import AuthenticationError
        mock_fub_service.create_note.side_effect = AuthenticationError("Invalid FUB token")
        mock_fub_service_class.return_value = mock_fub_service
        
        request_data = {
            "content": "Test note content",
            "person_id": "person_123"
        }
        
        headers = {"Authorization": "Bearer valid_token"}
        response = client.post("/fub/note", json=request_data, headers=headers)
        assert response.status_code == 401
        assert "FUB authentication" in response.json()["detail"]

    @patch('routes.fub.FubService')
    @patch('routes.fub.get_current_account')
    def test_create_note_fub_general_error(self, mock_get_account, mock_fub_service_class, client):
        """Test create note when FUB service raises general error."""
        mock_account = Account(
            fub_account_id="fub_123",
            subscription_status=SubscriptionStatus.active,
            fub_access_token="access_token_123"
        )
        mock_get_account.return_value = mock_account
        
        # Mock FUB service to raise general error
        mock_fub_service = Mock()
        mock_fub_service.create_note.side_effect = Exception("FUB API is down")
        mock_fub_service_class.return_value = mock_fub_service
        
        request_data = {
            "content": "Test note content",
            "person_id": "person_123"
        }
        
        headers = {"Authorization": "Bearer valid_token"}
        response = client.post("/fub/note", json=request_data, headers=headers)
        assert response.status_code == 500
        assert "Failed to create note" in response.json()["detail"]

    def test_create_note_invalid_request_format(self, client):
        """Test create note endpoint with invalid request format."""
        # Missing required fields
        request_data = {"content": "Test content"}  # Missing person_id
        
        headers = {"Authorization": "Bearer valid_token"}
        response = client.post("/fub/note", json=request_data, headers=headers)
        assert response.status_code == 422

    def test_create_note_content_too_long(self, client):
        """Test create note endpoint with content exceeding max length."""
        request_data = {
            "content": "x" * 2001,  # Exceeds 2000 character limit
            "person_id": "person_123"
        }
        
        headers = {"Authorization": "Bearer valid_token"}
        response = client.post("/fub/note", json=request_data, headers=headers)
        assert response.status_code == 422

    def test_create_note_empty_content(self, client):
        """Test create note endpoint with empty content."""
        request_data = {
            "content": "",  # Empty content
            "person_id": "person_123"
        }
        
        headers = {"Authorization": "Bearer valid_token"}
        response = client.post("/fub/note", json=request_data, headers=headers)
        assert response.status_code == 422


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @patch('routes.fub.get_current_account')
    def test_create_note_database_error(self, mock_get_account, client):
        """Test create note endpoint when database error occurs."""
        mock_get_account.side_effect = Exception("Database connection failed")
        
        request_data = {
            "content": "Test note content",
            "person_id": "person_123"
        }
        
        headers = {"Authorization": "Bearer valid_token"}
        response = client.post("/fub/note", json=request_data, headers=headers)
        assert response.status_code == 500

    @patch('routes.fub.FubService')
    @patch('routes.fub.get_current_account')
    def test_create_note_service_instantiation_error(self, mock_get_account, 
                                                    mock_fub_service_class, client):
        """Test create note when FUB service instantiation fails."""
        mock_account = Account(
            fub_account_id="fub_123",
            subscription_status=SubscriptionStatus.active,
            fub_access_token="access_token_123"
        )
        mock_get_account.return_value = mock_account
        
        # Mock FUB service class to raise error on instantiation
        mock_fub_service_class.side_effect = Exception("Service initialization failed")
        
        request_data = {
            "content": "Test note content",
            "person_id": "person_123"
        }
        
        headers = {"Authorization": "Bearer valid_token"}
        response = client.post("/fub/note", json=request_data, headers=headers)
        assert response.status_code == 500


class TestIntegration:
    """Test integration scenarios."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @patch('routes.fub.FubService')
    @patch('routes.fub.get_current_account')
    def test_complete_note_creation_workflow(self, mock_get_account, mock_fub_service_class, client):
        """Test complete note creation workflow from authentication to FUB API call."""
        # Setup account with FUB integration
        mock_account = Account(
            account_id=123,
            fub_account_id="fub_123",
            subscription_status=SubscriptionStatus.active,
            fub_access_token="valid_access_token"
        )
        mock_get_account.return_value = mock_account
        
        # Setup FUB service with realistic note creation
        mock_fub_service = Mock()
        mock_fub_service.create_note.return_value = "note_789"
        mock_fub_service_class.return_value = mock_fub_service
        
        request_data = {
            "content": (
                "Follow-up from AI assistant:\n\n"
                "Based on recent lead activity, I recommend:\n"
                "• Scheduling a product demo\n"
                "• Discussing pricing options\n"
                "• Following up within 24 hours"
            ),
            "person_id": "lead_456"
        }
        
        headers = {"Authorization": "Bearer valid_token"}
        response = client.post("/fub/note", json=request_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["note_id"] == "note_789"
        assert data["person_id"] == "lead_456"
        assert data["success"] is True
        
        # Verify FUB service was called correctly
        mock_fub_service.create_note.assert_called_once()
        call_args = mock_fub_service.create_note.call_args
        assert call_args[1]["person_id"] == "lead_456"
        assert "AI assistant" in call_args[1]["content"]

    @patch('routes.fub.FubService')
    @patch('routes.fub.get_current_account')
    def test_note_creation_with_special_characters(self, mock_get_account, 
                                                  mock_fub_service_class, client):
        """Test note creation with special characters and formatting."""
        mock_account = Account(
            fub_account_id="fub_123",
            subscription_status=SubscriptionStatus.active,
            fub_access_token="access_token_123"
        )
        mock_get_account.return_value = mock_account
        
        mock_fub_service = Mock()
        mock_fub_service.create_note.return_value = "note_special"
        mock_fub_service_class.return_value = mock_fub_service
        
        request_data = {
            "content": (
                "Follow-up note with special chars: "
                "• Bullet points\n"
                "• Email: john@example.com\n"
                "• Phone: (555) 123-4567\n"
                "• Meeting @ 2:00 PM\n"
                "• Budget: $50,000 - $75,000"
            ),
            "person_id": "person_special"
        }
        
        headers = {"Authorization": "Bearer valid_token"}
        response = client.post("/fub/note", json=request_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["note_id"] == "note_special"
        assert data["success"] is True

    @patch('routes.fub.FubService')
    @patch('routes.fub.get_current_account')
    def test_multiple_note_creation_attempts(self, mock_get_account, 
                                           mock_fub_service_class, client):
        """Test multiple note creation requests for the same account."""
        mock_account = Account(
            fub_account_id="fub_123",
            subscription_status=SubscriptionStatus.active,
            fub_access_token="access_token_123"
        )
        mock_get_account.return_value = mock_account
        
        mock_fub_service = Mock()
        mock_fub_service.create_note.side_effect = ["note_1", "note_2", "note_3"]
        mock_fub_service_class.return_value = mock_fub_service
        
        headers = {"Authorization": "Bearer valid_token"}
        
        # Create multiple notes
        for i in range(3):
            request_data = {
                "content": f"Follow-up note #{i+1}",
                "person_id": f"person_{i+1}"
            }
            
            response = client.post("/fub/note", json=request_data, headers=headers)
            assert response.status_code == 200
            
            data = response.json()
            assert data["note_id"] == f"note_{i+1}"
            assert data["person_id"] == f"person_{i+1}"
        
        # Verify FUB service was called 3 times
        assert mock_fub_service.create_note.call_count == 3 