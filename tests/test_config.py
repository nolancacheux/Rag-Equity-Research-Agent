"""Tests for configuration settings."""

import pytest
from unittest.mock import patch, MagicMock
import os


class TestSettings:
    """Tests for Settings class."""

    def test_settings_with_groq(self):
        """Test settings with Groq API key."""
        # Import fresh each time
        import importlib
        import src.config.settings as settings_module
        
        with patch.dict(os.environ, {
            "GROQ_API_KEY": "test-groq-key",
        }, clear=True):
            importlib.reload(settings_module)
            settings = settings_module.Settings()

            assert settings.groq_api_key is not None
            assert settings.use_groq is True

    def test_is_production_false(self):
        """Test is_production property when not in production."""
        import importlib
        import src.config.settings as settings_module
        
        with patch.dict(os.environ, {
            "GROQ_API_KEY": "test-key",
            "APP_ENV": "development",
        }, clear=True):
            importlib.reload(settings_module)
            settings = settings_module.Settings()

            assert settings.is_production is False

    def test_is_production_true(self):
        """Test is_production property when in production."""
        import importlib
        import src.config.settings as settings_module
        
        with patch.dict(os.environ, {
            "GROQ_API_KEY": "test-key",
            "APP_ENV": "production",
        }, clear=True):
            importlib.reload(settings_module)
            settings = settings_module.Settings()

            assert settings.is_production is True

    def test_use_azure_openai_complete(self):
        """Test use_azure_openai when fully configured."""
        import importlib
        import src.config.settings as settings_module
        
        with patch.dict(os.environ, {
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
            "AZURE_OPENAI_API_KEY": "test-azure-key",
            "AZURE_OPENAI_DEPLOYMENT": "gpt-4",
        }, clear=True):
            importlib.reload(settings_module)
            settings = settings_module.Settings()

            assert settings.use_azure_openai is True

    def test_use_azure_openai_incomplete(self):
        """Test use_azure_openai when only endpoint configured."""
        import importlib
        import src.config.settings as settings_module
        
        with patch.dict(os.environ, {
            "GROQ_API_KEY": "test-key",
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
            # No API key
        }, clear=True):
            importlib.reload(settings_module)
            settings = settings_module.Settings()

            assert settings.use_azure_openai is False

    def test_default_values(self):
        """Test default settings values."""
        import importlib
        import src.config.settings as settings_module
        
        with patch.dict(os.environ, {
            "GROQ_API_KEY": "test-key",
        }, clear=True):
            importlib.reload(settings_module)
            settings = settings_module.Settings()

            assert settings.app_env == "development"
            assert settings.log_level == "INFO"
            assert settings.api_port == 8000


class TestGetSettings:
    """Tests for get_settings function."""

    def test_get_settings_returns_settings(self):
        """Test that get_settings returns a Settings instance."""
        import importlib
        import src.config.settings as settings_module
        
        with patch.dict(os.environ, {
            "GROQ_API_KEY": "test-key",
        }, clear=True):
            importlib.reload(settings_module)
            settings_module.get_settings.cache_clear()
            
            settings = settings_module.get_settings()

            assert settings is not None
            assert hasattr(settings, 'app_env')
