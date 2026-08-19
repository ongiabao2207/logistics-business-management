# Communication

Purpose: define how services communicate through HTTP, RabbitMQ, or callback/webhook.

---

## 1. Communication Types

Use synchronous HTTP when a service needs an immediate result to continue processing.

Use asynchronous RabbitMQ events for:

- Notification;
- Audit Log;
- domain events/side effects that should not block the core transaction.

Use callback/webhook for E-Sign.

---

## 2. Gateway Routing

```text
Client -> Traefik -> Target Service
```

Traefik is the API Gateway.

The gateway must not contain business logic.

The gateway must not calculate payment, approve documents, or handle contract lifecycle.

---

## 3. Synchronous HTTP Dependencies

Contract Service may call:

- Customer Service to validate/retrieve customer information;
- Price Service to reference prices when needed.

Payment Service may call:

- Contract Service to retrieve contract/effective terms;
- Production Service to retrieve usage data;
- Price Service to retrieve effective unit price.

Approval Service may call the owning service to retrieve document details for display/validation.

Contract/Payment must call Price API. They must not read Price Redis.

---

## 4. Asynchronous Events

Business services publish events to RabbitMQ for side effects.

Primary consumers:

- Notification Service;
- Audit Log Service.

Example events:

- contract submitted;
- approval requested;
- approval approved/rejected;
- payment statement created;
- E-Sign completed/failed.

Notification/Audit failure must not fail a committed core transaction.

---

## 5. E-Sign Communication

E-Sign uses async request + callback/webhook.

```text
Approval Service
  -> send E-Sign request
  -> wait for callback/webhook
  -> update E-Sign state
  -> publish event if needed
```

A successful request submission must not be treated as a successful signature.

Approval state and signing state must be clearly separated.

---

## 6. Event Reliability Rules

When publishing events:

- include entity id;
- include actor/context when available;
- include timestamp;
- use a clear event type.

Consumers must handle duplicate events caused by retry.

Audit events should prioritize completeness.

---

## 7. Forbidden Communication

Do not allow:

- service A reading service B's database;
- service A reading service B's Redis namespace;
- Contract/Payment reading Price Redis;
- Gateway accessing any database directly;
- Notification Service deciding business status;
- Audit Log Service changing business entity state.

---

## 8. Rule of Thumb

Need data immediately: call the owning service API.

Need notification/log/side effect: publish an event through RabbitMQ.

Need E-Sign integration: send an async request and update state from callback/webhook.
