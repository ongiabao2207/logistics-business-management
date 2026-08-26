from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.price_schema import (
    ActiveServicePriceResponse,
    PriceListCreate,
    PriceListResponse,
    PriceListUpdate,
    ServiceCreate,
    ServiceResponse,
)
from app.services import price_service


router = APIRouter(prefix="/api/v1")


@router.post("/services", response_model=ServiceResponse, status_code=201)
def create_service(payload: ServiceCreate, db: Session = Depends(get_db)):
    return price_service.create_service(db, payload)


@router.get("/services", response_model=list[ServiceResponse])
def list_services(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return price_service.list_services(db, offset, limit)


@router.delete("/services/{service_id}", status_code=204)
def deactivate_service(service_id: int, db: Session = Depends(get_db)) -> None:
    price_service.deactivate_service(db, service_id)


@router.post("/price-lists", response_model=PriceListResponse, status_code=201)
def create_price_list(payload: PriceListCreate, db: Session = Depends(get_db)):
    return price_service.create_price_list(db, payload)


@router.get("/price-lists", response_model=list[PriceListResponse])
def list_price_lists(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return price_service.list_price_lists(db, offset, limit)


@router.get(
    "/price-lists/active/services/{service_id}",
    response_model=ActiveServicePriceResponse,
)
def get_active_service_price(service_id: int, db: Session = Depends(get_db)):
    return price_service.get_active_service_price(db, service_id)


@router.get("/price-lists/{price_list_id}", response_model=PriceListResponse)
def get_price_list(price_list_id: str, db: Session = Depends(get_db)):
    return price_service.get_price_list(db, price_list_id)


@router.patch("/price-lists/{price_list_id}", response_model=PriceListResponse)
def update_price_list(
    price_list_id: str, payload: PriceListUpdate, db: Session = Depends(get_db)
):
    return price_service.update_price_list(db, price_list_id, payload)


@router.delete("/price-lists/{price_list_id}", status_code=204)
def delete_price_list(price_list_id: str, db: Session = Depends(get_db)) -> None:
    price_service.delete_price_list(db, price_list_id)


@router.post("/price-lists/{price_list_id}/submit", response_model=PriceListResponse)
def submit_price_list(price_list_id: str, db: Session = Depends(get_db)):
    return price_service.submit_price_list(db, price_list_id)
