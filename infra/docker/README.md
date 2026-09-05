# Shared Docker environment

This directory contains the single Docker Compose file for the services that
are currently implemented. Run all commands from the repository root.

## Start the environment

```bash
docker compose -f infra/docker/docker-compose.yml up --build -d
docker compose -f infra/docker/docker-compose.yml ps
```

Traefik is available at `http://localhost:8088` and its development dashboard
is at `http://localhost:8089` by default. Set `TRAEFIK_HTTP_PORT=80` if you
want the gateway on `http://localhost`.

## Routes and ports

| Component | Traefik route | Direct host port |
| --- | --- | --- |
| Contract Service | `http://contract.localhost` or `/contracts` | `8001` |
| Price Service | `http://price.localhost` | `8002` |
| Production Service | `http://production.localhost` | `8003` |
| Payment Service | `http://payment.localhost` | `8004` |
| Notification Service | `http://notification.localhost` | `8007` |
| RabbitMQ management | n/a | `15672` |
| Contract PostgreSQL | n/a | `5432` |
| Price PostgreSQL | n/a | `5433` |
| Production PostgreSQL | n/a | `5434` |
| Payment PostgreSQL | n/a | `5435` |
| Notification PostgreSQL | n/a | `5438` |

The direct ports are bound to `127.0.0.1` for local development. Container-to-
container connections use service names and container ports instead of host
ports.

Examples:

```bash
curl http://contract.localhost/health
curl http://price.localhost/api/v1/health
curl http://production.localhost/health
curl http://payment.localhost/health
```

## Network and database isolation

Traefik and the API containers share `lbm-gateway`. Each API also joins only
its own database network. Database containers never join the gateway network,
so one service cannot reach another service's PostgreSQL container through the
Compose network topology.

Named volumes preserve local PostgreSQL data between restarts. To stop the
environment without deleting data:

```bash
docker compose -f infra/docker/docker-compose.yml down
```

Only use `down --volumes` when the local databases may be permanently reset.

## Port overrides

Every published port can be overridden without editing the Compose file. For
example, in PowerShell:

```powershell
$env:TRAEFIK_HTTP_PORT = "8088"
$env:CONTRACT_DB_PORT = "15432"
docker compose -f infra/docker/docker-compose.yml up --build -d
```

Development credentials also have environment-variable overrides. Do not put
real secrets in this Compose file or commit a `.env` file.
