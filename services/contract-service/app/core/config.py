import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    app_name: str
    database_url: str
    customer_client_mode: str


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("CONTRACT_SERVICE_APP_NAME", "Contract Service"),
        database_url=os.getenv(
            "CONTRACT_SERVICE_DATABASE_URL",
            "postgresql+psycopg://contract_user:contract_password@localhost:5432/contract_db",
        ),
        customer_client_mode=os.getenv("CONTRACT_SERVICE_CUSTOMER_CLIENT_MODE", "fake"),
    )
