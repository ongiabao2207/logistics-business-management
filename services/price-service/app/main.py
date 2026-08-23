from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.routers.price_router import router as price_router
from app.services.price_service import PriceServiceError


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title=settings.app_name)
    application.include_router(price_router)

    @application.exception_handler(PriceServiceError)
    async def handle_price_service_error(
        _request: Request, exc: PriceServiceError
    ) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @application.get("/api/v1/health", tags=["health"])
    def health_check() -> dict[str, str]:
        return {"status": "ok", "service": "price-service"}

    return application


app = create_app()
