import os

os.environ["CUSTOMER_SERVICE_DATABASE_URL"] = "sqlite://"

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.customer_model import CustomerInfo


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db() -> Session:
    with TestingSession() as session:
        yield session


@pytest.fixture
def customer_factory():
    def create(
        customer_id: str = "KH0001",
        company_name: str = "Samsung Electronics HCMC",
        status: str = "ACTIVE",
    ) -> CustomerInfo:
        with TestingSession() as session:
            customer = CustomerInfo(
                id=customer_id,
                company_name=company_name,
                company_type="Logistics",
                tax_code="0312345678",
                address="Ho Chi Minh City",
                contact_name="Nguyen Van An",
                contact_email="an.nguyen@samsung.example",
                contact_phone="0901234567",
                status=status,
            )
            session.add(customer)
            session.commit()
            session.refresh(customer)
            session.expunge(customer)
            return customer

    return create


@pytest.fixture
def client():
    pytest.importorskip("httpx")
    pytest.importorskip("jwt")

    from fastapi import Request
    from fastapi.testclient import TestClient

    from app.core.auth import CurrentUser, get_current_user
    from app.db.session import get_db
    from app.main import app

    def override_get_db():
        with TestingSession() as session:
            yield session

    def override_current_user(_request: Request) -> CurrentUser:
        return CurrentUser(
            account_id="sale-1",
            username="sale_user",
            role="ROLE_SALE",
            access_token="test-token",
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_current_user
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
