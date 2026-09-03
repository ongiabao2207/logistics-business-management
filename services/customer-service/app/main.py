from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.routers.customer_router import router as customer_router
from app.services.customer_service import CustomerServiceError


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title=settings.app_name)
    application.include_router(customer_router)

    @application.exception_handler(CustomerServiceError)
    async def handle_customer_service_error(
        _request: Request, exc: CustomerServiceError
    ) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @application.get("/api/v1/health", tags=["health"])
    def health_check() -> dict[str, str]:
        return {"status": "ok", "service": "customer-service"}

    return application


app = create_app()
