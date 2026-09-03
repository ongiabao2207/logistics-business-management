from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://notification_user:notification_password@localhost:5437/notification_db"
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/%2F"
    rabbitmq_consumer_enabled: bool = False
    identity_jwks_url: str = "http://localhost:8005/.well-known/jwks.json"
    jwt_issuer: str = "identity-service"
    jwt_audience: str = "logistics-api"

    model_config = SettingsConfigDict(env_prefix="NOTIFICATION_", env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
