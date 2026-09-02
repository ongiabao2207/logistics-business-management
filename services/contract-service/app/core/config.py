import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    app_name: str
    database_url: str
    customer_client_mode: str
    price_client_mode: str
    price_service_url: str
    price_client_timeout_seconds: float
    redis_url: str
    price_cache_enabled: bool
    price_cache_ttl_seconds: int
    identity_jwks_url: str
    jwt_issuer: str
    jwt_audience: str
    rabbitmq_url: str
    rabbitmq_enabled: bool


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("CONTRACT_SERVICE_APP_NAME", "Contract Service"),
        database_url=os.getenv(
            "CONTRACT_SERVICE_DATABASE_URL",
            "postgresql+psycopg://contract_user:contract_password@localhost:5432/contract_db",
        ),
        customer_client_mode=os.getenv("CONTRACT_SERVICE_CUSTOMER_CLIENT_MODE", "fake"),
        price_client_mode=os.getenv("CONTRACT_SERVICE_PRICE_CLIENT_MODE", "fake"),
        price_service_url=os.getenv(
            "CONTRACT_SERVICE_PRICE_SERVICE_URL",
            "http://localhost:8002/api/v1",
        ),
        price_client_timeout_seconds=float(
            os.getenv("CONTRACT_SERVICE_PRICE_CLIENT_TIMEOUT_SECONDS", "5")
        ),
        redis_url=os.getenv("CONTRACT_SERVICE_REDIS_URL", "redis://localhost:6379/0"),
        price_cache_enabled=os.getenv(
            "CONTRACT_SERVICE_PRICE_CACHE_ENABLED", "false"
        ).lower()
        == "true",
        price_cache_ttl_seconds=int(
            os.getenv("CONTRACT_SERVICE_PRICE_CACHE_TTL_SECONDS", "300")
        ),
        identity_jwks_url=os.getenv(
            "CONTRACT_SERVICE_IDENTITY_JWKS_URL",
            "http://localhost:8005/.well-known/jwks.json",
        ),
        jwt_issuer=os.getenv("CONTRACT_SERVICE_JWT_ISSUER", "identity-service"),
        jwt_audience=os.getenv("CONTRACT_SERVICE_JWT_AUDIENCE", "logistics-api"),
        rabbitmq_url=os.getenv("CONTRACT_SERVICE_RABBITMQ_URL", "amqp://guest:guest@localhost:5672/%2F"),
        rabbitmq_enabled=os.getenv("CONTRACT_SERVICE_RABBITMQ_ENABLED", "false").lower() == "true",
    )
