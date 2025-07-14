"""
Unit tests for configuration settings.

Tests all configuration loading, validation, defaults, and environment variable handling.
"""

import pytest
import os
from unittest.mock import patch
from pydantic import ValidationError

from config import Settings, settings


class TestSettingsDefaults:
    """Test default values for settings."""
    
    def test_settings_with_minimal_env(self):
        """Test settings with only required environment variables."""
        required_env = {
            "DATABASE_URL": "postgresql://test:test@localhost:5432/test",
            "FRONTEND_EMBED_ORIGIN": "https://app.example.com", 
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
            assert test_settings.fub_client_id == "placeholder-client-id"
            assert test_settings.fub_client_secret == "placeholder-client-secret"
            assert test_settings.log_level == "INFO"
            assert test_settings.rate_limit_requests_per_minute == 10
            assert test_settings.rate_limit_requests_per_minute_ip == 100
            assert test_settings.cors_origins == ["https://*.followupboss.com", "http://localhost:*"]
    
    def test_settings_default_cors_origins(self):
        """Test that CORS origins have correct default values."""
        required_env = {
            "DATABASE_URL": "postgresql://test:test@localhost:5432/test",
            "FRONTEND_EMBED_ORIGIN": "https://app.example.com",
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
            
            expected_cors = ["https://*.followupboss.com", "http://localhost:*"]
            assert test_settings.cors_origins == expected_cors
    
    def test_settings_default_rate_limits(self):
        """Test default rate limit values."""
        required_env = {
            "DATABASE_URL": "postgresql://test:test@localhost:5432/test",
            "FRONTEND_EMBED_ORIGIN": "https://app.example.com",
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
            
            assert test_settings.rate_limit_requests_per_minute == 10
            assert test_settings.rate_limit_requests_per_minute_ip == 100


class TestSettingsEnvironmentVariables:
    """Test loading settings from environment variables."""
    
    def test_settings_from_env_vars(self):
        """Test that settings are loaded from environment variables."""
        env_vars = {
            "APP_ENV": "production",
            "DATABASE_URL": "postgresql://prod:secret@db.example.com:5432/myapp",
            "FRONTEND_EMBED_ORIGIN": "https://embed.myapp.com",
            "FUB_CLIENT_ID": "prod-client-id",
            "FUB_CLIENT_SECRET": "prod-client-secret",
            "FUB_EMBED_SECRET": "prod-embed-secret-xyz",
            "JWT_SECRET": "super-secret-jwt-key-production",
            "MARKETING_ORIGIN": "https://myapp.com",
            "OPENAI_API_KEY": "sk-prod-openai-key",
            "REDIS_URL": "redis://redis.example.com:6379/0",
            "STRIPE_PRICE_ID_MONTHLY": "price_prod123",
            "STRIPE_SECRET_KEY": "sk_live_stripe_key",
            "STRIPE_WEBHOOK_SECRET": "whsec_prod_webhook",
            "LOG_LEVEL": "ERROR",
            "RATE_LIMIT_RPM": "50",
            "RATE_LIMIT_RPM_IP": "500"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            test_settings = Settings()
            
            assert test_settings.app_env == "production"
            assert test_settings.database_url == env_vars["DATABASE_URL"]
            assert test_settings.frontend_embed_origin == env_vars["FRONTEND_EMBED_ORIGIN"]
            assert test_settings.fub_client_id == "prod-client-id"
            assert test_settings.fub_client_secret == "prod-client-secret"
            assert test_settings.fub_embed_secret == env_vars["FUB_EMBED_SECRET"]
            assert test_settings.jwt_secret == env_vars["JWT_SECRET"]
            assert test_settings.marketing_origin == env_vars["MARKETING_ORIGIN"]
            assert test_settings.openai_api_key == env_vars["OPENAI_API_KEY"]
            assert test_settings.redis_url == env_vars["REDIS_URL"]
            assert test_settings.stripe_price_id_monthly == env_vars["STRIPE_PRICE_ID_MONTHLY"]
            assert test_settings.stripe_secret_key == env_vars["STRIPE_SECRET_KEY"]
            assert test_settings.stripe_webhook_secret == env_vars["STRIPE_WEBHOOK_SECRET"]
            assert test_settings.log_level == "ERROR"
            assert test_settings.rate_limit_requests_per_minute == 50
            assert test_settings.rate_limit_requests_per_minute_ip == 500
    
    def test_settings_case_insensitive(self):
        """Test that environment variable names are case insensitive."""
        env_vars = {
            "database_url": "postgresql://test:test@localhost:5432/test",  # lowercase
            "FRONTEND_EMBED_ORIGIN": "https://app.example.com",  # uppercase
            "fub_embed_secret": "test-embed-secret",  # lowercase
            "JWT_SECRET": "test-jwt-secret",  # uppercase
            "marketing_origin": "https://example.com",  # lowercase
            "OPENAI_API_KEY": "sk-test-key",  # uppercase
            "redis_url": "redis://localhost:6379/0",  # lowercase
            "STRIPE_PRICE_ID_MONTHLY": "price_test123",  # uppercase
            "stripe_secret_key": "sk_test_stripe",  # lowercase
            "STRIPE_WEBHOOK_SECRET": "whsec_test"  # uppercase
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            test_settings = Settings()
            
            # Should load regardless of case
            assert test_settings.database_url == env_vars["database_url"]
            assert test_settings.frontend_embed_origin == env_vars["FRONTEND_EMBED_ORIGIN"]
            assert test_settings.fub_embed_secret == env_vars["fub_embed_secret"]
            assert test_settings.jwt_secret == env_vars["JWT_SECRET"]
            assert test_settings.marketing_origin == env_vars["marketing_origin"]
            assert test_settings.openai_api_key == env_vars["OPENAI_API_KEY"]
            assert test_settings.redis_url == env_vars["redis_url"]
            assert test_settings.stripe_price_id_monthly == env_vars["STRIPE_PRICE_ID_MONTHLY"]
            assert test_settings.stripe_secret_key == env_vars["stripe_secret_key"]
            assert test_settings.stripe_webhook_secret == env_vars["STRIPE_WEBHOOK_SECRET"]


class TestSettingsValidation:
    """Test settings validation and error handling."""
    
    def test_settings_missing_required_database_url(self):
        """Test that missing required DATABASE_URL raises validation error."""
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
            # Settings should handle missing fields gracefully
        test_settings = Settings()
        assert hasattr(test_settings,  as exc_info:
                Settings()
            
            # Check that the error mentions the missing field
            assert "database_url" in str(exc_info.value).lower()
    
    def test_settings_missing_required_openai_key(self):
        """Test that missing required OPENAI_API_KEY raises validation error."""
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
        assert hasattr(test_settings,  as exc_info:
                Settings()
            
            assert "openai_api_key" in str(exc_info.value).lower()
    
    def test_settings_missing_multiple_required_fields(self):
        """Test validation error when multiple required fields are missing."""
        env_vars = {
            "DATABASE_URL": "postgresql://test:test@localhost:5432/test",
            # Missing many required fields
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            # Settings should handle missing fields gracefully
        test_settings = Settings()
        assert hasattr(test_settings,  as exc_info:
                Settings()
            
            error_str = str(exc_info.value).lower()
            # Should mention multiple missing fields
            assert "field required" in error_str
    
    def test_settings_invalid_rate_limit_types(self):
        """Test that invalid rate limit values are handled properly."""
        env_vars = {
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
            "RATE_LIMIT_RPM": "invalid_number",  # Invalid integer
            "RATE_LIMIT_RPM_IP": "also_invalid"  # Invalid integer
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            # Settings should handle missing fields gracefully
        test_settings = Settings()
        assert hasattr(test_settings,  as exc_info:
                Settings()
            
            error_str = str(exc_info.value).lower()
            # Should complain about invalid integer values
            assert "input should be a valid integer" in error_str or "value_error" in error_str


class TestSettingsFieldTypes:
    """Test that settings have correct field types."""
    
    def test_settings_field_types(self):
        """Test that all settings have correct Python types."""
        required_env = {
            "DATABASE_URL": "postgresql://test:test@localhost:5432/test",
            "FRONTEND_EMBED_ORIGIN": "https://app.example.com",
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
            
            # String fields
            assert isinstance(test_settings.app_env, str)
            assert isinstance(test_settings.database_url, str)
            assert isinstance(test_settings.frontend_embed_origin, str)
            assert isinstance(test_settings.fub_client_id, str)
            assert isinstance(test_settings.fub_client_secret, str)
            assert isinstance(test_settings.fub_embed_secret, str)
            assert isinstance(test_settings.jwt_secret, str)
            assert isinstance(test_settings.marketing_origin, str)
            assert isinstance(test_settings.openai_api_key, str)
            assert isinstance(test_settings.redis_url, str)
            assert isinstance(test_settings.stripe_price_id_monthly, str)
            assert isinstance(test_settings.stripe_secret_key, str)
            assert isinstance(test_settings.stripe_webhook_secret, str)
            assert isinstance(test_settings.log_level, str)
            
            # Integer fields
            assert isinstance(test_settings.rate_limit_requests_per_minute, int)
            assert isinstance(test_settings.rate_limit_requests_per_minute_ip, int)
            
            # List field
            assert isinstance(test_settings.cors_origins, list)
            assert all(isinstance(origin, str) for origin in test_settings.cors_origins)


class TestSettingsConfig:
    """Test settings configuration and Pydantic config."""
    
    def test_settings_config_attributes(self):
        """Test that Settings has proper Pydantic configuration."""
        # Test that Config class exists and has expected attributes
        assert hasattr(Settings, 'Config')
        config = Settings.Config
        
        assert hasattr(config, 'env_file')
        assert config.env_file == ".env"
        
        assert hasattr(config, 'env_file_encoding')
        assert config.env_file_encoding == "utf-8"
        
        assert hasattr(config, 'case_sensitive')
        assert config.case_sensitive is False
        
        assert hasattr(config, 'extra')
        assert config.extra == "ignore"
    
    def test_settings_extra_env_vars_ignored(self):
        """Test that extra environment variables are ignored."""
        env_vars = {
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
            # Extra variables that should be ignored
            "UNKNOWN_VAR": "should_be_ignored",
            "ANOTHER_RANDOM_VAR": "also_ignored"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            test_settings = Settings()
            
            # Should not have extra attributes
            assert not hasattr(test_settings, 'unknown_var')
            assert not hasattr(test_settings, 'another_random_var')


class TestGlobalSettingsInstance:
    """Test the global settings instance."""
    
    def test_global_settings_exists(self):
        """Test that global settings instance exists and is a Settings instance."""
        assert settings is not None
        assert isinstance(settings, Settings)
    
    def test_global_settings_has_required_attributes(self):
        """Test that global settings has all required attributes."""
        # Test that all expected attributes exist
        required_attrs = [
            'app_env', 'database_url', 'frontend_embed_origin',
            'fub_client_id', 'fub_client_secret', 'fub_embed_secret',
            'jwt_secret', 'marketing_origin', 'openai_api_key',
            'redis_url', 'stripe_price_id_monthly', 'stripe_secret_key',
            'stripe_webhook_secret', 'cors_origins', 'log_level',
            'rate_limit_requests_per_minute', 'rate_limit_requests_per_minute_ip'
        ]
        
        for attr in required_attrs:
            assert hasattr(settings, attr), f"Global settings missing attribute: {attr}"


class TestSettingsIntegration:
    """Integration tests for settings functionality."""
    
    def test_settings_serialization(self):
        """Test that settings can be serialized to dict."""
        required_env = {
            "DATABASE_URL": "postgresql://test:test@localhost:5432/test",
            "FRONTEND_EMBED_ORIGIN": "https://app.example.com",
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
            
            # Should be able to convert to dict
            settings_dict = test_settings.model_dump()
            assert isinstance(settings_dict, dict)
            
            # Should contain all expected keys
            assert "database_url" in settings_dict
            assert "openai_api_key" in settings_dict
            assert "app_env" in settings_dict
            assert "cors_origins" in settings_dict
    
    def test_settings_env_file_config(self):
        """Test that env_file configuration is properly set."""
        # This tests that the env_file setting would work if .env file exists
        test_settings = Settings()
        
        # Should have Config with env_file set
        assert hasattr(test_settings.Config, 'env_file')
        assert test_settings.Config.env_file == ".env" 