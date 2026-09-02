from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Identity Service"
    database_url: str = "postgresql+psycopg://identity_user:identity_password@localhost:5436/identity_db"
    jwt_private_key_path: Path = Path("secrets/jwt-private.pem")
    jwt_public_key_path: Path = Path("secrets/jwt-public.pem")
    jwt_issuer: str = "identity-service"
    jwt_audience: str = "logistics-api"
    access_token_ttl_minutes: int = 15
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/%2F"
    rabbitmq_enabled: bool = False

    model_config = SettingsConfigDict(env_prefix="IDENTITY_", env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
