# System Overview

Purpose: give developers/Codex/agents a compact overview of the whole system.

This document only describes the big picture. Business rules belong in `docs/requirements/`.

---

## 1. Architecture Style

The system uses a microservices architecture.

API Gateway: **Traefik**.

Traefik is responsible for:

- routing client requests to the correct service;
- handling gateway-level routing configuration;
- applying cross-cutting gateway concerns when needed.

Traefik must not contain business logic.

---

## 2. Services

The system has 9 microservices:

1. Customer Service
2. Contract Service
3. Production Service
4. Payment Service
5. Approval Service
6. Identity Service
7. Price Service
8. Notification Service
9. Audit Log Service

Confirmed decisions:

- Appendix belongs to Contract Service.
- There is no separate Appendix Service.
- E-Sign belongs to Approval Service.
- Notification and Audit Log consume asynchronous events through RabbitMQ.

---

## 3. Infrastructure

Main components:

- FastAPI for backend services.
- PostgreSQL as the source of truth.
- Redis for cache/ephemeral data.
- RabbitMQ for asynchronous events.
- JWT for authentication/authorization context.
- Docker/Kubernetes for runtime/deployment environment.
- Traefik as the API Gateway.

---

## 4. High-Level Flow

```text
Client
  -> Traefik API Gateway
  -> Business Services
  -> Own PostgreSQL database

Business Services
  -> RabbitMQ
  -> Notification Service / Audit Log Service
```

The gateway only routes requests and handles cross-cutting concerns.

Business logic must stay inside the service that owns the business capability.

---

## 5. Core Principles

- Database-per-service.
- No service may read another service's database.
- No service may read another service's Redis namespace.
- PostgreSQL is the source of truth.
- Redis is not a shared business-data store.
- Cross-service access must go through APIs or events.
- Async side effects must not break the committed core transaction if Notification/Audit fails.

---

## 6. Source Priority

If older documents conflict with confirmed decisions, confirmed decisions take priority.

Confirmed decisions include:

- Traefik is the API Gateway.
- The system has the 9 services listed above.
- Current approval flow: Legal -> Director -> Approved.
- Workflow must still be configurable by document type.
- E-Sign uses async request + callback/webhook.
- Notification/Audit use RabbitMQ async events.
- Payment stores `unit_price_snapshot`.
