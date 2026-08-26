from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.clients.contract_client import ContractClient, FakeContractClient, HttpContractClient
from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.production_schema import (
    OverlapCheckRequest, OverlapCheckResponse, ProductionDetailsReplace,
    ProductionPeriodCreate, ProductionPeriodDetailResponse, ProductionPeriodResponse,
)
from app.services.production_service import ProductionService

router = APIRouter(prefix="/api/v1/production-periods", tags=["production-periods"])


def get_contract_client() -> ContractClient:
    settings = get_settings()
    if settings.contract_client_mode.lower() == "http":
        return HttpContractClient(settings.contract_service_url)
    return FakeContractClient()


def get_production_service(db: Session = Depends(get_db), contract_client: ContractClient = Depends(get_contract_client)) -> ProductionService:
    return ProductionService(db, contract_client)


def current_actor_id(x_user_id: Annotated[str | None, Header()] = None) -> str:
    """Temporary gateway-authenticated identity header until Identity Service is integrated."""
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="X-User-Id header is required")
    return x_user_id


@router.post("/check-overlap", response_model=OverlapCheckResponse)
def check_overlap(payload: OverlapCheckRequest, service: ProductionService = Depends(get_production_service)) -> OverlapCheckResponse:
    conflicts = service.check_overlap(payload.customer_id, payload.contract_id, payload.from_date, payload.to_date)
    return OverlapCheckResponse(overlaps=bool(conflicts), conflicting_period_ids=conflicts)


@router.post("/draft", response_model=ProductionPeriodResponse, status_code=status.HTTP_201_CREATED)
def create_draft(payload: ProductionPeriodCreate, actor_id: str = Depends(current_actor_id), service: ProductionService = Depends(get_production_service)) -> ProductionPeriodResponse:
    return service.create_draft(payload, actor_id)


@router.get("", response_model=list[ProductionPeriodResponse])
def list_production_periods(customer_id: str | None = Query(default=None), contract_id: str | None = Query(default=None), service: ProductionService = Depends(get_production_service)) -> list[ProductionPeriodResponse]:
    return service.list_periods(customer_id, contract_id)


@router.get("/{period_id}", response_model=ProductionPeriodDetailResponse)
def get_production_period(period_id: int, service: ProductionService = Depends(get_production_service)) -> ProductionPeriodDetailResponse:
    period = service.get_period(period_id)
    return ProductionPeriodDetailResponse(**ProductionPeriodResponse.model_validate(period).model_dump(), totals=service.totals(period))


@router.put("/{period_id}/details", response_model=ProductionPeriodDetailResponse)
def replace_production_details(period_id: int, payload: ProductionDetailsReplace, service: ProductionService = Depends(get_production_service)) -> ProductionPeriodDetailResponse:
    period = service.replace_details(period_id, payload.details)
    return ProductionPeriodDetailResponse(**ProductionPeriodResponse.model_validate(period).model_dump(), totals=service.totals(period))


@router.post("/{period_id}/lock", response_model=ProductionPeriodResponse)
def lock_production_period(period_id: int, actor_id: str = Depends(current_actor_id), service: ProductionService = Depends(get_production_service)) -> ProductionPeriodResponse:
    return service.lock_period(period_id, actor_id)
