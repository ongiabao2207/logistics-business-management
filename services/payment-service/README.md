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

`POST /api/v1/payments` saves the first draft. Each generated line keeps both
the source `confirmed_quantity` received from Production Service and the
editable `billing_quantity` used for payment calculation.

Payment IDs use the payment-period year and a three-digit yearly sequence:
`TT-2026-001`, `TT-2026-002`, through `TT-2026-999`. Each new year starts again
at `001`. A dedicated, row-locked sequence table is used instead of counting
payments, so deleted records do not cause number reuse and concurrent creates
do not normally allocate the same ID.

To save a controlled `DRAFT` edit, `PATCH /api/v1/payments/{payment_id}` requires
a reason and accepts an optional global `tax_rate` and/or line actions. A line
accepts only `service_id`, `billing_quantity`, an optional line-specific
`tax_rate`, and `remove`. The API rejects source fields such as
`confirmed_quantity`, `description`, and `unit_price_snapshot`.

```json
{
  "reason": "Exclude two containers without sufficient billing documents",
  "tax_rate": 0.08,
  "lines": [
    {
      "service_id": "CONTAINER_20",
      "billing_quantity": 10
    }
  ]
}
```

To remove an existing line:

```json
{
  "reason": "Remove an ineligible service line",
  "lines": [
    {
      "service_id": "CONTAINER_20",
      "remove": true
    }
  ]
}
```

A new line is accepted only when Production Service returns confirmed or
reconciled production for that service and period, and Price Service returns an
effective price. At least one line must remain.

The controlled quantities satisfy
`0 < billing_quantity <= confirmed_quantity`; tax rates are between `0` and
`1`. Payment edits retain the stored unit-price snapshot instead of resolving
a newer price. Every changed line creates an adjustment history entry with the
reason, confirmed quantity, previous/new billing quantity, previous/new tax,
and monetary difference.

Only `DRAFT` payments can be updated through PATCH. The UI action "save and
submit" should save the draft first and then call
`POST /api/v1/payments/{payment_id}/submit`.

Approval Service owns the reviewer's revision request, including its reason,
detail, requester, and timestamp. After Approval Service marks a payment as
`REVISION_REQUESTED`, the accountant applies the requested correction through
`POST /api/v1/payments/{payment_id}/adjustments`:

```json
{
  "revision_request_id": "approval-revision-001",
  "adjustment_note": "Adjusted DV001 using reconciliation records",
  "lines": [
    {
      "service_id": "CONTAINER_20",
      "billing_quantity": 10
    }
  ]
}
```

Payment Service does not accept the reviewer's `reason_code` or `detail` in this
endpoint. Those values are read from Approval Service using
`revision_request_id`. It accepts the accountant's explanation and controlled
line changes, recalculates totals, and writes `REVISION_ADJUSTMENT` history.
The same approval revision request cannot be applied twice. Adjustments are
rejected unless the payment is `REVISION_REQUESTED`; direct PATCH remains
restricted to `DRAFT` payments.

Decimal values are serialized without trailing zeroes while remaining strings
to preserve exact monetary precision. For example, `1200000.00` is returned as
`"1200000"`, `10.0000` as `"10"`, and `0.0800` as `"0.08"`. Real fractional
values such as `10.25` are not rounded away.

## Test

```bash
pytest
```
