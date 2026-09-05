# Production–Contract API integration

Production Service never reads Contract Service data directly from PostgreSQL.
It validates a production period through this Contract Service API:

`GET /api/v1/contracts/{contract_id}/validate-services?fromDate=YYYY-MM-DD&toDate=YYYY-MM-DD`

The endpoint is available to `ROLE_OPERATION`. It returns the contract's
`customer_id` and the service identifiers that may be recorded for that period.
It rejects a contract that does not exist, is not `ACTIVE`, or whose validity
period does not contain the requested production period.

The production-period form reads `GET /api/v1/contracts` and then the selected
contract detail through HTTP APIs. It uses only contracts with status `ACTIVE`.
