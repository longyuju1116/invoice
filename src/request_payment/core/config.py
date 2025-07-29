"""Configuration management for RequestPayment system."""

from functools import lru_cache
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Configuration for pydantic-settings
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application settings
    app_name: str = Field(default="RequestPayment")
    environment: str = Field(default="production")  # Changed for Hugging Face Spaces
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    
    # Server settings (simplified for Hugging Face Spaces)
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=7860)  # Hugging Face Spaces default port
    workers: int = Field(default=1)
    
    # Security settings (simplified)
    secret_key: str = Field(default="huggingface-spaces-demo-key-change-this-in-production-12345678")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=7)
    
    # CORS settings (relaxed for demo)
    cors_origins: str = Field(default="*")  # Allow all origins for demo
    allowed_hosts: str = Field(default="*")  # Allow all hosts for demo
    

    
    # File storage settings (simplified for Hugging Face Spaces)
    upload_dir: str = Field(default="uploads")
    images_dir: str = Field(default="uploads/images")
    max_file_size: int = Field(default=5242880)  # 5MB
    max_image_size: int = Field(default=2097152)  # 2MB for images
    allowed_file_types: str = Field(default=".jpg,.jpeg,.png,.pdf")
    allowed_image_types: str = Field(default=".jpg,.jpeg,.png")
    
    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        """Validate secret key is provided."""
        if not value:
            raise ValueError("SECRET_KEY must be provided")
        if len(value) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return value
    
    def get_cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        if self.cors_origins == "*":
            return ["*"]
        return [item.strip() for item in self.cors_origins.split(",")]
    
    def get_allowed_hosts_list(self) -> List[str]:
        """Get allowed hosts as a list."""
        if self.allowed_hosts == "*":
            return ["*"]
        return [item.strip() for item in self.allowed_hosts.split(",")]
    
    def get_allowed_image_types_list(self) -> List[str]:
        """Get allowed image types as a list."""
        return [item.strip() for item in self.allowed_image_types.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.
    
    Returns:
        Settings: The application settings.
    """
    return Settings() 