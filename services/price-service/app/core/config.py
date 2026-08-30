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
        app_name=os.getenv("PRICE_APP_NAME", "Price Service"),
        database_url=os.getenv(
            "PRICE_DATABASE_URL",
            "postgresql+psycopg://postgres:postgres@localhost:5432/price_db",
        ),
        identity_jwks_url=os.getenv(
            "PRICE_IDENTITY_JWKS_URL",
            "http://localhost:8005/.well-known/jwks.json",
        ),
        jwt_issuer=os.getenv("PRICE_JWT_ISSUER", "identity-service"),
        jwt_audience=os.getenv("PRICE_JWT_AUDIENCE", "logistics-api"),
    )
