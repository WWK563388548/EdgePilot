from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "backend/.env"), extra="ignore")

    app_name: str = "EdgePilot Backend"
    app_env: str = "local"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://edgepilot:edgepilot@localhost:5432/edgepilot"
    redis_url: str = "redis://localhost:6379/0"

    sse_heartbeat_seconds: int = 15


settings = Settings()
