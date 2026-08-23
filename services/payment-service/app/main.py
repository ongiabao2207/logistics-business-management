from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.payments import router as payment_router
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine
import app.models  # noqa: F401

settings = get_settings()

@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(payment_router, prefix=settings.api_prefix)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "service": "payment"}
