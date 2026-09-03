from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine
from app.messaging.consumer import NotificationConsumer
from app.routers.notification_router import router


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    consumer = None
    if get_settings().rabbitmq_consumer_enabled:
        consumer = NotificationConsumer(get_settings().rabbitmq_url)
        consumer.start()
    yield
    if consumer:
        consumer.stop()


app = FastAPI(title="Notification Service", version="1.0.0", lifespan=lifespan)
app.include_router(router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
