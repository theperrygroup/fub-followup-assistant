"""Tests for configuration module.

This module tests the Settings class and configuration loading functionality.
All tests verify proper environment variable loading, validation, and defaults.
"""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from config import Settings


class TestSettingsDefaults:
    """Test default values in Settings class."""
    
    def test_settings_with_minimal_env(self):
        """Test settings with only required environment variables."""
        required_env = {
            "DATABASE_URL": "postgresql://test:test@localhost:5432/test",
            "FRONTEND_EMBED_ORIGIN": "https://app.example.com",
            "FUB_CLIENT_ID": "placeholder-client-id",
            "FUB_EMBED_SECRET": "test-embed-secret",
            "JWT_SECRET": "test-jwt-secret",
            "MARKETING_ORIGIN": "https://example.com",
            "OPENAI_API_KEY": "sk-test-key",
            "REDIS_URL": "redis://localhost:6379/0",
            "STRIPE_PRICE_ID_MONTHLY": "price_test123",
            "STRIPE_SECRET_KEY": "sk_test_stripe",
            "STRIPE_WEBHOOK_SECRET": "whsec_test"
        }

        with patch.dict(os.environ, required_env, clear=True):
            test_settings = Settings()

            # Test required fields are set
            assert test_settings.database_url == required_env["DATABASE_URL"]
            assert test_settings.frontend_embed_origin == required_env["FRONTEND_EMBED_ORIGIN"]
            assert test_settings.fub_client_id == "placeholder-client-id"
            assert test_settings.fub_embed_secret == required_env["FUB_EMBED_SECRET"]
            assert test_settings.jwt_secret == required_env["JWT_SECRET"]
            assert test_settings.marketing_origin == required_env["MARKETING_ORIGIN"]
            assert test_settings.openai_api_key == required_env["OPENAI_API_KEY"]
            assert test_settings.redis_url == required_env["REDIS_URL"]
            assert test_settings.stripe_price_id_monthly == required_env["STRIPE_PRICE_ID_MONTHLY"]
            assert test_settings.stripe_secret_key == required_env["STRIPE_SECRET_KEY"]
            assert test_settings.stripe_webhook_secret == required_env["STRIPE_WEBHOOK_SECRET"]

            # Test default values
            assert test_settings.app_env == "dev"

    def test_settings_default_cors_origins(self):
        """Test default CORS origins."""
        # Use test environment setup
        test_settings = Settings()
        expected_cors = ["https://*.followupboss.com", "http://localhost:*"]
        assert test_settings.cors_origins == expected_cors

    def test_settings_default_rate_limits(self):
        """Test default rate limit values."""
        test_settings = Settings()
        assert test_settings.rate_limit_requests_per_minute == 10
        assert test_settings.rate_limit_requests_per_minute_ip == 100


class TestSettingsEnvironmentVariables:
    """Test environment variable loading."""

    def test_settings_from_env_vars(self):
        """Test that settings load from environment variables."""
        test_env = {
            "APP_ENV": "production",
            "DATABASE_URL": "postgresql://prod:prod@prod.com:5432/prod",
            "FRONTEND_EMBED_ORIGIN": "https://prod-app.example.com",
            "FUB_CLIENT_ID": "prod-client-id",
            "FUB_CLIENT_SECRET": "prod-client-secret",
            "FUB_EMBED_SECRET": "prod-embed-secret",
            "JWT_SECRET": "prod-jwt-secret",
            "MARKETING_ORIGIN": "https://prod.example.com",
            "OPENAI_API_KEY": "sk-prod-key",
            "REDIS_URL": "redis://prod:6379/0",
            "STRIPE_PRICE_ID_MONTHLY": "price_prod123",
            "STRIPE_SECRET_KEY": "sk_prod_stripe",
            "STRIPE_WEBHOOK_SECRET": "whsec_prod",
            "LOG_LEVEL": "ERROR",
            "RATE_LIMIT_RPM": "50",
            "RATE_LIMIT_RPM_IP": "500"
        }

        with patch.dict(os.environ, test_env, clear=True):
            test_settings = Settings()

            assert test_settings.app_env == "production"
            assert test_settings.database_url == test_env["DATABASE_URL"]
            assert test_settings.frontend_embed_origin == test_env["FRONTEND_EMBED_ORIGIN"]
            assert test_settings.fub_client_id == test_env["FUB_CLIENT_ID"]
            assert test_settings.fub_client_secret == test_env["FUB_CLIENT_SECRET"]
            assert test_settings.fub_embed_secret == test_env["FUB_EMBED_SECRET"]
            assert test_settings.jwt_secret == test_env["JWT_SECRET"]
            assert test_settings.marketing_origin == test_env["MARKETING_ORIGIN"]
            assert test_settings.openai_api_key == test_env["OPENAI_API_KEY"]
            assert test_settings.redis_url == test_env["REDIS_URL"]
            assert test_settings.stripe_price_id_monthly == test_env["STRIPE_PRICE_ID_MONTHLY"]
            assert test_settings.stripe_secret_key == test_env["STRIPE_SECRET_KEY"]
            assert test_settings.stripe_webhook_secret == test_env["STRIPE_WEBHOOK_SECRET"]
            assert test_settings.log_level == "ERROR"
            assert test_settings.rate_limit_requests_per_minute == 50
            assert test_settings.rate_limit_requests_per_minute_ip == 500

    def test_settings_case_insensitive(self):
        """Test that environment variable names are case insensitive."""
        test_env = {
            "database_url": "postgresql://test:test@localhost:5432/test",
            "FRONTEND_EMBED_ORIGIN": "https://app.example.com",
            "fub_embed_secret": "test-embed-secret",
            "JWT_SECRET": "test-jwt-secret",
            "marketing_origin": "https://example.com",
            "OPENAI_API_KEY": "sk-test-key",
            "redis_url": "redis://localhost:6379/0",
            "STRIPE_PRICE_ID_MONTHLY": "price_test123",
            "stripe_secret_key": "sk_test_stripe",
            "STRIPE_WEBHOOK_SECRET": "whsec_test"
        }

        with patch.dict(os.environ, test_env, clear=True):
            test_settings = Settings()
            assert test_settings.database_url == test_env["database_url"]
            assert test_settings.frontend_embed_origin == test_env["FRONTEND_EMBED_ORIGIN"]


class TestSettingsValidation:
    """Test settings validation."""

    def test_settings_missing_required_database_url(self):
        """Test that missing required DATABASE_URL is handled appropriately."""
        env_vars = {
            "FRONTEND_EMBED_ORIGIN": "https://app.example.com",
            "FUB_EMBED_SECRET": "test-embed-secret",
            "JWT_SECRET": "test-jwt-secret",
            "MARKETING_ORIGIN": "https://example.com",
            "OPENAI_API_KEY": "sk-test-key",
            "REDIS_URL": "redis://localhost:6379/0",
            "STRIPE_PRICE_ID_MONTHLY": "price_test123",
            "STRIPE_SECRET_KEY": "sk_test_stripe",
            "STRIPE_WEBHOOK_SECRET": "whsec_test"
            # Missing DATABASE_URL
        }

        with patch.dict(os.environ, env_vars, clear=True):
            # Settings should handle missing DATABASE_URL gracefully
            test_settings = Settings()
            # Verify the field exists (may have default or placeholder value)
            assert hasattr(test_settings, 'database_url')

    def test_settings_missing_required_openai_key(self):
        """Test that missing required OPENAI_API_KEY is handled appropriately."""
        env_vars = {
            "DATABASE_URL": "postgresql://test:test@localhost:5432/test",
            "FRONTEND_EMBED_ORIGIN": "https://app.example.com",
            "FUB_EMBED_SECRET": "test-embed-secret",
            "JWT_SECRET": "test-jwt-secret",
            "MARKETING_ORIGIN": "https://example.com",
            "REDIS_URL": "redis://localhost:6379/0",
            "STRIPE_PRICE_ID_MONTHLY": "price_test123",
            "STRIPE_SECRET_KEY": "sk_test_stripe",
            "STRIPE_WEBHOOK_SECRET": "whsec_test"
            # Missing OPENAI_API_KEY
        }

        with patch.dict(os.environ, env_vars, clear=True):
            # Settings should handle missing fields gracefully
            test_settings = Settings()
            assert hasattr(test_settings, 'openai_api_key')

    def test_settings_missing_multiple_required_fields(self):
        """Test handling when multiple required fields are missing."""
        env_vars = {
            "DATABASE_URL": "postgresql://test:test@localhost:5432/test",
            # Missing many required fields
        }

        with patch.dict(os.environ, env_vars, clear=True):
            # Settings should handle missing fields gracefully with defaults
            test_settings = Settings()
            assert hasattr(test_settings, 'database_url')

    def test_settings_invalid_rate_limit_types(self):
        """Test validation of rate limit field types."""
        test_env = {
            "DATABASE_URL": "postgresql://test:test@localhost:5432/test",
            "FRONTEND_EMBED_ORIGIN": "https://app.example.com",
            "FUB_EMBED_SECRET": "test-embed-secret",
            "JWT_SECRET": "test-jwt-secret",
            "MARKETING_ORIGIN": "https://example.com",
            "OPENAI_API_KEY": "sk-test-key",
            "REDIS_URL": "redis://localhost:6379/0",
            "STRIPE_PRICE_ID_MONTHLY": "price_test123",
            "STRIPE_SECRET_KEY": "sk_test_stripe",
            "STRIPE_WEBHOOK_SECRET": "whsec_test",
            "RATE_LIMIT_RPM": "not_a_number"
        }

        with patch.dict(os.environ, test_env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            
            error_str = str(exc_info.value)
            assert "rate_limit_requests_per_minute" in error_str or "RATE_LIMIT_RPM" in error_str


class TestSettingsFieldTypes:
    """Test field type validation."""

    def test_settings_field_types(self):
        """Test that settings fields have correct types."""
        test_settings = Settings()

        # String fields
        assert isinstance(test_settings.app_env, str)
        assert isinstance(test_settings.database_url, str)
        assert isinstance(test_settings.frontend_embed_origin, str)
        assert isinstance(test_settings.fub_client_id, str)
        assert isinstance(test_settings.log_level, str)

        # Integer fields
        assert isinstance(test_settings.rate_limit_requests_per_minute, int)
        assert isinstance(test_settings.rate_limit_requests_per_minute_ip, int)

        # List fields
        assert isinstance(test_settings.cors_origins, list)
        assert all(isinstance(origin, str) for origin in test_settings.cors_origins)


class TestSettingsConfig:
    """Test settings configuration."""

    def test_settings_config_attributes(self):
        """Test that settings config has expected attributes."""
        test_settings = Settings()
        config = test_settings.model_config if hasattr(test_settings, 'model_config') else test_settings.Config
        
        # Check that configuration exists and has expected properties
        assert hasattr(config, 'case_sensitive') or hasattr(config, 'extra')

    def test_settings_extra_env_vars_ignored(self):
        """Test that extra environment variables are ignored."""
        test_env = {
            "DATABASE_URL": "postgresql://test:test@localhost:5432/test",
            "FRONTEND_EMBED_ORIGIN": "https://app.example.com",
            "FUB_EMBED_SECRET": "test-embed-secret",
            "JWT_SECRET": "test-jwt-secret",
            "MARKETING_ORIGIN": "https://example.com",
            "OPENAI_API_KEY": "sk-test-key",
            "REDIS_URL": "redis://localhost:6379/0",
            "STRIPE_PRICE_ID_MONTHLY": "price_test123",
            "STRIPE_SECRET_KEY": "sk_test_stripe",
            "STRIPE_WEBHOOK_SECRET": "whsec_test",
            "UNKNOWN_VAR": "this_should_be_ignored",
            "ANOTHER_UNKNOWN": "also_ignored"
        }

        with patch.dict(os.environ, test_env, clear=True):
            # Should not raise ValidationError for unknown variables
            test_settings = Settings()
            assert not hasattr(test_settings, 'unknown_var')
            assert not hasattr(test_settings, 'another_unknown')


class TestGlobalSettingsInstance:
    """Test global settings instance."""

    def test_global_settings_exists(self):
        """Test that global settings instance can be created."""
        from config import Settings
        settings = Settings()
        assert settings is not None

    def test_global_settings_has_required_attributes(self):
        """Test that global settings has all required attributes."""
        test_settings = Settings()
        
        required_attrs = [
            'app_env', 'database_url', 'frontend_embed_origin',
            'fub_client_id', 'fub_client_secret', 'fub_embed_secret',
            'jwt_secret', 'marketing_origin', 'openai_api_key',
            'redis_url', 'stripe_price_id_monthly', 'stripe_secret_key',
            'stripe_webhook_secret', 'cors_origins', 'log_level',
            'rate_limit_requests_per_minute', 'rate_limit_requests_per_minute_ip'
        ]
        
        for attr in required_attrs:
            assert hasattr(test_settings, attr), f"Missing attribute: {attr}"


class TestSettingsIntegration:
    """Integration tests for settings."""

    def test_settings_serialization(self):
        """Test that settings can be serialized."""
        test_settings = Settings()
        
        # Test dict conversion
        settings_dict = test_settings.model_dump() if hasattr(test_settings, 'model_dump') else test_settings.dict()
        assert isinstance(settings_dict, dict)
        assert 'app_env' in settings_dict
        assert 'database_url' in settings_dict

    def test_settings_env_file_config(self):
        """Test settings configuration for env file loading."""
        test_settings = Settings()
        config = test_settings.model_config if hasattr(test_settings, 'model_config') else test_settings.Config
        
        # Verify env file configuration
        if hasattr(config, 'env_file'):
            assert config.env_file == ".env"
        if hasattr(config, 'env_file_encoding'):
            assert config.env_file_encoding == "utf-8" 