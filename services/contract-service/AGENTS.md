# Contract Service

## Scope

Contract Service owns:

- contracts;
- contract service details;
- contract appendices;
- appendix details;
- contract lifecycle business rules.

Do not move business logic owned by Customer, Price, Approval,
Notification, Audit Log, or other services into Contract Service.

## Architecture

Follow the project layering:

Request -> Router -> Service -> CRUD -> Model (DB) -> Schema -> Response

Contract-specific rules:

- HTTP handling belongs in `app/api/`.
- Business rules belong in `app/services/`.
- Persistence belongs in `app/crud/`.
- SQLAlchemy entities belong in `app/models/`.
- Pydantic contracts belong in `app/schemas/`.
- External service access belongs in `app/clients/`.
- RabbitMQ integration belongs in `app/messaging/`.

Follow all additional rules from the root `AGENTS.md`.

## Owned data

Contract Service owns its PostgreSQL data.

It may store logical references such as:

- `customer_id`;
- `service_id`;
- `price_list_id`;
- `approval_instance_id`.

These identifiers do not grant ownership of external data.

Never directly access another service's database or Redis cache.

## External dependencies

Contract Service may depend on:

- Customer Service;
- Price Service;
- Approval Service;
- RabbitMQ.

Typical responsibilities:

Customer Service:
- verify customer existence;
- verify customer active status.

Price Service:
- validate services;
- resolve applicable prices.

Approval Service:
- create and manage approval workflows.

RabbitMQ:
- publish asynchronous domain events.

## Dependency availability

Before using Customer, Price, Approval, or another service:

1. Inspect its current implementation.
2. Check whether the required endpoint/contract exists.
3. Check whether it is currently usable.
4. Do not assume availability from directory existence alone.

If available:

- use the real public API;
- access it through the appropriate HTTP client.

If unavailable:

- use a fake/test-double client;
- do not require the unavailable service to run;
- preserve the planned client interface and API contract.

Do not duplicate another service's business logic.

## Client design

Contract business logic must depend on client abstractions.

Recommended concept:

CustomerClient
- HttpCustomerClient
- FakeCustomerClient

PriceClient
- HttpPriceClient
- FakePriceClient

ApprovalClient
- HttpApprovalClient
- FakeApprovalClient

The Service layer must not depend directly on `httpx`
or another HTTP implementation.

Select the implementation using configuration
or FastAPI dependency injection.

## Fake and mock rules

Use fakes when another service is unavailable during development.

Use mocks primarily for isolated unit tests.

Fakes must:

- implement the expected client interface;
- return contract-compatible payloads;
- support relevant success and failure cases;
- use deterministic sample data where possible;
- be replaceable by the real HTTP client.

Fakes must not:

- become a production source of truth;
- access another service's database;
- reproduce another service's full business logic;
- invent a different public contract.

## RabbitMQ events

Contract Service may publish events such as:

- `ContractCreated`;
- `ContractUpdated`;
- `ContractSubmitted`;
- `ContractCancelled`;
- `AppendixCreated`;
- `AppendixUpdated`;
- `AppendixEffective`.

Notification and Audit behavior must not be implemented
inside Contract Service.

If Notification or Audit Log Service is unavailable,
do not create fake HTTP integrations for them.

Implement and test the RabbitMQ event contract instead.

## API Gateway

API Gateway is upstream of Contract Service.

Contract Service must not depend on Gateway to run.

When Gateway is unavailable:

- expose Contract APIs directly during development;
- test the service using its local URL;
- do not create a fake Gateway client.

## Confirmation gate

The root Confirmation Gate applies to every Contract Service task.

Before making any change:

1. Inspect relevant Contract Service code.
2. Read relevant business requirements.
3. Inspect required external dependencies.
4. Identify real and fake clients required.
5. Identify files expected to change.
6. Present the implementation plan.
7. Ask the user for explicit confirmation.

Do not create, edit, delete, install, migrate, commit, or otherwise modify anything before approval.

Only start implementation after the user clearly confirms.

If implementation later requires a significant change outside the approved plan, stop and request approval again.

## Testing

Unit tests should isolate external dependencies.

Cover relevant cases such as:

- customer exists and is active;
- customer does not exist;
- customer is inactive;
- service and price are valid;
- service or price is unavailable;
- approval creation succeeds;
- approval creation fails;
- invalid contract state transitions;
- invalid contract input.

Use real dependent services in integration tests when those services are available.

When they are unavailable, use the agreed fake clients.

When a real dependency becomes available, replace the fake integration without changing Contract Service business logic.