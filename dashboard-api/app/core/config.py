from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", case_sensitive=False
    )

    app_name: str = "TESIS Dashboard API"
    database_url: str = (
        "postgresql+psycopg://n8n_user:n8n_pass@postgres:5432/ecommerce_tesis"
    )
    dashboard_jwt_secret: str = "demo-dashboard-jwt-secret"
    dashboard_enc_key: str = ""
    dashboard_n8n_secret: str = "demo-n8n-secret"
    dashboard_google_client_id: str = ""
    dashboard_google_client_secret: str = ""
    dashboard_google_redirect_uri: str = ""
    dashboard_frontend_url: str = "http://localhost:5173"
    telegram_code_ttl_minutes: int = 15
    cors_origins: str = "http://localhost:5173,http://localhost:8080"

    access_token_expire_minutes: int = 120
    refresh_token_expire_days: int = 7

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()