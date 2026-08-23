import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    app_name: str
    api_prefix: str
    database_url: str
    use_fake_clients: bool


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
    )