"""
Configuration module using Pydantic Settings.

CRITICAL: This module uses lazy loading pattern.
No environment variables are loaded at import time.
Each service must call get_settings() explicitly.
"""

from typing import Optional
from urllib.parse import urlparse

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    IMPORTANT: Do NOT set env_file in Config.
    Environment variables must be loaded externally by the service.
    """

    model_config = SettingsConfigDict(
        env_file=None,
        case_sensitive=False,
        extra="ignore"
    )

    # Database - Optional, will be built from Supabase if not provided
    database_url: Optional[str] = Field(
        default=None,
        description="PostgreSQL connection URL (optional if using Supabase)"
    )

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )

    # Authentication
    static_token: str = Field(
        ...,
        description="Static bearer token for API authentication"
    )

    # Supabase
    supabase_url: str = Field(
        ...,
        description="Supabase REST API URL"
    )
    supabase_secret_key: str = Field(
        ...,
        description="Supabase service role secret key"
    )

    # OpenRouter LLM
    openrouter_api_key: str = Field(
        ...,
        description="OpenRouter API key for LLM access"
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter API base URL"
    )
    math_model_name: str = Field(
        default="deepseek/deepseek-math-7b-instruct",
        description="Math model name on OpenRouter"
    )

    # Langfuse
    langfuse_secret_key: str = Field(
        ...,
        description="Langfuse secret key"
    )
    langfuse_public_key: str = Field(
        ...,
        description="Langfuse public key"
    )
    langfuse_base_url: str = Field(
        default="https://cloud.langfuse.com",
        description="Langfuse base URL"
    )

    # Sentry
    sentry_dsn: Optional[str] = Field(
        default=None,
        description="Sentry DSN for error tracking"
    )
    sentry_environment: str = Field(
        default="development",
        description="Sentry environment name"
    )
    sentry_traces_sample_rate: float = Field(
        default=0.1,
        description="Sentry traces sample rate"
    )
    sentry_profiles_sample_rate: float = Field(
        default=1.0,
        description="Sentry profiles sample rate"
    )

    # Application
    app_name: str = Field(
        default="MOE API",
        description="Application name"
    )
    debug: bool = Field(
        default=False,
        description="Debug mode flag"
    )

    @computed_field  # type: ignore[misc]
    @property
    def db_url(self) -> str:
        """
        Get database URL, building from Supabase credentials if DATABASE_URL not provided.
        
        Supabase connection format:
        postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
        
        Returns:
            str: PostgreSQL connection URL
        """
        if self.database_url:
            return self.database_url
        
        # Build from Supabase credentials
        # Parse Supabase URL to extract project ref and region
        parsed = urlparse(self.supabase_url)
        # Supabase URL format: https://[project-ref].supabase.co
        hostname = parsed.hostname or ""
        project_ref = hostname.split('.')[0] if hostname else ""
        
        # Supabase uses pooler connection for better performance
        # Format: postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
        # For simplicity, we'll use direct connection format
        # postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
        
        db_url = f"postgresql://postgres:{self.supabase_secret_key}@db.{project_ref}.supabase.co:5432/postgres"
        return db_url


def get_settings() -> Settings:
    """
    Factory function to create Settings instance.

    This function should be called by each service explicitly.
    DO NOT call this at module level.

    Returns:
        Settings: Configured settings instance

    Note:
        Settings() will automatically load values from environment
        variables. Required fields must be set in the environment
        before calling this function.
    """
    return Settings()  # type: ignore[call-arg]
