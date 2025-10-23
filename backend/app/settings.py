"""
LetterOn Server - Application Settings
Purpose: Centralized configuration management using Pydantic Settings
Testing: Loads from .env file or environment variables
AWS Deployment: Set environment variables in ECS task definition or Lambda configuration

This module defines all configuration settings for the application including:
- AWS credentials and service names
- Database table names
- Authentication settings
- CORS configuration
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.

    All settings have default values where appropriate.
    Required settings without defaults will raise validation errors if missing.
    """

    # Application Settings
    app_name: str = "LetterOn Server"
    debug: bool = False
    log_level: str = "INFO"
    environment: str = "development"

    # Security
    secret_key: str  # REQUIRED - Used for JWT signing
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # AWS Configuration
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""  # Optional, uses default boto3 credentials if empty
    aws_secret_access_key: str = ""  # Optional, uses default boto3 credentials if empty

    # S3 Configuration
    s3_bucket_name: str = "letteron-images"
    s3_image_prefix: str = "letters/"  # Prefix for letter images in S3

    # Lambda Functions
    lambda_ocr_function_name: str = "LetterOnOCRHandler"
    lambda_llm_function_name: str = "LetterOnLLMHandler"

    # DynamoDB Configuration
    dynamodb_endpoint: str = ""  # For local development (e.g., http://localhost:8002)

    # DynamoDB Tables
    dynamodb_users_table: str = "LetterOn-Users"
    dynamodb_letters_table: str = "LetterOn-Letters"
    dynamodb_reminders_table: str = "LetterOn-Reminders"
    dynamodb_conversations_table: str = "LetterOn-Conversations"

    # CORS Settings
    cors_origins: str = "http://localhost:3000,http://localhost:3001,http://localhost:5173"

    # File Upload Settings
    max_upload_size_mb: int = 1  # Max size per file in MB
    max_files_per_upload: int = 3
    allowed_image_types: List[str] = ["image/jpeg", "image/png", "image/jpg", "image/webp"]

    # Reminder Scheduler Settings
    reminder_check_interval_seconds: int = 60  # Check reminders every 60 seconds

    # Rate Limiting (optional - for future implementation)
    rate_limit_enabled: bool = False
    rate_limit_requests_per_minute: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS origins string to list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def max_upload_size_bytes(self) -> int:
        """Convert max upload size from MB to bytes."""
        return self.max_upload_size_mb * 1024 * 1024

    def get_aws_credentials(self) -> dict:
        """
        Get AWS credentials configuration.
        Returns empty dict if using default credentials.
        """
        if self.aws_access_key_id and self.aws_secret_access_key:
            return {
                "aws_access_key_id": self.aws_access_key_id,
                "aws_secret_access_key": self.aws_secret_access_key,
                "region_name": self.aws_region
            }
        return {"region_name": self.aws_region}


# Global settings instance
settings = Settings()


# Validate critical settings on import
if len(settings.secret_key) < 32:
    raise ValueError(
        "SECRET_KEY must be at least 32 characters long for secure JWT signing. "
        "Generate one using: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
    )
