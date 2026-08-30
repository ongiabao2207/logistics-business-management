import os

os.environ["PRICE_DATABASE_URL"] = "sqlite://"

import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.core.auth import CurrentUser, get_current_user
from app.main import app
from app.models.price_model import PriceList, Service


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
def client():
    def override_get_db():
        with TestingSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    def override_current_user(request: Request) -> CurrentUser:
        role = "ROLE_DIRECTOR" if request.url.path.endswith(("/approve", "/reject")) else "ROLE_SALE"
        return CurrentUser(
            account_id="test-user-1",
            username="test_user",
            role=role,
            access_token="test-token",
        )

    app.dependency_overrides[get_current_user] = override_current_user
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def service_factory():
    def create(name: str = "Lưu kho") -> Service:
        with TestingSession() as session:
            entity = Service(
                name=name,
                description=f"Mô tả {name}",
                is_active=True,
                unit="Ngày",
            )
            session.add(entity)
            session.commit()
            session.refresh(entity)
            session.expunge(entity)
            return entity

    return create


@pytest.fixture
def set_price_list_status():
    def set_status(price_list_id: str, status: str) -> None:
        with TestingSession() as session:
            entity = session.get(PriceList, price_list_id)
            entity.status = status
            session.commit()

    return set_status
