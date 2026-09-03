import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    app_name: str
    database_url: str
    identity_jwks_url: str
    jwt_issuer: str
    jwt_audience: str


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("CUSTOMER_SERVICE_APP_NAME", "Customer Service"),
        database_url=os.getenv(
            "CUSTOMER_SERVICE_DATABASE_URL",
            "postgresql+psycopg://customer_user:customer_password@localhost:5437/customer_db",
        ),
        identity_jwks_url=os.getenv(
            "CUSTOMER_SERVICE_IDENTITY_JWKS_URL",
            "http://localhost:8005/.well-known/jwks.json",
        ),
        jwt_issuer=os.getenv("CUSTOMER_SERVICE_JWT_ISSUER", "identity-service"),
        jwt_audience=os.getenv("CUSTOMER_SERVICE_JWT_AUDIENCE", "logistics-api"),
    )
