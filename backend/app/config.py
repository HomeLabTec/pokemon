from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "PokeVault"
    secret_key: str = "dev-secret"
    access_token_expire_minutes: int = 60 * 24
    database_url: str = "postgresql+psycopg2://pokemon:pokemon@db:5432/pokemon"
    redis_url: str = "redis://redis:6379/0"
    media_root: str = "/media"
    allowed_origins: str = "http://localhost:8080,http://localhost:5173"


settings = Settings()
