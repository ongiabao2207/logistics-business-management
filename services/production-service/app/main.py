from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.db.schema import ensure_schema
from app.db.session import engine
from app.messaging.outbox_publisher import OutboxPublisher
from app.messaging.worker import OutboxWorker
from app.routers.production_router import router

@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_schema(engine)
    settings = get_settings()
    worker = None
    if settings.rabbitmq_enabled:
        worker = OutboxWorker(OutboxPublisher(settings.rabbitmq_url), settings.outbox_poll_interval_seconds)
        worker.start()
    yield
    if worker:
        worker.stop()

app = FastAPI(title="Production Service", version="1.0.0", lifespan=lifespan)
app.include_router(router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
