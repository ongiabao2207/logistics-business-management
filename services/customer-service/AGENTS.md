# Customer Service

## Scope

Customer Service owns:

- customer company profile;
- customer representative/contact information;
- customer status.

Do not move business logic owned by Contract, Price, Payment, Approval,
Notification, Audit Log, or other services into Customer Service.

## Architecture

Follow the project layering:

Request -> Router -> Service -> CRUD -> Model (DB) -> Schema -> Response

Customer-specific rules:

- HTTP handling belongs in `app/routers/`.
- Business rules belong in `app/services/`.
- Persistence belongs in `app/crud/`.
- SQLAlchemy entities belong in `app/models/`.
- Pydantic contracts belong in `app/schemas/`.

Follow all additional rules from the root `AGENTS.md`.

## Owned Data

Customer Service owns its PostgreSQL data.

Other services may store logical customer IDs, but must retrieve customer
details through Customer Service APIs.

Never directly access another service's database or Redis cache.
