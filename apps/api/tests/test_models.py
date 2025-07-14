"""
Unit tests for database models.

Tests all SQLModel classes for proper validation, defaults, and constraints.
"""

import pytest
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from typing import Dict, Any

from models import Account, ChatMessage, RateLimitEntry, SubscriptionStatus


class TestSubscriptionStatus:
    """Test the SubscriptionStatus enum."""
    
    def test_subscription_status_values(self):
        """Test that all subscription status values are correctly defined."""
        assert SubscriptionStatus.ACTIVE == "active"
        assert SubscriptionStatus.CANCELLED == "cancelled"
        assert SubscriptionStatus.INCOMPLETE == "incomplete"
        assert SubscriptionStatus.PAST_DUE == "past_due"
        assert SubscriptionStatus.TRIALING == "trialing"
        assert SubscriptionStatus.UNPAID == "unpaid"
    
    def test_subscription_status_membership(self):
        """Test subscription status membership checks."""
        assert "active" in SubscriptionStatus
        assert "invalid_status" not in SubscriptionStatus
    
    def test_subscription_status_iteration(self):
        """Test iteration over subscription statuses."""
        statuses = list(SubscriptionStatus)
        expected = ["active", "cancelled", "incomplete", "past_due", "trialing", "unpaid"]
        assert len(statuses) == len(expected)
        for status in expected:
            assert status in [s.value for s in statuses]


class TestAccount:
    """Test the Account model."""
    
    def test_account_creation_with_required_fields(self, sample_account_data):
        """Test creating an account with only required fields."""
        # Only provide required fields
        required_data = {
            "fub_account_id": sample_account_data["fub_account_id"]
        }
        
        account = Account(**required_data)
        
        assert account.fub_account_id == required_data["fub_account_id"]
        assert account.subscription_status == SubscriptionStatus.TRIALING  # Default
        assert account.fub_access_token is None
        assert account.fub_refresh_token is None
        assert account.stripe_customer_id is None
        assert account.account_id is None  # Not set until DB insert
        assert isinstance(account.created_at, datetime)
    
    def test_account_creation_with_all_fields(self, sample_account_data):
        """Test creating an account with all fields."""
        account = Account(**sample_account_data)
        
        assert account.fub_account_id == sample_account_data["fub_account_id"]
        assert account.fub_access_token == sample_account_data["fub_access_token"]
        assert account.fub_refresh_token == sample_account_data["fub_refresh_token"]
        assert account.stripe_customer_id == sample_account_data["stripe_customer_id"]
        assert account.subscription_status == sample_account_data["subscription_status"]
        assert isinstance(account.created_at, datetime)
    
    def test_account_subscription_status_validation(self, sample_account_data):
        """Test that subscription status accepts valid enum values."""
        for status in SubscriptionStatus:
            sample_account_data["subscription_status"] = status
            account = Account(**sample_account_data)
            assert account.subscription_status == status
    
    def test_account_subscription_status_invalid(self, sample_account_data):
        """Test that invalid subscription status raises validation error."""
        sample_account_data["subscription_status"] = "invalid_status"
        
        with pytest.raises(ValueError, match="Input should be"):
            Account(**sample_account_data)
    
    def test_account_fub_account_id_required(self, sample_account_data):
        """Test that fub_account_id is required."""
        del sample_account_data["fub_account_id"]
        
        with pytest.raises(ValueError, match="Field required"):
            Account(**sample_account_data)
    
    def test_account_created_at_default(self, sample_account_data):
        """Test that created_at gets a default timestamp."""
        before = datetime.utcnow()
        account = Account(fub_account_id=sample_account_data["fub_account_id"])
        after = datetime.utcnow()
        
        assert before <= account.created_at <= after
    
    def test_account_field_types(self, sample_account_data):
        """Test field type validation."""
        account = Account(**sample_account_data)
        
        assert isinstance(account.fub_account_id, str)
        assert isinstance(account.subscription_status, SubscriptionStatus)
        assert account.fub_access_token is None or isinstance(account.fub_access_token, str)
        assert account.fub_refresh_token is None or isinstance(account.fub_refresh_token, str)
        assert account.stripe_customer_id is None or isinstance(account.stripe_customer_id, str)
        assert isinstance(account.created_at, datetime)
    
    def test_account_table_name(self):
        """Test that table name is set correctly."""
        assert Account.__tablename__ == "accounts"
    
    def test_account_serialization(self, sample_account_data):
        """Test account serialization to dict."""
        account = Account(**sample_account_data)
        account_dict = account.model_dump()
        
        assert account_dict["fub_account_id"] == sample_account_data["fub_account_id"]
        assert account_dict["subscription_status"] == sample_account_data["subscription_status"]
        assert "created_at" in account_dict
    
    def test_account_repr(self, sample_account_data):
        """Test account string representation."""
        account = Account(**sample_account_data)
        repr_str = repr(account)
        
        assert "Account" in repr_str
        assert sample_account_data["fub_account_id"] in repr_str


class TestChatMessage:
    """Test the ChatMessage model."""
    
    def test_chat_message_creation_with_required_fields(self, sample_chat_message_data):
        """Test creating a chat message with only required fields."""
        required_data = {
            "person_id": sample_chat_message_data["person_id"],
            "question": sample_chat_message_data["question"],
            "role": sample_chat_message_data["role"]
        }
        
        message = ChatMessage(**required_data)
        
        assert message.person_id == required_data["person_id"]
        assert message.question == required_data["question"]
        assert message.role == required_data["role"]
        assert message.answer is None
        assert isinstance(message.created_at, datetime)
        assert isinstance(message.id, UUID)
    
    def test_chat_message_creation_with_all_fields(self, sample_chat_message_data):
        """Test creating a chat message with all fields."""
        message = ChatMessage(**sample_chat_message_data)
        
        assert message.person_id == sample_chat_message_data["person_id"]
        assert message.question == sample_chat_message_data["question"]
        assert message.answer == sample_chat_message_data["answer"]
        assert message.role == sample_chat_message_data["role"]
        assert isinstance(message.created_at, datetime)
        assert isinstance(message.id, UUID)
    
    def test_chat_message_role_validation(self, sample_chat_message_data):
        """Test role field validation."""
        valid_roles = ["user", "assistant"]
        
        for role in valid_roles:
            sample_chat_message_data["role"] = role
            message = ChatMessage(**sample_chat_message_data)
            assert message.role == role
    
    def test_chat_message_required_fields(self, sample_chat_message_data):
        """Test that required fields must be provided."""
        required_fields = ["person_id", "question", "role"]
        
        for field in required_fields:
            incomplete_data = sample_chat_message_data.copy()
            del incomplete_data[field]
            
            with pytest.raises(ValueError, match="Field required"):
                ChatMessage(**incomplete_data)
    
    def test_chat_message_uuid_generation(self, sample_chat_message_data):
        """Test that UUID is automatically generated."""
        message1 = ChatMessage(**sample_chat_message_data)
        message2 = ChatMessage(**sample_chat_message_data)
        
        assert isinstance(message1.id, UUID)
        assert isinstance(message2.id, UUID)
        assert message1.id != message2.id  # Should be unique
    
    def test_chat_message_created_at_default(self, sample_chat_message_data):
        """Test that created_at gets a default timestamp."""
        before = datetime.utcnow()
        message = ChatMessage(**sample_chat_message_data)
        after = datetime.utcnow()
        
        assert before <= message.created_at <= after
    
    def test_chat_message_field_types(self, sample_chat_message_data):
        """Test field type validation."""
        message = ChatMessage(**sample_chat_message_data)
        
        assert isinstance(message.person_id, str)
        assert isinstance(message.question, str)
        assert isinstance(message.role, str)
        assert message.answer is None or isinstance(message.answer, str)
        assert isinstance(message.created_at, datetime)
        assert isinstance(message.id, UUID)
    
    def test_chat_message_table_name(self):
        """Test that table name is set correctly."""
        assert ChatMessage.__tablename__ == "chat_messages"
    
    def test_chat_message_long_text_fields(self, sample_chat_message_data):
        """Test that long text fields are handled properly."""
        long_text = "A" * 10000  # Very long text
        
        sample_chat_message_data["question"] = long_text
        sample_chat_message_data["answer"] = long_text
        
        message = ChatMessage(**sample_chat_message_data)
        
        assert message.question == long_text
        assert message.answer == long_text
    
    def test_chat_message_serialization(self, sample_chat_message_data):
        """Test chat message serialization to dict."""
        message = ChatMessage(**sample_chat_message_data)
        message_dict = message.model_dump()
        
        assert message_dict["person_id"] == sample_chat_message_data["person_id"]
        assert message_dict["question"] == sample_chat_message_data["question"]
        assert message_dict["role"] == sample_chat_message_data["role"]
        assert "created_at" in message_dict
        assert "id" in message_dict


class TestRateLimitEntry:
    """Test the RateLimitEntry model."""
    
    def test_rate_limit_entry_creation_with_required_fields(self):
        """Test creating a rate limit entry with only required fields."""
        identifier = "test_identifier"
        window_start = datetime.utcnow()
        
        entry = RateLimitEntry(
            identifier=identifier,
            window_start=window_start
        )
        
        assert entry.identifier == identifier
        assert entry.window_start == window_start
        assert entry.request_count == 1  # Default value
        assert isinstance(entry.created_at, datetime)
        assert entry.id is None  # Not set until DB insert
    
    def test_rate_limit_entry_creation_with_all_fields(self):
        """Test creating a rate limit entry with all fields."""
        identifier = "test_identifier"
        window_start = datetime.utcnow()
        request_count = 5
        created_at = datetime.utcnow() - timedelta(minutes=1)
        
        entry = RateLimitEntry(
            identifier=identifier,
            window_start=window_start,
            request_count=request_count,
            created_at=created_at
        )
        
        assert entry.identifier == identifier
        assert entry.window_start == window_start
        assert entry.request_count == request_count
        assert entry.created_at == created_at
    
    def test_rate_limit_entry_required_fields(self):
        """Test that required fields must be provided."""
        # Missing identifier
        with pytest.raises(ValueError, match="Field required"):
            RateLimitEntry(window_start=datetime.utcnow())
        
        # Missing window_start
        with pytest.raises(ValueError, match="Field required"):
            RateLimitEntry(identifier="test")
    
    def test_rate_limit_entry_request_count_default(self):
        """Test that request_count defaults to 1."""
        entry = RateLimitEntry(
            identifier="test",
            window_start=datetime.utcnow()
        )
        
        assert entry.request_count == 1
    
    def test_rate_limit_entry_request_count_validation(self):
        """Test request count validation."""
        # Positive count should work
        entry = RateLimitEntry(
            identifier="test",
            window_start=datetime.utcnow(),
            request_count=10
        )
        assert entry.request_count == 10
        
        # Zero count should work
        entry = RateLimitEntry(
            identifier="test", 
            window_start=datetime.utcnow(),
            request_count=0
        )
        assert entry.request_count == 0
    
    def test_rate_limit_entry_field_types(self):
        """Test field type validation."""
        entry = RateLimitEntry(
            identifier="test_identifier",
            window_start=datetime.utcnow(),
            request_count=5
        )
        
        assert isinstance(entry.identifier, str)
        assert isinstance(entry.window_start, datetime)
        assert isinstance(entry.request_count, int)
        assert isinstance(entry.created_at, datetime)
    
    def test_rate_limit_entry_table_name(self):
        """Test that table name is set correctly."""
        assert RateLimitEntry.__tablename__ == "rate_limit_entries"
    
    def test_rate_limit_entry_created_at_default(self):
        """Test that created_at gets a default timestamp."""
        before = datetime.utcnow()
        entry = RateLimitEntry(
            identifier="test",
            window_start=datetime.utcnow()
        )
        after = datetime.utcnow()
        
        assert before <= entry.created_at <= after
    
    def test_rate_limit_entry_serialization(self):
        """Test rate limit entry serialization to dict."""
        entry = RateLimitEntry(
            identifier="test_identifier",
            window_start=datetime.utcnow(),
            request_count=5
        )
        entry_dict = entry.model_dump()
        
        assert entry_dict["identifier"] == "test_identifier"
        assert entry_dict["request_count"] == 5
        assert "window_start" in entry_dict
        assert "created_at" in entry_dict
    
    def test_rate_limit_entry_window_start_timezone(self):
        """Test that window_start handles timezone-aware datetimes."""
        from datetime import timezone
        
        tz_aware_time = datetime.now(timezone.utc)
        entry = RateLimitEntry(
            identifier="test",
            window_start=tz_aware_time
        )
        
        assert entry.window_start == tz_aware_time


# Integration tests for model relationships and edge cases
class TestModelIntegration:
    """Integration tests for models."""
    
    def test_models_with_similar_field_names(self, sample_account_data, sample_chat_message_data):
        """Test that models with similar field names don't interfere."""
        account = Account(**sample_account_data)
        message = ChatMessage(**sample_chat_message_data)
        
        # Both have created_at fields
        assert hasattr(account, 'created_at')
        assert hasattr(message, 'created_at')
        assert account.created_at != message.created_at  # Different instances
    
    def test_models_serialization_consistency(self, sample_account_data, sample_chat_message_data):
        """Test that all models can be serialized consistently."""
        account = Account(**sample_account_data)
        message = ChatMessage(**sample_chat_message_data)
        rate_limit = RateLimitEntry(identifier="test", window_start=datetime.utcnow())
        
        # All should be serializable to dict
        account_dict = account.model_dump()
        message_dict = message.model_dump()
        rate_limit_dict = rate_limit.model_dump()
        
        assert isinstance(account_dict, dict)
        assert isinstance(message_dict, dict)
        assert isinstance(rate_limit_dict, dict)
        
        # All should have created_at fields
        assert "created_at" in account_dict
        assert "created_at" in message_dict
        assert "created_at" in rate_limit_dict
    
    def test_model_table_names_unique(self):
        """Test that all model table names are unique."""
        table_names = [
            Account.__tablename__,
            ChatMessage.__tablename__,
            RateLimitEntry.__tablename__
        ]
        
        assert len(table_names) == len(set(table_names))  # All unique
    
    def test_uuid_consistency(self, sample_chat_message_data):
        """Test UUID field consistency across message instances."""
        # Create multiple messages
        messages = [ChatMessage(**sample_chat_message_data) for _ in range(5)]
        
        # All should have unique UUIDs
        uuids = [msg.id for msg in messages]
        assert len(uuids) == len(set(uuids))
        
        # All should be valid UUID objects
        for uuid_val in uuids:
            assert isinstance(uuid_val, UUID)
            # Test that it can be converted to string and back
            uuid_str = str(uuid_val)
            assert UUID(uuid_str) == uuid_val 