from fastapi import Depends

from app.clients.contracts import FakeContractClient, HttpContractClient
from app.clients.prices import FakePriceClient, HttpPriceClient
from app.clients.production import FakeProductionClient, HttpProductionClient
from app.core.auth import CurrentUser, get_current_user
from app.crud.payment_crud import PaymentCrud
from app.core.config import get_settings
from app.messaging.producer import RabbitMQEventPublisher
from app.services.payment_service import PaymentService


def build_payment_service(access_token: str | None = None) -> PaymentService:
    settings = get_settings()
    use_fakes = settings.use_fake_clients or access_token is None
    return PaymentService(
        crud=PaymentCrud(),
        contracts=FakeContractClient() if use_fakes else HttpContractClient(settings.contract_service_url, access_token, settings.upstream_timeout_seconds),
        production=FakeProductionClient() if use_fakes else HttpProductionClient(settings.production_service_url, access_token, settings.upstream_timeout_seconds),
        prices=FakePriceClient() if use_fakes else HttpPriceClient(settings.price_service_url, access_token, settings.upstream_timeout_seconds),
        events=RabbitMQEventPublisher(settings.rabbitmq_url, settings.rabbitmq_enabled),
    )


def get_payment_service(current_user: CurrentUser = Depends(get_current_user)) -> PaymentService:
    return build_payment_service(current_user.access_token)
