"""Configuration settings for the application."""

from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseSettings, Field, HttpUrl, SecretStr

# Load environment variables from .env file
load_dotenv()


class MinIOSettings(BaseSettings):
    """MinIO configuration settings."""
    
    endpoint: HttpUrl = Field(..., env='MINIO_ENDPOINT')
    access_key: str = Field(..., env='MINIO_ACCESS_KEY')
    secret_key: SecretStr = Field(..., env='MINIO_SECRET_KEY')
    bucket_name: str = Field(..., env='MINIO_BUCKET_NAME')


class OpenAISettings(BaseSettings):
    """OpenAI configuration settings."""
    
    api_key: Optional[SecretStr] = Field(None, env='OPENAI_API_KEY')
    model_name: str = Field(default="gpt-4", env='OPENAI_MODEL_NAME')
    temperature: float = Field(default=0.7, env='OPENAI_TEMPERATURE')
    max_tokens: int = Field(default=1000, env='OPENAI_MAX_TOKENS')


class AppSettings(BaseSettings):
    """Application configuration settings."""
    
    debug: bool = Field(default=False, env='DEBUG')
    log_level: str = Field(default="INFO", env='LOG_LEVEL')
    input_dir: Path = Field(default=Path("data/input"))
    output_dir: Path = Field(default=Path("data/output"))
    
    # MinIO settings
    minio: MinIOSettings = Field(default_factory=MinIOSettings)
    
    # OpenAI settings
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create global settings instance
settings = AppSettings()
