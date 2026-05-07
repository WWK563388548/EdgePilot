from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "backend/.env"), extra="ignore")

    app_name: str = "EdgePilot Backend"
    app_env: str = "local"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    database_url: str = "postgresql://edgepilot:edgepilot@localhost:5432/edgepilot"
    redis_url: str = "redis://localhost:6379/0"
    cors_allowed_origins: str = "http://localhost:3000"

    auth_issuer: str = ""
    auth_audience: str = ""
    auth_jwks_url: str = ""
    auth_algorithms: str = "RS256"
    auth_tenant_claim: str = "https://edgepilot/tenant_id"
    auth_account_claim: str = "https://edgepilot/account_id"
    auth_role_claim: str = "https://edgepilot/role"
    auth_email_claim: str = "https://edgepilot/email"
    auth_display_name_claim: str = "https://edgepilot/name"
    auth_email_verified_claim: str = "https://edgepilot/email_verified"
    auth_default_role: str = "owner"
    auth0_management_client_id: str = ""
    auth0_management_client_secret: str = ""
    auth0_management_audience: str = ""

    polygon_api_key: str = ""
    polygon_base_url: str = "https://api.polygon.io"
    ingestion_admin_token: str = ""

    sse_heartbeat_seconds: int = 15


settings = Settings()
