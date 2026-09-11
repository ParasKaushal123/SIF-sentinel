"""Application configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://sif_user:sif_pass@localhost:5432/sif_sentinel"
    database_url_sync: str = "postgresql://sif_user:sif_pass@localhost:5432/sif_sentinel"

    # Model provider
    model_provider: str = "fixture"  # fixture | openai | anthropic
    model_api_key: str = ""
    model_name: str = "gpt-4o"

    # Analysis
    analysis_timeout_seconds: int = 30

    # Worker
    worker_enabled: bool = False
    worker_concurrency: int = 4
    worker_poll_interval: int = 2

    # Mode
    demo_mode: bool = True

    # App
    app_name: str = "SIF Sentinel"
    app_version: str = "0.1.0"
    debug: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
