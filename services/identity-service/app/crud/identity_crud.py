from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.identity_model import Account, Role


class IdentityCrud:
    def get_role(self, db: Session, role_id: int) -> Role | None:
        return db.get(Role, role_id)

    def list_roles(self, db: Session) -> list[Role]:
        return list(db.scalars(select(Role).order_by(Role.id)))

    def get_account(self, db: Session, account_id: int) -> Account | None:
        return db.get(Account, account_id)

    def get_account_by_username(self, db: Session, username: str) -> Account | None:
        return db.scalar(select(Account).where(Account.username == username.lower()))

    def get_account_by_email(self, db: Session, email: str) -> Account | None:
        return db.scalar(select(Account).where(Account.email == email.lower()))

    def list_accounts(self, db: Session) -> list[Account]:
        return list(db.scalars(select(Account).order_by(Account.id)))

    def create_account(self, db: Session, account: Account) -> Account:
        db.add(account)
        db.commit()
        db.refresh(account)
        return account

    def save_account(self, db: Session, account: Account) -> Account:
        db.add(account)
        db.commit()
        db.refresh(account)
        return account
