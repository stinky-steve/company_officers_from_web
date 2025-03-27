"""Configuration settings for the application."""

import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class AppSettings:
    """Application settings."""
    
    # MinIO Configuration
    minio_endpoint: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    minio_access_key: str = os.getenv("MINIO_ACCESS_KEY", "")
    minio_secret_key: str = os.getenv("MINIO_SECRET_KEY", "")
    minio_bucket_name: str = os.getenv("MINIO_BUCKET_NAME", "min-co-web-page-data")
    
    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # Application Configuration
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Directory paths
    input_dir: Path = Path("data/raw")
    output_dir: Path = Path("data/processed")

# Create settings instance
settings = AppSettings() 