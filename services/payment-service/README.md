# Payment Service

FastAPI service that owns payment statements, calculation results, unit-price snapshots, adjustments, and payment lifecycle state.

During local development it uses deterministic fake Contract, Production, Price, and Approval clients because those services are not implemented yet. Replace the dependency providers with HTTP client implementations when their public APIs become available.

## Run

```bash
pip install -e '.[test]'
uvicorn app.main:app --reload
```

OpenAPI is available at `/docs`. The default local database is `payment.db`; set `PAYMENT_DATABASE_URL` for PostgreSQL.

## API

- `POST /api/v1/payments/preview`
- `POST /api/v1/payments`
- `GET /api/v1/payments`
- `GET /api/v1/payments/{payment_id}`
- `PATCH /api/v1/payments/{payment_id}`
- `POST /api/v1/payments/{payment_id}/submit`
- `POST /api/v1/payments/{payment_id}/adjustments`

## Test

```bash
pytest
```
