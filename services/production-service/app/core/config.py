from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Production Service"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/production"
    contract_client_mode: str = "fake"
    contract_service_url: str = "http://contract-service:8000"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="PRODUCTION_", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
