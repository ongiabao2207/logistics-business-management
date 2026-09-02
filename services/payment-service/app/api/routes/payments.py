from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_payment_service
from app.db.session import get_db
from app.core.auth import CurrentUser, require_roles
from app.schemas.payment_schema import (
    AdjustmentCreate,
    PaymentCreate,
    PaymentPeriodRequest,
    PaymentPreviewResponse,
    PaymentResponse,
    PaymentUpdate,
    PaymentReview,
)
from app.services.payment_service import PaymentError, PaymentService


router = APIRouter(prefix="/payments", tags=["payments"])


def call(action):
    try:
        return action()
    except PaymentError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/preview", response_model=PaymentPreviewResponse)
def preview_payment(request: PaymentPeriodRequest, _user: Annotated[CurrentUser, Depends(require_roles("ROLE_ACCOUNTANT"))], service: PaymentService = Depends(get_payment_service)):
    return call(lambda: service.preview(request))


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(request: PaymentCreate, _user: Annotated[CurrentUser, Depends(require_roles("ROLE_ACCOUNTANT"))], db: Session = Depends(get_db), service: PaymentService = Depends(get_payment_service)):
    return call(lambda: service.create(db, request))


@router.get("", response_model=list[PaymentResponse])
def list_payments(
    _user: Annotated[CurrentUser, Depends(require_roles("ROLE_ACCOUNTANT", "ROLE_DIRECTOR", "ROLE_LEGAL"))],
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    service: PaymentService = Depends(get_payment_service),
):
    return service.list(db, offset, limit)


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: str, _user: Annotated[CurrentUser, Depends(require_roles("ROLE_ACCOUNTANT", "ROLE_DIRECTOR", "ROLE_LEGAL"))], db: Session = Depends(get_db), service: PaymentService = Depends(get_payment_service)):
    return call(lambda: service.get(db, payment_id))


@router.patch("/{payment_id}", response_model=PaymentResponse)
def update_payment(payment_id: str, request: PaymentUpdate, _user: Annotated[CurrentUser, Depends(require_roles("ROLE_ACCOUNTANT"))], db: Session = Depends(get_db), service: PaymentService = Depends(get_payment_service)):
    return call(lambda: service.update_draft(db, payment_id, request))


@router.post("/{payment_id}/submit", response_model=PaymentResponse)
def submit_payment(payment_id: str, _user: Annotated[CurrentUser, Depends(require_roles("ROLE_ACCOUNTANT"))], db: Session = Depends(get_db), service: PaymentService = Depends(get_payment_service)):
    return call(lambda: service.submit(db, payment_id))


@router.post("/{payment_id}/review", response_model=PaymentResponse)
def review_payment(payment_id: str, request: PaymentReview, _user: Annotated[CurrentUser, Depends(require_roles("ROLE_LEGAL", "ROLE_DIRECTOR"))], db: Session = Depends(get_db), service: PaymentService = Depends(get_payment_service)):
    return call(lambda: service.review(db, payment_id, request.decision))


@router.post("/{payment_id}/adjustments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_adjustment(
    payment_id: str,
    request: AdjustmentCreate,
    _user: Annotated[CurrentUser, Depends(require_roles("ROLE_ACCOUNTANT"))],
    db: Session = Depends(get_db),
    service: PaymentService = Depends(get_payment_service),
):
    return call(lambda: service.adjust(db, payment_id, request))
