# Service Boundaries

Purpose: define which service owns which business capability, so logic is not placed in the wrong service.

---

## 1. Customer Service

Owns:

- customer profile;
- customer status;
- customer data needed for contract/payment lookup.

Does not own:

- contract lifecycle;
- payment calculation;
- approval workflow.

---

## 2. Contract Service

Owns:

- Contract;
- Contract Appendix;
- contract lifecycle;
- contract-effective information.

Appendix belongs to Contract Service.

There is no separate Appendix Service.

Does not own:

- price catalog/version;
- payment statement;
- approval workflow state.

---

## 3. Production Service

Owns:

- production/usage records;
- usage period;
- actual service quantity used for payment calculation.

Does not own:

- contract terms;
- price version;
- payment approval/signing state.

---

## 4. Payment Service

Owns:

- payment statement;
- payment calculation result;
- `unit_price_snapshot`;
- payment lifecycle.

Payment must retrieve prices through Price API.

Payment must not read Price Redis or Price database.

Does not own:

- price master data;
- contract master data;
- production source data;
- E-Sign workflow.

---

## 5. Approval Service

Owns:

- approval workflow;
- approval step/state;
- approver assignment;
- E-Sign request state;
- E-Sign callback/webhook handling.

Current team-defined flow:

```text
Legal -> Director -> Approved
```

The architecture must still allow workflow configuration by document type.

Does not own:

- contract/payment/price document content;
- notification delivery;
- audit trail storage.

---

## 6. Identity Service

Owns:

- user identity;
- authentication;
- roles/permissions context;
- JWT-related logic.

Does not own:

- business approval rules;
- contract/payment/customer data.

---

## 7. Price Service

Owns:

- service catalog;
- price list;
- price version;
- effective price lookup.

Contract and Payment must call Price API when they need price data.

Does not own:

- payment statement;
- contract appendix lifecycle;
- production usage data.

---

## 8. Notification Service

Owns:

- asynchronous notification handling;
- notification template/channel logic if designed;
- retry/delivery status if designed.

Notification consumes events through RabbitMQ.

Does not own:

- business transaction state;
- approval decision;
- audit trail.

---

## 9. Audit Log Service

Owns:

- audit trail;
- immutable business/action log;
- event consumption for audit purposes.

Audit Log consumes events through RabbitMQ.

Does not own:

- application debug logs;
- business entity state;
- approval decision.

---

## 10. Boundary Rules

- A service only writes to its own database.
- A service must not query another service's tables/schema.
- A service must not read another service's Redis key namespace.
- Shared IDs are logical references, not cross-service foreign keys.
- If a service needs another service's data, it must call that service's API or consume a published event.
