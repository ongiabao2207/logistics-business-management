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
    )
