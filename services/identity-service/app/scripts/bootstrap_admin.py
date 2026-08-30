import os

from app.core.security import hash_password
from app.crud.identity_crud import IdentityCrud
from app.db.session import SessionLocal
from app.models.identity_model import Account


def main() -> None:
    username = os.environ.get("IDENTITY_BOOTSTRAP_ADMIN_USERNAME", "").strip().lower()
    email = os.environ.get("IDENTITY_BOOTSTRAP_ADMIN_EMAIL", "").strip().lower()
    password = os.environ.get("IDENTITY_BOOTSTRAP_ADMIN_PASSWORD", "")
    if not username or not email or not password:
        raise SystemExit("Set IDENTITY_BOOTSTRAP_ADMIN_USERNAME, EMAIL and PASSWORD")
    if len(password) < 8:
        raise SystemExit("Bootstrap admin password must contain at least 8 characters")

    crud = IdentityCrud()
    with SessionLocal() as db:
        if crud.get_account_by_username(db, username) or crud.get_account_by_email(db, email):
            raise SystemExit("Bootstrap admin username or email already exists")
        role = next((item for item in crud.list_roles(db) if item.name == "ROLE_ADMIN"), None)
        if role is None:
            raise SystemExit("ROLE_ADMIN is missing; run migrations first")
        crud.create_account(
            db,
            Account(
                username=username,
                email=email,
                password_hash=hash_password(password),
                role_id=role.id,
            ),
        )
    print(f"Created administrator account: {username}")


if __name__ == "__main__":
    main()
