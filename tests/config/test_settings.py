"""Tests for the settings module."""

import os
from pathlib import Path
from typing import Generator

import pytest
from pydantic import ValidationError

from src.config.settings import AppSettings, MinIOSettings, OpenAISettings, settings


@pytest.fixture
def mock_env_vars() -> Generator[None, None, None]:
    """Fixture to set up test environment variables."""
    # Store original environment variables
    original_env = dict(os.environ)
    
    # Set test environment variables
    os.environ.update({
        'MINIO_ENDPOINT': 'http://test-minio:9001',
        'MINIO_ACCESS_KEY': 'test-access-key',
        'MINIO_SECRET_KEY': 'test-secret-key',
        'MINIO_BUCKET_NAME': 'test-bucket',
        'OPENAI_API_KEY': 'test-openai-key',
        'OPENAI_MODEL_NAME': 'gpt-3.5-turbo',
        'OPENAI_TEMPERATURE': '0.5',
        'OPENAI_MAX_TOKENS': '500',
        'DEBUG': 'true',
        'LOG_LEVEL': 'DEBUG'
    })
    
    yield
    
    # Restore original environment variables
    os.environ.clear()
    os.environ.update(original_env)


class TestMinIOSettings:
    """Test suite for MinIO settings."""
    
    def test_minio_settings_validation(self, mock_env_vars):
        """Test MinIO settings validation."""
        minio_settings = MinIOSettings()
        
        assert minio_settings.endpoint == 'http://test-minio:9001'
        assert minio_settings.access_key == 'test-access-key'
        assert minio_settings.secret_key.get_secret_value() == 'test-secret-key'
        assert minio_settings.bucket_name == 'test-bucket'
    
    def test_minio_settings_missing_required(self):
        """Test MinIO settings with missing required fields."""
        # Remove required environment variables
        if 'MINIO_ENDPOINT' in os.environ:
            del os.environ['MINIO_ENDPOINT']
        
        with pytest.raises(ValidationError):
            MinIOSettings()


class TestOpenAISettings:
    """Test suite for OpenAI settings."""
    
    def test_openai_settings_validation(self, mock_env_vars):
        """Test OpenAI settings validation."""
        openai_settings = OpenAISettings()
        
        assert openai_settings.api_key.get_secret_value() == 'test-openai-key'
        assert openai_settings.model_name == 'gpt-3.5-turbo'
        assert openai_settings.temperature == 0.5
        assert openai_settings.max_tokens == 500
    
    def test_openai_settings_defaults(self):
        """Test OpenAI settings with default values."""
        # Remove OpenAI environment variables
        for key in ['OPENAI_API_KEY', 'OPENAI_MODEL_NAME', 'OPENAI_TEMPERATURE', 'OPENAI_MAX_TOKENS']:
            if key in os.environ:
                del os.environ[key]
        
        openai_settings = OpenAISettings()
        
        assert openai_settings.api_key is None
        assert openai_settings.model_name == 'gpt-4'
        assert openai_settings.temperature == 0.7
        assert openai_settings.max_tokens == 1000


class TestAppSettings:
    """Test suite for application settings."""
    
    def test_app_settings_validation(self, mock_env_vars):
        """Test application settings validation."""
        app_settings = AppSettings()
        
        assert app_settings.debug is True
        assert app_settings.log_level == 'DEBUG'
        assert isinstance(app_settings.input_dir, Path)
        assert isinstance(app_settings.output_dir, Path)
        
        # Test nested settings
        assert app_settings.minio.endpoint == 'http://test-minio:9001'
        assert app_settings.openai.model_name == 'gpt-3.5-turbo'
    
    def test_app_settings_defaults(self):
        """Test application settings with default values."""
        # Remove environment variables
        for key in ['DEBUG', 'LOG_LEVEL']:
            if key in os.environ:
                del os.environ[key]
        
        app_settings = AppSettings()
        
        assert app_settings.debug is False
        assert app_settings.log_level == 'INFO'
        assert app_settings.input_dir == Path('data/input')
        assert app_settings.output_dir == Path('data/output')


def test_global_settings_instance(mock_env_vars):
    """Test the global settings instance."""
    assert isinstance(settings, AppSettings)
    assert settings.debug is True
    assert settings.log_level == 'DEBUG'
    assert settings.minio.endpoint == 'http://test-minio:9001'
    assert settings.openai.model_name == 'gpt-3.5-turbo' 