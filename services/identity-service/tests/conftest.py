import os
import tempfile
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


key_dir = Path(tempfile.mkdtemp(prefix="identity-test-keys-"))
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
private_path = key_dir / "private.pem"
public_path = key_dir / "public.pem"
private_path.write_bytes(
    private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
)
public_path.write_bytes(
    private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
)

os.environ["IDENTITY_DATABASE_URL"] = "sqlite://"
os.environ["IDENTITY_JWT_PRIVATE_KEY_PATH"] = str(private_path)
os.environ["IDENTITY_JWT_PUBLIC_KEY_PATH"] = str(public_path)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.identity_model import Account, Role


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.create_all(engine)
    with TestingSession() as db:
        roles = [
            Role(name="ROLE_SALE", description="Sales"),
            Role(name="ROLE_OPERATION", description="Operations"),
            Role(name="ROLE_ACCOUNTANT", description="Accounting"),
            Role(name="ROLE_LEGAL", description="Legal"),
            Role(name="ROLE_DIRECTOR", description="Director"),
            Role(name="ROLE_ADMIN", description="Administrator"),
        ]
        db.add_all(roles)
        db.flush()
        db.add_all(
            [
                Account(
                    username="admin",
                    email="admin@abc.com",
                    password_hash=hash_password("AdminPassword123!"),
                    role_id=roles[-1].id,
                ),
                Account(
                    username="sale_user",
                    email="sale@abc.com",
                    password_hash=hash_password("SalePassword123!"),
                    role_id=roles[0].id,
                ),
                Account(
                    username="inactive_user",
                    email="inactive@abc.com",
                    password_hash=hash_password("InactivePassword123!"),
                    role_id=roles[0].id,
                    is_active=False,
                ),
            ]
        )
        db.commit()
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def client():
    def override_get_db():
        with TestingSession() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def db() -> Session:
    with TestingSession() as session:
        yield session


@pytest.fixture
def login(client):
    def perform(username: str = "admin", password: str = "AdminPassword123!") -> str:
        response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
        assert response.status_code == 200
        return response.json()["access_token"]

    return perform
