# Price Service

## Scope

Price Service owns:

- service catalog;
- price lists;
- price-list versions;
- effective price lookup and related business rules.

Do not move business logic owned by Contract, Payment, Approval,
Notification, Audit Log, or other services into Price Service.

## Architecture

Follow the project layering:

Request -> Router -> Service -> CRUD -> Model (DB) -> Schema -> Response

Price-specific rules:

- HTTP handling belongs in `app/routers/`.
- Business rules belong in `app/services/`.
- Persistence belongs in `app/crud/`.
- SQLAlchemy entities belong in `app/models/`.
- Pydantic contracts belong in `app/schemas/`.
- External service access belongs in `app/clients/`.
- RabbitMQ integration belongs in `app/messaging/`.

Follow all additional rules from the root `AGENTS.md`.

## Owned data

Price Service owns its PostgreSQL data and may use Redis only for its own
cache or ephemeral state under a Price-specific namespace.

Never directly access another service's database or Redis cache.

## External dependencies

Price Service may depend on:

- Approval Service for price-list approval workflows;
- RabbitMQ for asynchronous domain events.

Before using another service, inspect whether its required public contract is
implemented and usable. Use a compatible fake client when it is unavailable.

## Testing

Unit tests must isolate external dependencies. Cover effective-period overlap,
versioning, historical-price immutability, and effective-price resolution when
those features are implemented.
