# Database Ownership

Purpose: enforce database-per-service and data ownership rules.

---

## 1. Global Rules

PostgreSQL is the source of truth.

Each service owns its own database/schema/tables.

A service must not:

- read another service's database;
- write another service's database;
- create foreign keys across databases/services;
- read another service's Redis namespace.

Cross-service IDs are logical references only.

---

## 2. Customer Data

Owner: Customer Service.

Data:

- customer profile;
- customer status;
- customer-related master data.

Other services may only reference `customer_id` and call Customer API when details are needed.

---

## 3. Contract Data

Owner: Contract Service.

Data:

- contract;
- contract lifecycle state;
- contract appendix;
- contract effective period/terms.

Appendix is Contract Service data.

No other service may directly modify contract/appendix data.

---

## 4. Production Data

Owner: Production Service.

Data:

- usage/production records;
- quantity;
- usage period;
- source data for payment calculation.

Payment must retrieve production data through Production API.

---

## 5. Payment Data

Owner: Payment Service.

Data:

- payment statement;
- payment line/calculation result;
- payment lifecycle state;
- `unit_price_snapshot`.

Payment must store `unit_price_snapshot` when payment is calculated/finalized.

Payment must not depend on future changes or availability of the original price version.

---

## 6. Approval Data

Owner: Approval Service.

Data:

- workflow definition/config;
- approval request;
- approval step;
- current assignee/status;
- E-Sign request;
- E-Sign callback result/signing state.

Current workflow:

```text
Legal -> Director -> Approved
```

Workflow must still be configurable by document type.

---

## 7. Identity Data

Owner: Identity Service.

Data:

- user;
- role/permission data;
- authentication-related data;
- JWT/token-related metadata if needed.

Business services only use identity context. They do not own user identity.

---

## 8. Price Data

Owner: Price Service.

Data:

- service catalog;
- price list;
- price version;
- effective price rules.

Contract/Payment must call Price API.

Contract/Payment must not read Price database or Price Redis.

---

## 9. Notification Data

Owner: Notification Service.

Data:

- notification job/message;
- delivery status;
- retry metadata if designed.

Notification data is not the source of truth for business status.

---

## 10. Audit Log Data

Owner: Audit Log Service.

Data:

- audit event;
- actor/action/entity metadata;
- immutable audit trail.

Audit Log must not change business entity state.

---

## 11. Redis Ownership

One Redis instance/container may be shared in development.

However, Redis keys must be namespaced by service/use case.

Examples:

- `price:*` for Price cache;
- `auth:*` for Identity/JWT-related cache;
- `gateway:*` for gateway rate limit if used.

Redis is not a shared business-data store.

No service may read another service's Redis keys.

---

## 12. Snapshot Rule

Snapshots are valid when they preserve business history.

Required example:

- Payment stores `unit_price_snapshot`.

A snapshot does not mean a service may clone the full ownership of another service.
