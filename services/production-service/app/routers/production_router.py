from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.clients.contract_client import ContractClient, FakeContractClient, HttpContractClient
from app.core.config import get_settings
from app.core.auth import CurrentUser, get_current_user, require_roles
from app.db.session import get_db
from app.schemas.production_schema import (
    OverlapCheckRequest, OverlapCheckResponse, ProductionDetailsReplace,
    ProductionPeriodCreate, ProductionPeriodDetailResponse, ProductionPeriodResponse,
    ProductionReview,
)
from app.services.production_service import ProductionService

router = APIRouter(prefix="/api/v1/production-periods", tags=["production-periods"])


def get_contract_client(current_user: CurrentUser = Depends(get_current_user)) -> ContractClient:
    settings = get_settings()
    if settings.contract_client_mode.lower() == "http":
        return HttpContractClient(settings.contract_service_url, current_user.access_token)
    return FakeContractClient()


def get_production_service(db: Session = Depends(get_db), contract_client: ContractClient = Depends(get_contract_client)) -> ProductionService:
    return ProductionService(db, contract_client)


@router.post("/check-overlap", response_model=OverlapCheckResponse)
def check_overlap(payload: OverlapCheckRequest, _user: Annotated[CurrentUser, Depends(require_roles("ROLE_OPERATION", "ROLE_ACCOUNTANT"))], service: ProductionService = Depends(get_production_service)) -> OverlapCheckResponse:
    conflicts = service.check_overlap(payload.customer_id, payload.contract_id, payload.from_date, payload.to_date)
    return OverlapCheckResponse(overlaps=bool(conflicts), conflicting_period_ids=conflicts)


@router.post("/draft", response_model=ProductionPeriodResponse, status_code=status.HTTP_201_CREATED)
def create_draft(payload: ProductionPeriodCreate, current_user: Annotated[CurrentUser, Depends(require_roles("ROLE_OPERATION"))], service: ProductionService = Depends(get_production_service)) -> ProductionPeriodResponse:
    return service.create_draft(payload, current_user.account_id)


@router.get("", response_model=list[ProductionPeriodResponse])
def list_production_periods(_user: Annotated[CurrentUser, Depends(require_roles("ROLE_OPERATION", "ROLE_LEGAL", "ROLE_DIRECTOR"))], customer_id: str | None = Query(default=None), contract_id: str | None = Query(default=None), service: ProductionService = Depends(get_production_service)) -> list[ProductionPeriodResponse]:
    return service.list_periods(customer_id, contract_id)


@router.get("/{period_id}", response_model=ProductionPeriodDetailResponse)
def get_production_period(period_id: int, _user: Annotated[CurrentUser, Depends(require_roles("ROLE_OPERATION", "ROLE_LEGAL", "ROLE_DIRECTOR"))], service: ProductionService = Depends(get_production_service)) -> ProductionPeriodDetailResponse:
    period = service.get_period(period_id)
    return ProductionPeriodDetailResponse(**ProductionPeriodResponse.model_validate(period).model_dump(), totals=service.totals(period))


@router.put("/{period_id}/details", response_model=ProductionPeriodDetailResponse)
def replace_production_details(period_id: int, payload: ProductionDetailsReplace, _user: Annotated[CurrentUser, Depends(require_roles("ROLE_OPERATION"))], service: ProductionService = Depends(get_production_service)) -> ProductionPeriodDetailResponse:
    period = service.replace_details(period_id, payload.details)
    return ProductionPeriodDetailResponse(**ProductionPeriodResponse.model_validate(period).model_dump(), totals=service.totals(period))


@router.post("/{period_id}/lock", response_model=ProductionPeriodResponse)
def lock_production_period(period_id: int, current_user: Annotated[CurrentUser, Depends(require_roles("ROLE_OPERATION"))], service: ProductionService = Depends(get_production_service)) -> ProductionPeriodResponse:
    return service.lock_period(period_id, current_user.account_id)


@router.post("/{period_id}/review", response_model=ProductionPeriodResponse)
def review_production_period(period_id: int, payload: ProductionReview, current_user: Annotated[CurrentUser, Depends(require_roles("ROLE_LEGAL", "ROLE_DIRECTOR"))], service: ProductionService = Depends(get_production_service)) -> ProductionPeriodResponse:
    return service.review_period(period_id, payload.decision, current_user.account_id)
