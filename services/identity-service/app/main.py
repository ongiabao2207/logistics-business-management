from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.security import public_jwk
from app.routers.account_router import router as account_router
from app.routers.auth_router import router as auth_router
from app.routers.role_router import router as role_router
from app.services.identity_service import IdentityServiceError


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title=settings.app_name)
    application.include_router(auth_router)
    application.include_router(account_router)
    application.include_router(role_router)

    @application.exception_handler(IdentityServiceError)
    async def handle_identity_error(_request: Request, exc: IdentityServiceError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @application.get("/api/v1/health", tags=["health"])
    def health_check() -> dict[str, str]:
        return {"status": "ok", "service": "identity-service"}

    @application.get("/.well-known/jwks.json", tags=["authentication"])
    def jwks() -> dict[str, list[dict]]:
        return {"keys": [public_jwk(settings)]}

    return application


app = create_app()
