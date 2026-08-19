# Project

Logistics Business Management System implemented using microservices.

## Architecture

- Backend services use FastAPI.
- Each service owns its own PostgreSQL data.
- Never access another service's database directly.
- Synchronous service-to-service communication uses HTTP APIs.
- Asynchronous business events use RabbitMQ.
- Redis is used only where caching or ephemeral state is justified.

## Layering

FastAPI services follow:

Request -> Router -> Service -> CRUD -> Model (DB) -> Schema -> Response

Rules:

- Routers handle HTTP concerns only.
- Business logic belongs in services.
- CRUD handles persistence only.
- SQLAlchemy models must not be exposed directly through APIs.
- Pydantic schemas define API input/output contracts for request validation and response serialization.
- External service calls belong in `clients/`.
- RabbitMQ producers and consumers belong in `messaging/`.

## Service ownership

Services must not access another service's PostgreSQL database or Redis cache.

For example:

Contract Service -> Price Service API -> Price cache/DB

Never:

Contract Service -> Price Service database

## External service dependencies during development

Before implementing a feature that depends on another service:

1. Inspect the dependent service under `services/`.
2. Check whether the required API or event contract is already implemented and usable.
3. Do not assume a service is available merely because its directory exists.

If the dependent service is available:

- use its documented public API through the appropriate client;
- do not duplicate its data or business logic.

If the dependent service is not implemented or not currently usable:

- do not block implementation of the current service;
- do not require the unavailable service to run locally;
- use a fake/mock/test-double implementation of the corresponding client;
- keep the fake/mock compatible with the planned public contract;
- use deterministic project sample data when appropriate.

Never implement another service's business logic inside the current service just to replace an unavailable dependency.

Mocks and fakes are temporary development/testing substitutes and must be easy to replace with real integrations later.

## Client abstraction

Business logic must depend on client abstractions rather than direct HTTP calls.

External clients should support interchangeable implementations when needed, for example:

CustomerClient
- HttpCustomerClient
- FakeCustomerClient

PriceClient
- HttpPriceClient
- FakePriceClient

ApprovalClient
- HttpApprovalClient
- FakeApprovalClient

Application code should select the appropriate implementation through configuration or dependency injection.

## Git workflow

Before adding any new features or fix bugs, always work on a new git branch.  
Never commit directly on `main`.

Branch naming convention:

- `feature/<short-description>`
- `bugfix/<short-description>`
- `refactor/<short-description>`
- `docs/<short-description>`
- `chore/<short-description>`

Examples:

- `feature/create-contract`
- `feature/payment-preview`
- `bugfix/price-overlap`

Keep branches short-lived.

Do not include unrelated changes.

## Before implementing

1. Read relevant documentation under `docs/`.
2. Read the service-level `AGENTS.md`.
3. Inspect existing implementation.
4. Identify affected service contracts.
5. Inspect whether required dependent services are currently available.
6. Decide which dependencies use real clients and which require fakes/mocks.
7. Propose a plan before making non-trivial changes.

## Testing

After changing a service:

1. Run its unit tests.
2. Run affected integration tests.
3. Run contract tests when an API/event contract changes.

Bug fixes should include a regression test.

Unit tests should isolate external service dependencies using mocks/fakes where appropriate.

Integration tests may use real dependent services when they are available.

## Cross-service changes

Do not silently change a public API or event contract.

When changing a contract:

1. Identify all consumers.
2. Update the documented contract.
3. Update affected consumers.
4. Add/update contract tests.

## Source of truth

Business requirements:  
`docs/requirements/`

Architecture:  
`docs/architecture/`

Original assignment/design:  
`docs/source/`

If implementation conflicts with documented business rules,  
report the conflict instead of silently changing the rule.

## Safety

- Never commit secrets.
- Never commit `.env`.
- Never modify production-like data destructively without explicit instruction.
- Do not push or create a pull request unless explicitly requested.