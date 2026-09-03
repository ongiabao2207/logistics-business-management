# Direct Approval Model

The system intentionally uses direct approval in each owning business service. A standalone Approval Service is not used.

## Role matrix

| Role | Modules | Actions |
|---|---|---|
| `ROLE_ADMIN` | Identity | Manage user accounts |
| `ROLE_SALE` | Contracts, Prices | Create and manage records |
| `ROLE_ACCOUNTANT` | Payments, Production | Create and manage payment statements; list and view production details |
| `ROLE_OPERATION` | Production | Create and manage production periods |
| `ROLE_LEGAL`, `ROLE_DIRECTOR` | Contracts, Prices, Payments, Production | List, view detail, approve, reject |

## Review contract

Contracts, payments, and production periods expose:

```text
POST /{resource}/{id}/review
{ "decision": "APPROVE" | "REJECT" }
```

Price lists retain their existing `/approve` and `/reject` endpoints. Both `ROLE_LEGAL` and `ROLE_DIRECTOR` may call review endpoints. Review is only accepted while a record is in its reviewable state.

## Ownership

Each business service validates and persists its own status transition. Frontend permissions only control presentation and never replace backend authorization.
