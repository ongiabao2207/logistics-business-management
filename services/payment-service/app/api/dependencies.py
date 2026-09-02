from functools import lru_cache

from app.clients.contracts import FakeContractClient
from app.clients.prices import FakePriceClient
from app.clients.production import FakeProductionClient
from app.crud.payment_crud import PaymentCrud
from app.core.config import get_settings
from app.messaging.producer import RabbitMQEventPublisher
from app.services.payment_service import PaymentService


@lru_cache
def get_payment_service() -> PaymentService:
    return PaymentService(
        crud=PaymentCrud(),
        contracts=FakeContractClient(),
        production=FakeProductionClient(),
        prices=FakePriceClient(),
        events=RabbitMQEventPublisher(get_settings().rabbitmq_url, get_settings().rabbitmq_enabled),
    )
