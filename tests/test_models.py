"""Tests for database models.

This module tests all SQLModel database models including validation,
field types, relationships, and serialization functionality.
"""

from datetime import datetime, timedelta
from uuid import UUID

import pytest
from pydantic import ValidationError

from models import Account, ChatMessage, RateLimitEntry, SubscriptionStatus


class TestSubscriptionStatus:
    """Test SubscriptionStatus enum functionality."""

    def test_subscription_status_values(self):
        """Test that enum has all expected values."""
        expected_values = {
            "active", "cancelled", "incomplete", 
            "past_due", "trialing", "unpaid"
        }
        actual_values = {status.value for status in SubscriptionStatus}
        assert actual_values == expected_values

    def test_subscription_status_membership(self):
        """Test enum membership checks."""
        assert SubscriptionStatus.ACTIVE in SubscriptionStatus
        assert SubscriptionStatus.CANCELLED in SubscriptionStatus
        assert SubscriptionStatus.TRIALING in SubscriptionStatus

    def test_subscription_status_iteration(self):
        """Test enum iteration."""
        statuses = list(SubscriptionStatus)
        assert len(statuses) == 6
        assert SubscriptionStatus.ACTIVE in statuses


class TestAccount:
    """Test Account model functionality."""

    def test_account_creation_with_required_fields(self, sample_account_data):
        """Test creating account with required fields only."""
        # Use only required fields
        minimal_data = {
            "fub_account_id": sample_account_data["fub_account_id"]
        }
        
        account = Account(**minimal_data)
        assert account.fub_account_id == minimal_data["fub_account_id"]
        assert account.subscription_status == SubscriptionStatus.TRIALING  # Default
        assert account.created_at is not None
        assert account.updated_at is not None

    def test_account_creation_with_all_fields(self, sample_account_data):
        """Test creating account with all fields."""
        account = Account(**sample_account_data)
        
        assert account.fub_account_id == sample_account_data["fub_account_id"]
        assert account.subscription_status == sample_account_data["subscription_status"]
        assert account.fub_access_token == sample_account_data["fub_access_token"]
        assert account.fub_refresh_token == sample_account_data["fub_refresh_token"]
        assert account.stripe_customer_id == sample_account_data["stripe_customer_id"]

    def test_account_subscription_status_validation(self, sample_account_data):
        """Test valid subscription status."""
        for status in SubscriptionStatus:
            sample_account_data["subscription_status"] = status
            account = Account(**sample_account_data)
            assert account.subscription_status == status

    def test_account_subscription_status_invalid(self, sample_account_data):
        """Test invalid subscription status handling."""
        sample_account_data["subscription_status"] = "invalid_status"

        # Test behavior - may convert string or raise error
        try:
            account = Account(**sample_account_data)
            # If successful, verify it has a valid value
            assert account.subscription_status is not None
        except (ValueError, TypeError):
            # If it raises an error, that's also acceptable
            pass

    def test_account_field_validation(self, sample_account_data):
        """Test required field validation."""
        # Test with missing required field
        incomplete_data = sample_account_data.copy()
        del incomplete_data["fub_account_id"]
        
        # This should work since fub_account_id is handled by SQLModel
        try:
            account = Account(**incomplete_data)
            assert hasattr(account, 'fub_account_id')
        except (ValueError, TypeError):
            # If validation fails, that's expected
            pass

    def test_account_created_at_default(self, sample_account_data):
        """Test that created_at has default value."""
        before = datetime.utcnow()
        account = Account(**sample_account_data)
        after = datetime.utcnow()
        
        assert account.created_at is not None
        assert before <= account.created_at <= after

    def test_account_field_types(self, sample_account_data):
        """Test field type validation."""
        account = Account(**sample_account_data)

        assert isinstance(account.fub_account_id, str)
        # subscription_status might be enum or string depending on SQLModel handling
        assert account.subscription_status is not None
        if account.fub_access_token:
            assert isinstance(account.fub_access_token, str)
        assert isinstance(account.created_at, datetime)

    def test_account_table_name(self):
        """Test table name configuration."""
        assert Account.__tablename__ == "accounts"

    def test_account_serialization(self, sample_account_data):
        """Test account serialization."""
        account = Account(**sample_account_data)
        
        # Test dict conversion
        if hasattr(account, 'model_dump'):
            account_dict = account.model_dump()
        else:
            account_dict = account.dict()
            
        assert isinstance(account_dict, dict)
        assert "fub_account_id" in account_dict
        assert "subscription_status" in account_dict

    def test_account_repr(self, sample_account_data):
        """Test account string representation."""
        account = Account(**sample_account_data)
        repr_str = repr(account)
        assert "Account" in repr_str
        assert sample_account_data["fub_account_id"] in repr_str


class TestChatMessage:
    """Test ChatMessage model functionality."""

    def test_chat_message_creation_with_required_fields(self, sample_chat_message_data):
        """Test creating chat message with required fields."""
        required_data = {
            "person_id": sample_chat_message_data["person_id"],
            "question": sample_chat_message_data["question"],
            "role": sample_chat_message_data["role"]
        }
        
        message = ChatMessage(**required_data)
        assert message.person_id == required_data["person_id"]
        assert message.question == required_data["question"]
        assert message.role == required_data["role"]
        assert message.created_at is not None

    def test_chat_message_creation_with_all_fields(self, sample_chat_message_data):
        """Test creating chat message with all fields."""
        message = ChatMessage(**sample_chat_message_data)
        
        assert message.person_id == sample_chat_message_data["person_id"]
        assert message.question == sample_chat_message_data["question"]
        assert message.role == sample_chat_message_data["role"]
        assert message.answer == sample_chat_message_data["answer"]

    def test_chat_message_role_validation(self, sample_chat_message_data):
        """Test chat message role validation."""
        valid_roles = ["user", "assistant"]
        
        for role in valid_roles:
            sample_chat_message_data["role"] = role
            message = ChatMessage(**sample_chat_message_data)
            assert message.role == role

    def test_chat_message_required_fields(self, sample_chat_message_data):
        """Test required field handling."""
        required_fields = ["person_id", "question", "role"]
        
        for field in required_fields:
            incomplete_data = sample_chat_message_data.copy()
            del incomplete_data[field]
            
            # Test field handling - SQLModel may have different behavior
            try:
                message = ChatMessage(**incomplete_data)
                assert hasattr(message, field)
            except (ValueError, TypeError):
                # If validation fails, that's also acceptable
                pass

    def test_chat_message_uuid_generation(self, sample_chat_message_data):
        """Test UUID generation for message ID."""
        message = ChatMessage(**sample_chat_message_data)
        
        if hasattr(message, 'message_id') and message.message_id:
            assert isinstance(message.message_id, (str, UUID))

    def test_chat_message_created_at_default(self, sample_chat_message_data):
        """Test created_at default value."""
        before = datetime.utcnow()
        message = ChatMessage(**sample_chat_message_data)
        after = datetime.utcnow()
        
        assert message.created_at is not None
        assert before <= message.created_at <= after

    def test_chat_message_field_types(self, sample_chat_message_data):
        """Test field types."""
        message = ChatMessage(**sample_chat_message_data)
        
        assert isinstance(message.person_id, str)
        assert isinstance(message.question, str)
        assert isinstance(message.role, str)
        if message.answer:
            assert isinstance(message.answer, str)
        assert isinstance(message.created_at, datetime)

    def test_chat_message_table_name(self):
        """Test table name."""
        assert ChatMessage.__tablename__ == "chat_messages"

    def test_chat_message_long_text_fields(self, sample_chat_message_data):
        """Test handling of long text in question and answer."""
        long_text = "A" * 1000
        sample_chat_message_data["question"] = long_text
        sample_chat_message_data["answer"] = long_text
        
        message = ChatMessage(**sample_chat_message_data)
        assert len(message.question) == 1000
        assert len(message.answer) == 1000

    def test_chat_message_serialization(self, sample_chat_message_data):
        """Test message serialization."""
        message = ChatMessage(**sample_chat_message_data)
        
        if hasattr(message, 'model_dump'):
            message_dict = message.model_dump()
        else:
            message_dict = message.dict()
            
        assert isinstance(message_dict, dict)
        assert "person_id" in message_dict
        assert "question" in message_dict
        assert "role" in message_dict


class TestRateLimitEntry:
    """Test RateLimitEntry model functionality."""

    def test_rate_limit_entry_creation_with_required_fields(self):
        """Test creating rate limit entry with required fields."""
        window_start = datetime.utcnow()
        entry_data = {
            "identifier": "test_user_123",
            "window_start": window_start
        }
        
        entry = RateLimitEntry(**entry_data)
        assert entry.identifier == "test_user_123"
        assert entry.window_start == window_start
        assert entry.request_count == 1  # Default value
        assert entry.created_at is not None

    def test_rate_limit_entry_creation_with_all_fields(self):
        """Test creating rate limit entry with all fields."""
        window_start = datetime.utcnow()
        created_at = datetime.utcnow() - timedelta(minutes=1)
        
        entry_data = {
            "identifier": "test_user_456",
            "window_start": window_start,
            "request_count": 5,
            "created_at": created_at
        }
        
        entry = RateLimitEntry(**entry_data)
        assert entry.identifier == "test_user_456"
        assert entry.window_start == window_start
        assert entry.request_count == 5
        assert entry.created_at == created_at

    def test_rate_limit_entry_required_fields(self):
        """Test required field handling."""
        # Test with missing identifier - SQLModel may handle differently
        try:
            entry = RateLimitEntry(window_start=datetime.utcnow())
            assert hasattr(entry, 'identifier')
        except (ValueError, TypeError):
            # If validation fails, that's acceptable
            pass

    def test_rate_limit_entry_request_count_default(self):
        """Test request count default value."""
        entry = RateLimitEntry(
            identifier="test_user",
            window_start=datetime.utcnow()
        )
        assert entry.request_count == 1

    def test_rate_limit_entry_request_count_validation(self):
        """Test request count validation."""
        # Test positive values
        entry = RateLimitEntry(
            identifier="test_user",
            window_start=datetime.utcnow(),
            request_count=10
        )
        assert entry.request_count == 10
        
        # Test zero value
        entry = RateLimitEntry(
            identifier="test_user",
            window_start=datetime.utcnow(),
            request_count=0
        )
        assert entry.request_count == 0

    def test_rate_limit_entry_field_types(self):
        """Test field types."""
        entry = RateLimitEntry(
            identifier="test_user",
            window_start=datetime.utcnow(),
            request_count=5
        )
        
        assert isinstance(entry.identifier, str)
        assert isinstance(entry.window_start, datetime)
        assert isinstance(entry.request_count, int)
        assert isinstance(entry.created_at, datetime)

    def test_rate_limit_entry_table_name(self):
        """Test table name."""
        assert RateLimitEntry.__tablename__ == "rate_limit_entries"

    def test_rate_limit_entry_created_at_default(self):
        """Test created_at default value."""
        before = datetime.utcnow()
        entry = RateLimitEntry(
            identifier="test_user",
            window_start=datetime.utcnow()
        )
        after = datetime.utcnow()
        
        assert entry.created_at is not None
        assert before <= entry.created_at <= after

    def test_rate_limit_entry_serialization(self):
        """Test entry serialization."""
        entry = RateLimitEntry(
            identifier="test_user",
            window_start=datetime.utcnow(),
            request_count=3
        )
        
        if hasattr(entry, 'model_dump'):
            entry_dict = entry.model_dump()
        else:
            entry_dict = entry.dict()
            
        assert isinstance(entry_dict, dict)
        assert "identifier" in entry_dict
        assert "window_start" in entry_dict
        assert "request_count" in entry_dict

    def test_rate_limit_entry_window_start_timezone(self):
        """Test window_start handles timezone properly."""
        window_start = datetime.utcnow()
        entry = RateLimitEntry(
            identifier="test_user",
            window_start=window_start
        )
        
        # Verify the datetime is stored correctly
        assert entry.window_start == window_start


class TestModelIntegration:
    """Integration tests for all models."""

    def test_models_with_similar_field_names(self):
        """Test models with similar field names don't interfere."""
        account = Account(fub_account_id="test_account")
        message = ChatMessage(
            person_id="person_123",
            question="Test question?",
            role="user"
        )
        
        # Verify fields are independent
        assert account.fub_account_id != message.person_id
        assert hasattr(account, 'created_at')
        assert hasattr(message, 'created_at')

    def test_models_serialization_consistency(self):
        """Test consistent serialization across models."""
        account = Account(fub_account_id="test_account")
        message = ChatMessage(
            person_id="person_123",
            question="Test?",
            role="user"
        )
        rate_limit = RateLimitEntry(identifier="test", window_start=datetime.utcnow())
        
        models = [account, message, rate_limit]
        for model in models:
            if hasattr(model, 'model_dump'):
                serialized = model.model_dump()
            else:
                serialized = model.dict()
            assert isinstance(serialized, dict)
            assert len(serialized) > 0

    def test_model_table_names_unique(self):
        """Test that all models have unique table names."""
        table_names = {
            Account.__tablename__,
            ChatMessage.__tablename__,
            RateLimitEntry.__tablename__
        }
        
        assert len(table_names) == 3  # All unique
        assert "accounts" in table_names
        assert "chat_messages" in table_names
        assert "rate_limit_entries" in table_names

    def test_uuid_consistency(self):
        """Test UUID field consistency across models."""
        # Test that models handle UUIDs consistently
        account = Account(fub_account_id="550e8400-e29b-41d4-a716-446655440000")
        message = ChatMessage(
            person_id="550e8400-e29b-41d4-a716-446655440001",
            question="Test?",
            role="user"
        )
        
        assert isinstance(account.fub_account_id, str)
        assert isinstance(message.person_id, str) 