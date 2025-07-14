"""
Unit tests for utility functions.

Tests all utility functions including rate limiting, caching, data formatting,
and database operations.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from typing import Optional

from utils import (
    get_redis_client,
    check_rate_limit,
    get_cached_lead_data,
    cache_lead_data,
    format_chat_response,
    summarize_lead_activities,
    get_account_by_fub_id,
    create_or_update_account
)
from models import Account


class TestRedisClient:
    """Test Redis client management."""
    
    @pytest.mark.asyncio
    async def test_get_redis_client_creates_new_instance(self):
        """Test that get_redis_client creates a new Redis instance."""
        with patch('utils.redis.from_url') as mock_from_url:
            test_redis_client = Mock()
            mock_from_url.return_value = test_redis_client
            
            # Reset global client to None
            import utils
            utils.test_redis_client = None
            
            result = await get_redis_client()
            
            assert result == test_redis_client
            mock_from_url.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_redis_client_reuses_existing_instance(self):
        """Test that get_redis_client reuses existing Redis instance."""
        with patch('utils.redis.from_url') as mock_from_url:
            test_redis_client = Mock()
            
            # Set global client
            import utils
            utils.test_redis_client = test_redis_client
            
            result = await get_redis_client()
            
            assert result == test_redis_client
            mock_from_url.assert_not_called()


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_within_limit(self, test_redis_client):
        """Test rate limit check when within limit."""
        # Configure the mock pipeline
        test_redis_client.pipeline.return_value.execute.return_value = [None, 5, None, None]  # 5 current requests
        
        with patch('utils.get_redis_client', return_value=test_redis_client):
            result = await check_rate_limit("test_key", max_requests=10, window_minutes=1)
            
            assert result is True
            test_redis_client.pipeline.assert_called()
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_exceeds_limit(self, test_redis_client):
        """Test rate limit check when exceeding limit."""
        # Mock Redis pipeline
        mock_pipeline = Mock()
        mock_pipeline.execute = AsyncMock(return_value=[None, 15, None, None])  # 15 current requests
        test_redis_client.pipeline.return_value = mock_pipeline
        
        with patch('utils.get_redis_client', return_value=test_redis_client):
            result = await check_rate_limit("test_key", max_requests=10, window_minutes=1)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_redis_error_fails_open(self, test_redis_client):
        """Test that Redis errors cause rate limiting to fail open."""
        test_redis_client.pipeline.side_effect = Exception("Redis connection error")
        
        with patch('utils.get_redis_client', return_value=test_redis_client):
            result = await check_rate_limit("test_key", max_requests=10, window_minutes=1)
            
            assert result is True  # Fails open on error
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_pipeline_operations(self, test_redis_client):
        """Test that rate limiting calls correct Redis operations."""
        mock_pipeline = Mock()
        mock_pipeline.execute = AsyncMock(return_value=[None, 3, None, None])
        test_redis_client.pipeline.return_value = mock_pipeline
        
        with patch('utils.get_redis_client', return_value=test_redis_client):
            await check_rate_limit("test_key", max_requests=10, window_minutes=5)
            
            # Verify pipeline operations were called
            mock_pipeline.zremrangebyscore.assert_called_once()
            mock_pipeline.zcard.assert_called_once()
            mock_pipeline.zadd.assert_called_once()
            mock_pipeline.expire.assert_called_once()


class TestCaching:
    """Test data caching functionality."""
    
    @pytest.mark.asyncio
    async def test_get_cached_lead_data_exists(self, test_redis_client):
        """Test getting cached lead data when it exists."""
        test_data = {"id": "123", "name": "John Doe", "email": "john@example.com"}
        test_redis_client.get = AsyncMock(return_value=json.dumps(test_data))
        
        with patch('utils.get_redis_client', return_value=test_redis_client):
            result = await get_cached_lead_data("123")
            
            assert result == test_data
            test_redis_client.get.assert_called_once_with("lead_data:123")
    
    @pytest.mark.asyncio
    async def test_get_cached_lead_data_not_exists(self, test_redis_client):
        """Test getting cached lead data when it doesn't exist."""
        test_redis_client.get = AsyncMock(return_value=None)
        
        with patch('utils.get_redis_client', return_value=test_redis_client):
            result = await get_cached_lead_data("123")
            
            assert result is None
            test_redis_client.get.assert_called_once_with("lead_data:123")
    
    @pytest.mark.asyncio
    async def test_get_cached_lead_data_redis_error(self, test_redis_client):
        """Test getting cached data handles Redis errors gracefully."""
        test_redis_client.get = AsyncMock(side_effect=Exception("Redis error"))
        
        with patch('utils.get_redis_client', return_value=test_redis_client):
            result = await get_cached_lead_data("123")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_lead_data_success(self, test_redis_client):
        """Test caching lead data successfully."""
        test_data = {"id": "123", "name": "John Doe"}
        test_redis_client.setex = AsyncMock()
        
        with patch('utils.get_redis_client', return_value=test_redis_client):
            await cache_lead_data("123", test_data, ttl_seconds=120)
            
            test_redis_client.setex.assert_called_once_with(
                "lead_data:123",
                120,
                json.dumps(test_data, default=str)
            )
    
    @pytest.mark.asyncio
    async def test_cache_lead_data_default_ttl(self, test_redis_client):
        """Test caching lead data with default TTL."""
        test_data = {"id": "123"}
        test_redis_client.setex = AsyncMock()
        
        with patch('utils.get_redis_client', return_value=test_redis_client):
            await cache_lead_data("123", test_data)
            
            test_redis_client.setex.assert_called_once_with(
                "lead_data:123",
                90,  # Default TTL
                json.dumps(test_data, default=str)
            )
    
    @pytest.mark.asyncio
    async def test_cache_lead_data_redis_error(self, test_redis_client):
        """Test caching data handles Redis errors gracefully."""
        test_redis_client.setex = AsyncMock(side_effect=Exception("Redis error"))
        
        with patch('utils.get_redis_client', return_value=test_redis_client):
            # Should not raise exception
            await cache_lead_data("123", {"data": "test"})


class TestFormatChatResponse:
    """Test chat response formatting."""
    
    def test_format_chat_response_basic(self):
        """Test basic chat response formatting."""
        response = "Call the lead\nSend follow-up email\nSchedule showing"
        result = format_chat_response(response)
        
        expected = "• Call the lead\n• Send follow-up email\n• Schedule showing"
        assert result == expected
    
    def test_format_chat_response_with_existing_bullets(self):
        """Test formatting when bullets already exist."""
        response = "• Call the lead\n- Send follow-up email\nSchedule showing"
        result = format_chat_response(response)
        
        expected = "• Call the lead\n- Send follow-up email\n• Schedule showing"
        assert result == expected
    
    def test_format_chat_response_more_than_three_lines(self):
        """Test formatting limits to 3 lines."""
        response = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"
        result = format_chat_response(response)
        
        lines = result.split('\n')
        assert len(lines) == 3
        assert "• Line 1" in result
        assert "• Line 2" in result
        assert "• Line 3" in result
        assert "Line 4" not in result
    
    def test_format_chat_response_empty_lines_filtered(self):
        """Test that empty lines are filtered out."""
        response = "Line 1\n\n\nLine 2\n\nLine 3\n\n"
        result = format_chat_response(response)
        
        lines = result.split('\n')
        assert len(lines) == 3
        assert all(line.strip() for line in lines)
    
    def test_format_chat_response_truncate_long_text(self):
        """Test that responses longer than 400 chars are truncated."""
        long_line = "This is a very long line that will make the total response exceed 400 characters when combined with other lines. " * 5
        response = f"{long_line}\nSecond line\nThird line"
        result = format_chat_response(response)
        
        assert len(result) <= 400
        assert result.endswith("...")
    
    def test_format_chat_response_exactly_400_chars(self):
        """Test response that's exactly 400 characters."""
        # Create a response that's exactly 400 chars
        line1 = "• " + "A" * 130  # 132 chars
        line2 = "• " + "B" * 130  # 132 chars  
        line3 = "• " + "C" * 132  # 134 chars
        response = f"{line1[2:]}\n{line2[2:]}\n{line3[2:]}"  # Remove bullets since they'll be added
        
        result = format_chat_response(response)
        assert len(result) <= 400
    
    def test_format_chat_response_empty_input(self):
        """Test formatting empty input."""
        result = format_chat_response("")
        assert result == ""
    
    def test_format_chat_response_only_whitespace(self):
        """Test formatting input with only whitespace."""
        result = format_chat_response("   \n  \n   ")
        assert result == ""


class TestSummarizeLeadActivities:
    """Test lead activity summarization."""
    
    def test_summarize_lead_activities_empty_list(self):
        """Test summarizing empty activities list."""
        result = summarize_lead_activities([])
        assert result == "No recent activities found."
    
    def test_summarize_lead_activities_mixed_types(self):
        """Test summarizing activities with mixed types."""
        activities = [
            {"type": "call", "created": "2023-01-01"},
            {"type": "email", "created": "2023-01-02"},
            {"type": "text", "created": "2023-01-03"},
            {"type": "note", "created": "2023-01-04"},
            {"type": "call", "created": "2023-01-05"}
        ]
        
        result = summarize_lead_activities(activities)
        
        assert "2 calls" in result
        assert "1 emails" in result
        assert "1 texts" in result
        assert "1 notes" in result
        assert "latest: 2023-01-05" in result  # Latest call
    
    def test_summarize_lead_activities_only_calls(self):
        """Test summarizing activities with only calls."""
        activities = [
            {"type": "call", "created": "2023-01-01"},
            {"type": "call", "created": "2023-01-02"}
        ]
        
        result = summarize_lead_activities(activities)
        
        assert "2 calls" in result
        assert "latest: 2023-01-02" in result
        assert "emails" not in result
        assert "texts" not in result
    
    def test_summarize_lead_activities_last_five_only(self):
        """Test that only last 5 activities are considered."""
        activities = []
        for i in range(10):
            activities.append({"type": "call", "created": f"2023-01-{i+1:02d}"})
        
        result = summarize_lead_activities(activities)
        
        # Should only count the last 5
        assert "5 calls" in result
        assert "latest: 2023-01-10" in result
    
    def test_summarize_lead_activities_case_insensitive_types(self):
        """Test that activity type matching is case insensitive."""
        activities = [
            {"type": "CALL", "created": "2023-01-01"},
            {"type": "Email", "created": "2023-01-02"},
            {"type": "SMS", "created": "2023-01-03"},
            {"type": "TEXT_MESSAGE", "created": "2023-01-04"}
        ]
        
        result = summarize_lead_activities(activities)
        
        assert "1 calls" in result
        assert "1 emails" in result
        assert "2 texts" in result  # SMS and TEXT_MESSAGE
    
    def test_summarize_lead_activities_missing_fields(self):
        """Test handling activities with missing fields."""
        activities = [
            {"type": "call"},  # Missing created
            {"created": "2023-01-02"},  # Missing type
            {}  # Empty activity
        ]
        
        result = summarize_lead_activities(activities)
        
        # Should handle gracefully
        assert isinstance(result, str)
    
    def test_summarize_lead_activities_no_matching_types(self):
        """Test activities with no matching types."""
        activities = [
            {"type": "unknown_type", "created": "2023-01-01"},
            {"type": "meeting", "created": "2023-01-02"}
        ]
        
        result = summarize_lead_activities(activities)
        
        assert result == "No recent activities found."


class TestDatabaseOperations:
    """Test database operation utilities."""
    
    def test_get_account_by_fub_id_exists(self, db_transaction, test_account):
        """Test getting account by FUB ID when it exists."""
        # test_account fixture should create an account in the test database
        result = get_account_by_fub_id(db_transaction, test_account["fub_account_id"])
        
        assert result is not None
        assert result.fub_account_id == test_account["fub_account_id"]
    
    def test_get_account_by_fub_id_not_exists(self, db_transaction):
        """Test getting account by FUB ID when it doesn't exist."""
        result = get_account_by_fub_id(db_transaction, "nonexistent_id")
        
        assert result is None
    
    def test_create_or_update_account_new_account(self, db_transaction):
        """Test creating a new account."""
        fub_account_id = "new_test_account"
        
        with patch('utils.get_account_by_fub_id', return_value=None):
            # Mock session operations
            mock_session = Mock()
            mock_session.add = Mock()
            mock_session.commit = Mock()
            mock_session.refresh = Mock()
            
            # Create account
            account = Account(fub_account_id=fub_account_id)
            
            with patch('utils.Account', return_value=account):
                result = create_or_update_account(
                    mock_session,
                    fub_account_id,
                    stripe_customer_id="cus_123"
                )
                
                mock_session.add.assert_called_once()
                mock_session.commit.assert_called_once()
                mock_session.refresh.assert_called_once()
                assert result == account
    
    def test_create_or_update_account_update_existing(self, db_transaction, test_account):
        """Test updating an existing account."""
        # Create a mock existing account
        existing_account = Account(
            fub_account_id=test_account["fub_account_id"],
            stripe_customer_id="old_customer_id"
        )
        
        mock_session = Mock()
        mock_session.commit = Mock()
        mock_session.refresh = Mock()
        
        with patch('utils.get_account_by_fub_id', return_value=existing_account):
            result = create_or_update_account(
                mock_session,
                test_account["fub_account_id"],
                stripe_customer_id="new_customer_id"
            )
            
            assert result.stripe_customer_id == "new_customer_id"
            assert isinstance(result.updated_at, datetime)
            mock_session.commit.assert_called_once()
            mock_session.refresh.assert_called_once()
    
    def test_create_or_update_account_invalid_field(self, db_transaction):
        """Test that invalid fields are ignored when updating."""
        existing_account = Account(fub_account_id="test_id")
        
        mock_session = Mock()
        mock_session.commit = Mock()
        mock_session.refresh = Mock()
        
        with patch('utils.get_account_by_fub_id', return_value=existing_account):
            # Try to set a field that doesn't exist
            result = create_or_update_account(
                mock_session,
                "test_id",
                invalid_field="should_be_ignored",
                stripe_customer_id="valid_field"
            )
            
            # Should not have invalid_field but should have valid field
            assert not hasattr(result, 'invalid_field')
            assert result.stripe_customer_id == "valid_field"


class TestUtilsIntegration:
    """Integration tests for utilities."""
    
    @pytest.mark.asyncio
    async def test_rate_limit_and_cache_integration(self, test_redis_client):
        """Test that rate limiting and caching work together."""
        # Setup mock Redis for both rate limiting and caching
        mock_pipeline = Mock()
        mock_pipeline.execute = AsyncMock(return_value=[None, 3, None, None])
        test_redis_client.pipeline.return_value = mock_pipeline
        test_redis_client.get = AsyncMock(return_value=None)
        test_redis_client.setex = AsyncMock()
        
        with patch('utils.get_redis_client', return_value=test_redis_client):
            # Test rate limiting
            rate_limit_ok = await check_rate_limit("test_key", 10)
            assert rate_limit_ok is True
            
            # Test caching
            test_data = {"id": "123", "name": "Test"}
            await cache_lead_data("123", test_data)
            cached_data = await get_cached_lead_data("123")
            
            # Should have called Redis operations
            test_redis_client.setex.assert_called_once()
            test_redis_client.get.assert_called_once()
    
    def test_format_and_summarize_integration(self):
        """Test that formatting and summarizing work together."""
        # Create activities that would generate a long response
        activities = [
            {"type": "call", "created": "2023-01-01"},
            {"type": "email", "created": "2023-01-02"},
            {"type": "text", "created": "2023-01-03"}
        ]
        
        summary = summarize_lead_activities(activities)
        formatted = format_chat_response(f"Based on activities: {summary}\nRecommendation 1\nRecommendation 2")
        
        # Should be properly formatted with bullets and within limits
        assert formatted.startswith("•")
        assert len(formatted) <= 400
        lines = formatted.split('\n')
        assert len(lines) <= 3 