import secrets

from app.core.security import hash_password, verify_password
from app.crud.identity_crud import IdentityCrud
from app.scripts.seed_sample_data import SAMPLE_ACCOUNTS, seed_sample_accounts


def test_sample_account_seed_is_idempotent_and_uses_shared_password(db):
    sample_password = secrets.token_urlsafe(16)
    seed_sample_accounts(db, sample_password)
    sale_account = IdentityCrud().get_account_by_username(db, "sale01")
    sale_account.password_hash = hash_password("ChangedPassword123!")
    db.commit()
    seed_sample_accounts(db, sample_password)

    crud = IdentityCrud()
    for username, email, role_name in SAMPLE_ACCOUNTS:
        account = crud.get_account_by_username(db, username)
        assert account is not None
        assert account.email == email
        assert account.role.name == role_name
        assert account.is_active is True
        if username == "sale01":
            assert verify_password("ChangedPassword123!", account.password_hash)
        else:
            assert verify_password(sample_password, account.password_hash)
