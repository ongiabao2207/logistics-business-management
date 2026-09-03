import os

from app.core.security import hash_password
from app.crud.identity_crud import IdentityCrud
from app.db.session import SessionLocal
from app.models.identity_model import Account


SAMPLE_ACCOUNTS = (
    ("sale01", "sale01@logistics.vn", "ROLE_SALE"),
    ("operation01", "operation01@logistics.vn", "ROLE_OPERATION"),
    ("accountant01", "accountant01@logistics.vn", "ROLE_ACCOUNTANT"),
    ("legal01", "legal01@logistics.vn", "ROLE_LEGAL"),
    ("director01", "director01@logistics.vn", "ROLE_DIRECTOR"),
)


def seed_sample_accounts(db, password: str) -> int:
    if len(password) < 8:
        raise ValueError("Sample account password must contain at least 8 characters")

    crud = IdentityCrud()
    roles = {role.name: role for role in crud.list_roles(db)}
    missing_roles = {role_name for _, _, role_name in SAMPLE_ACCOUNTS} - roles.keys()
    if missing_roles:
        raise RuntimeError(f"Missing roles: {', '.join(sorted(missing_roles))}")

    for username, email, role_name in SAMPLE_ACCOUNTS:
        account = crud.get_account_by_username(db, username)
        if account is None:
            db.add(
                Account(
                    username=username,
                    email=email,
                    password_hash=hash_password(password),
                    role_id=roles[role_name].id,
                )
            )
        else:
            account.email = email
            account.role_id = roles[role_name].id
            account.is_active = True
    db.commit()
    return len(SAMPLE_ACCOUNTS)


def main() -> None:
    password = os.environ.get("IDENTITY_SAMPLE_ACCOUNT_PASSWORD", "")
    if not password:
        raise SystemExit("IDENTITY_SAMPLE_ACCOUNT_PASSWORD is required")
    with SessionLocal() as db:
        count = seed_sample_accounts(db, password)
    print(f"Seeded {count} sample identity accounts")


if __name__ == "__main__":
    main()
