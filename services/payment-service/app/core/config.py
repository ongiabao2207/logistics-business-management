import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    app_name: str
    api_prefix: str
    database_url: str
    use_fake_clients: bool
    identity_jwks_url: str
    jwt_issuer: str
    jwt_audience: str
    rabbitmq_url: str
    rabbitmq_enabled: bool
    contract_service_url: str
    production_service_url: str
    price_service_url: str
    upstream_timeout_seconds: float


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv(
            "PAYMENT_SERVICE_APP_NAME",
            "Payment Service",
        ),
        api_prefix=os.getenv(
            "PAYMENT_SERVICE_API_PREFIX",
            "/api/v1",
        ),
        database_url=os.getenv(
            "PAYMENT_DATABASE_URL",
            "sqlite:///./payment.db",
        ),
        use_fake_clients=os.getenv(
            "PAYMENT_USE_FAKE_CLIENTS",
            "true",
        ).lower() == "true",
        identity_jwks_url=os.getenv(
            "PAYMENT_IDENTITY_JWKS_URL",
            "http://localhost:8005/.well-known/jwks.json",
        ),
        jwt_issuer=os.getenv("PAYMENT_JWT_ISSUER", "identity-service"),
        jwt_audience=os.getenv("PAYMENT_JWT_AUDIENCE", "logistics-api"),
        rabbitmq_url=os.getenv("PAYMENT_RABBITMQ_URL", "amqp://guest:guest@localhost:5672/%2F"),
        rabbitmq_enabled=os.getenv("PAYMENT_RABBITMQ_ENABLED", "false").lower() == "true",
        contract_service_url=os.getenv("PAYMENT_CONTRACT_SERVICE_URL", "http://localhost:8001/api/v1"),
        production_service_url=os.getenv("PAYMENT_PRODUCTION_SERVICE_URL", "http://localhost:8003/api/v1"),
        price_service_url=os.getenv("PAYMENT_PRICE_SERVICE_URL", "http://localhost:8002/api/v1"),
        upstream_timeout_seconds=float(os.getenv("PAYMENT_UPSTREAM_TIMEOUT_SECONDS", "5")),
    )
