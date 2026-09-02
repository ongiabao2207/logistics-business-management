from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.crud.identity_crud import IdentityCrud
from app.messaging.producer import EventPublisher, NoOpEventPublisher, RabbitMQEventPublisher
from app.models.identity_model import Account
from app.schemas.identity_schema import AccountCreate, AccountUpdate, TokenResponse


def _get_event_publisher(events: EventPublisher | None = None) -> EventPublisher:
    if events is not None:
        return events
    settings = get_settings()
    if settings.rabbitmq_enabled:
        return RabbitMQEventPublisher(settings.rabbitmq_url, settings.rabbitmq_enabled)
    return NoOpEventPublisher()


class IdentityServiceError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class IdentityService:
    def __init__(self, crud: IdentityCrud | None = None, events: EventPublisher | None = None):
        self.crud = crud or IdentityCrud()
        self.events = events

    def authenticate(self, db: Session, username: str, password: str, settings: Settings) -> TokenResponse:
        account = self.crud.get_account_by_username(db, username.strip().lower())
        if account is None or not verify_password(password, account.password_hash):
            raise IdentityServiceError(401, "Invalid username or password")
        if not account.is_active:
            raise IdentityServiceError(403, "Account is inactive")
        token, expires_in = create_access_token(
            account_id=account.id,
            username=account.username,
            role=account.role.name,
            settings=settings,
        )
        return TokenResponse(access_token=token, expires_in=expires_in)

    def create_account(self, db: Session, payload: AccountCreate) -> Account:
        if self.crud.get_account_by_username(db, payload.username):
            raise IdentityServiceError(409, "Username already exists")
        if self.crud.get_account_by_email(db, str(payload.email)):
            raise IdentityServiceError(409, "Email already exists")
        role = self.crud.get_role(db, payload.role_id)
        if role is None:
            raise IdentityServiceError(400, "Role does not exist")
        account = self.crud.create_account(
            db,
            Account(
                username=payload.username,
                email=str(payload.email),
                password_hash=hash_password(payload.password),
                role_id=role.id,
            ),
        )
        _get_event_publisher(self.events).publish(
            "ACCOUNT_CREATED",
            {
                "account_id": account.id,
                "username": account.username,
                "recipient_role": "ROLE_ADMIN",
                "title": "Tài khoản mới được tạo",
                "content": f"Tài khoản {account.username} vừa được khởi tạo.",
                "reference_type": "ACCOUNT",
                "reference_id": str(account.id),
            },
        )
        return account

    def require_account(self, db: Session, account_id: int) -> Account:
        account = self.crud.get_account(db, account_id)
        if account is None:
            raise IdentityServiceError(404, "Account not found")
        return account

    def update_account(self, db: Session, account_id: int, payload: AccountUpdate) -> Account:
        account = self.require_account(db, account_id)
        if payload.email is not None and str(payload.email) != account.email:
            if self.crud.get_account_by_email(db, str(payload.email)):
                raise IdentityServiceError(409, "Email already exists")
            account.email = str(payload.email)
        return self.crud.save_account(db, account)

    def update_status(self, db: Session, account_id: int, is_active: bool, actor_id: int) -> Account:
        account = self.require_account(db, account_id)
        if account.id == actor_id and not is_active:
            raise IdentityServiceError(400, "You cannot deactivate your own account")
        account.is_active = is_active
        updated = self.crud.save_account(db, account)
        _get_event_publisher(self.events).publish(
            "ACCOUNT_STATUS_UPDATED",
            {
                "account_id": updated.id,
                "username": updated.username,
                "is_active": updated.is_active,
                "recipient_role": "ROLE_ADMIN",
                "title": "Trạng thái tài khoản thay đổi",
                "content": f"Tài khoản {updated.username} đã được {'kích hoạt' if updated.is_active else 'vô hiệu hóa'}.",
                "reference_type": "ACCOUNT",
                "reference_id": str(updated.id),
            },
        )
        return updated

    def update_role(self, db: Session, account_id: int, role_id: int) -> Account:
        account = self.require_account(db, account_id)
        role = self.crud.get_role(db, role_id)
        if role is None:
            raise IdentityServiceError(400, "Role does not exist")
        account.role_id = role.id
        updated = self.crud.save_account(db, account)
        _get_event_publisher(self.events).publish(
            "USER_ROLE_UPDATED",
            {
                "account_id": updated.id,
                "username": updated.username,
                "role_id": updated.role_id,
                "recipient_role": "ROLE_ADMIN",
                "title": "Vai trò người dùng thay đổi",
                "content": f"Vai trò của tài khoản {updated.username} đã được cập nhật.",
                "reference_type": "ACCOUNT",
                "reference_id": str(updated.id),
            },
        )
        return updated
