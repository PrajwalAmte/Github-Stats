from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    # Database
    database_url: str

    # GitHub
    github_token: str
    github_api_url: str = "https://api.github.com/graphql"

    # Sync Authentication
    sync_secret: str

    # Application
    environment: str = "development"
    log_level: str = "INFO"

    # Sync Configuration
    sync_lock_duration_seconds: int = 300  # 5 minutes
    sync_failure_threshold: int = 3


settings = Settings()
