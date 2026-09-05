# Logistics Business Management System

Microservices-based Logistics Business Management System for managing customers, contracts, service pricing, production usage, payment statements, identity/access control, and notifications.

## Architecture

- Backend services are built with FastAPI.
- Each business service owns its own PostgreSQL database.
- Services communicate synchronously through HTTP APIs.
- Business events and side effects are published through RabbitMQ.
- Redis is used for cache or ephemeral state where justified.
- Traefik is the local API gateway in Docker Compose.
- The frontend is a React + Vite single-page application.

## Designed Services

The repository currently contains 7 runnable backend services. Approval is handled directly inside the owning business services in the current implementation, and Audit Log is documented as a designed boundary but does not yet have a standalone runnable service.

| Service | Main responsibility | Direct host port | Main routes |
| --- | --- | --- | --- |
| Contract Service | Owns contracts, contract service lines, contract appendices, contract lifecycle, and direct review/status transitions. | `8001` | `/api/v1/contracts`, `/api/v1/health` |
| Price Service | Owns the service catalog, price lists, price-list lifecycle, versioning, and effective price lookup. | `8002` | `/api/v1/services`, `/api/v1/price-lists`, `/api/v1/health` |
| Production Service | Owns production periods, actual service usage, usage detail updates, overlap checks, and period locking. | `8003` | `/api/v1/production-periods`, `/health` |
| Payment Service | Owns payment previews, payment statements, calculated totals, unit price snapshots, payment status, and adjustments. | `8004` | `/api/v1/payments`, `/health` |
| Identity Service | Owns accounts, roles, authentication, JWT issuance, and JWKS publishing. | `8005` | `/api/v1/auth`, `/api/v1/accounts`, `/api/v1/roles`, `/.well-known/jwks.json`, `/api/v1/health` |
| Customer Service | Owns customer profiles, customer contact/representative data, customer status, and customer lookup for other services. | `8006` | `/api/v1/customers`, `/api/v1/health` |
| Notification Service | Consumes asynchronous RabbitMQ events, stores user notifications, lists notifications, and marks notifications as read. | `8007` | `/api/v1/notifications`, `/health` |
| Approval Service | Designed boundary for workflow and E-Sign ownership in early architecture documents. Current implementation uses direct approval inside owning services instead. | Not assigned | Not runnable as a standalone service |
| Audit Log Service | Designed boundary for immutable business/action audit events consumed from RabbitMQ. | Not assigned | Not implemented as a standalone service |

## Local Infrastructure Ports

| Component | Port | Notes |
| --- | --- | --- |
| Traefik gateway | `8088` | Local gateway at `http://localhost:8088` |
| Traefik dashboard | `8089` | Development dashboard |
| RabbitMQ AMQP | `5672` | Async messaging |
| RabbitMQ management | `15672` | Management UI |
| Redis | `6379` | Cache/ephemeral state |
| Contract PostgreSQL | `5432` | Contract Service database |
| Price PostgreSQL | `5433` | Price Service database |
| Production PostgreSQL | `5434` | Production Service database |
| Payment PostgreSQL | `5435` | Payment Service database |
| Identity PostgreSQL | `5436` | Identity Service database |
| Customer PostgreSQL | `5437` | Customer Service database |
| Notification PostgreSQL | `5438` | Notification Service database |

## Tech Stack

### Backend

- Python `>=3.11`
- FastAPI
- Uvicorn
- Pydantic and Pydantic Settings
- SQLAlchemy
- PostgreSQL 16
- psycopg 3
- Alembic for services that use database migrations
- HTTPX for service-to-service HTTP clients
- PyJWT with crypto support for JWT validation/signing
- pwdlib with Argon2 for password hashing in Identity Service
- pika for RabbitMQ producers/consumers
- Redis for cache/ephemeral state
- Pytest, pytest-asyncio, and pytest-cov where configured

### Frontend

- React 18
- Vite 5
- Node.js and npm
- React Router
- TanStack Query
- Axios
- lucide-react
- ESLint
- CSS
- JavaScript ES modules

### Infrastructure

- Docker and Docker Compose
- Traefik
- RabbitMQ with management UI
- Redis
- PostgreSQL per service

## Start The Backend

Run commands from the repository root.

### 1. Prepare Identity JWT keys

Identity Service expects JWT key files under `services/identity-service/secrets/`. If they do not exist yet, create them:

```powershell
New-Item -ItemType Directory -Force services/identity-service/secrets

openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:3072 -out services/identity-service/secrets/jwt-private.pem
openssl rsa -pubout -in services/identity-service/secrets/jwt-private.pem -out services/identity-service/secrets/jwt-public.pem
```

Do not commit the `secrets/` directory.

### 2. Start all backend services

```powershell
docker compose -f infra/docker/docker-compose.yml up --build -d
docker compose -f infra/docker/docker-compose.yml ps
```

### 3. Check service health

```powershell
Invoke-RestMethod http://localhost:8001/api/v1/health
Invoke-RestMethod http://localhost:8002/api/v1/health
Invoke-RestMethod http://localhost:8003/health
Invoke-RestMethod http://localhost:8004/health
Invoke-RestMethod http://localhost:8005/api/v1/health
Invoke-RestMethod http://localhost:8006/api/v1/health
Invoke-RestMethod http://localhost:8007/health
```

Swagger/OpenAPI documentation is available at:

```text
http://localhost:8001/docs
http://localhost:8002/docs
http://localhost:8003/docs
http://localhost:8004/docs
http://localhost:8005/docs
http://localhost:8006/docs
http://localhost:8007/docs
```

### 4. Optional: seed demo data

After containers are running, seed payment integration sample data:

```powershell
powershell -ExecutionPolicy Bypass -File .\infra\docker\seed-payment-integration.ps1
```

To create sample Identity accounts, pass the sample password through an environment variable:

```powershell
docker compose -f infra/docker/docker-compose.yml exec `
  -e IDENTITY_SAMPLE_ACCOUNT_PASSWORD="<your-secure-password>" `
  identity-service python -m app.scripts.seed_sample_data
```

## Start The Frontend

Open a second terminal and run:

```powershell
cd frontend
npm install
npm run dev
```

The Vite development server runs at:

```text
http://localhost:5173
```

By default, `frontend/.env.example` leaves `VITE_API_BASE_URL` empty. In development, Vite proxies `/api/v1/...` requests to the correct backend ports configured in `frontend/vite.config.js`.

## Stop The Environment

Stop containers without deleting database volumes:

```powershell
docker compose -f infra/docker/docker-compose.yml down
```

Only use `down --volumes` when you intentionally want to delete local PostgreSQL/RabbitMQ/Redis data.

---

# Hệ Thống Quản Lý Kinh Doanh Logistics

Đồ án Logistics Business Management System được xây dựng theo kiến trúc microservices để quản lý khách hàng, hợp đồng, bảng giá dịch vụ, sản lượng thực tế, bảng thanh toán, định danh/phân quyền và thông báo.

## Kiến Trúc

- Backend services được xây dựng bằng FastAPI.
- Mỗi business service sở hữu PostgreSQL database riêng.
- Các service giao tiếp đồng bộ qua HTTP API.
- Business events và side effects được phát qua RabbitMQ.
- Redis chỉ dùng cho cache hoặc trạng thái tạm thời khi phù hợp.
- Traefik là API gateway local trong Docker Compose.
- Frontend là ứng dụng React + Vite.

## Các Service Đã Thiết Kế

Repository hiện có 7 backend service chạy được. Trong implementation hiện tại, phê duyệt được xử lý trực tiếp bên trong service sở hữu nghiệp vụ; Audit Log đã được tách boundary trong tài liệu thiết kế nhưng chưa có standalone runnable service.

| Service | Vai trò chính | Host port trực tiếp | Route chính |
| --- | --- | --- | --- |
| Contract Service | Quản lý hợp đồng, dòng dịch vụ trong hợp đồng, phụ lục hợp đồng, vòng đời hợp đồng và các bước review/status trực tiếp. | `8001` | `/api/v1/contracts`, `/api/v1/health` |
| Price Service | Quản lý danh mục dịch vụ, bảng giá, vòng đời bảng giá, versioning và tra cứu đơn giá hiệu lực. | `8002` | `/api/v1/services`, `/api/v1/price-lists`, `/api/v1/health` |
| Production Service | Quản lý kỳ sản lượng, sản lượng thực tế, chi tiết sử dụng dịch vụ, kiểm tra trùng kỳ và khóa kỳ sản lượng. | `8003` | `/api/v1/production-periods`, `/health` |
| Payment Service | Quản lý preview thanh toán, bảng thanh toán, tổng tiền tính toán, snapshot đơn giá, trạng thái thanh toán và điều chỉnh. | `8004` | `/api/v1/payments`, `/health` |
| Identity Service | Quản lý tài khoản, role, đăng nhập, phát hành JWT và public JWKS. | `8005` | `/api/v1/auth`, `/api/v1/accounts`, `/api/v1/roles`, `/.well-known/jwks.json`, `/api/v1/health` |
| Customer Service | Quản lý hồ sơ khách hàng, thông tin liên hệ/người đại diện, trạng thái khách hàng và tra cứu khách hàng cho service khác. | `8006` | `/api/v1/customers`, `/api/v1/health` |
| Notification Service | Consume event bất đồng bộ từ RabbitMQ, lưu thông báo người dùng, xem danh sách thông báo và đánh dấu đã đọc. | `8007` | `/api/v1/notifications`, `/health` |
| Approval Service | Boundary thiết kế cho workflow phê duyệt và E-Sign trong tài liệu kiến trúc ban đầu. Hiện tại chưa chạy riêng vì approval đang nằm trong owning services. | Chưa gán | Chưa có standalone service |
| Audit Log Service | Boundary thiết kế cho audit event bất biến, consume từ RabbitMQ. | Chưa gán | Chưa có standalone service |

## Port Hạ Tầng Local

| Thành phần | Port | Ghi chú |
| --- | --- | --- |
| Traefik gateway | `8088` | Gateway local tại `http://localhost:8088` |
| Traefik dashboard | `8089` | Dashboard development |
| RabbitMQ AMQP | `5672` | Messaging bất đồng bộ |
| RabbitMQ management | `15672` | Management UI |
| Redis | `6379` | Cache/trạng thái tạm thời |
| Contract PostgreSQL | `5432` | Database của Contract Service |
| Price PostgreSQL | `5433` | Database của Price Service |
| Production PostgreSQL | `5434` | Database của Production Service |
| Payment PostgreSQL | `5435` | Database của Payment Service |
| Identity PostgreSQL | `5436` | Database của Identity Service |
| Customer PostgreSQL | `5437` | Database của Customer Service |
| Notification PostgreSQL | `5438` | Database của Notification Service |

## Tech Stack

### Backend

- Python `>=3.11`
- FastAPI
- Uvicorn
- Pydantic và Pydantic Settings
- SQLAlchemy
- PostgreSQL 16
- psycopg 3
- Alembic cho các service có migration
- HTTPX cho HTTP client giữa các service
- PyJWT với crypto support để ký/xác thực JWT
- pwdlib với Argon2 để hash password trong Identity Service
- pika cho RabbitMQ producer/consumer
- Redis cho cache/trạng thái tạm thời
- Pytest, pytest-asyncio và pytest-cov ở các service có cấu hình

### Frontend

- React 18
- Vite 5
- Node.js và npm
- React Router
- TanStack Query
- Axios
- lucide-react
- ESLint
- CSS
- JavaScript ES modules

### Infrastructure

- Docker và Docker Compose
- Traefik
- RabbitMQ kèm management UI
- Redis
- PostgreSQL riêng cho từng service

## Khởi Động Backend

Chạy lệnh từ thư mục gốc repository.

### 1. Chuẩn bị JWT keys cho Identity Service

Identity Service cần JWT key files trong `services/identity-service/secrets/`. Nếu chưa có, tạo bằng:

```powershell
New-Item -ItemType Directory -Force services/identity-service/secrets

openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:3072 -out services/identity-service/secrets/jwt-private.pem
openssl rsa -pubout -in services/identity-service/secrets/jwt-private.pem -out services/identity-service/secrets/jwt-public.pem
```

Không commit thư mục `secrets/`.

### 2. Chạy toàn bộ backend services

```powershell
docker compose -f infra/docker/docker-compose.yml up --build -d
docker compose -f infra/docker/docker-compose.yml ps
```

### 3. Kiểm tra health check

```powershell
Invoke-RestMethod http://localhost:8001/api/v1/health
Invoke-RestMethod http://localhost:8002/api/v1/health
Invoke-RestMethod http://localhost:8003/health
Invoke-RestMethod http://localhost:8004/health
Invoke-RestMethod http://localhost:8005/api/v1/health
Invoke-RestMethod http://localhost:8006/api/v1/health
Invoke-RestMethod http://localhost:8007/health
```

Swagger/OpenAPI documentation:

```text
http://localhost:8001/docs
http://localhost:8002/docs
http://localhost:8003/docs
http://localhost:8004/docs
http://localhost:8005/docs
http://localhost:8006/docs
http://localhost:8007/docs
```

### 4. Tùy chọn: seed dữ liệu demo

Sau khi container đã chạy, seed dữ liệu mẫu cho luồng payment integration:

```powershell
powershell -ExecutionPolicy Bypass -File .\infra\docker\seed-payment-integration.ps1
```

Để tạo sample account cho Identity Service, truyền password qua environment variable:

```powershell
docker compose -f infra/docker/docker-compose.yml exec `
  -e IDENTITY_SAMPLE_ACCOUNT_PASSWORD="<your-secure-password>" `
  identity-service python -m app.scripts.seed_sample_data
```

## Khởi Động Frontend

Mở terminal thứ hai và chạy:

```powershell
cd frontend
npm install
npm run dev
```

Vite development server chạy tại:

```text
http://localhost:5173
```

Mặc định, `frontend/.env.example` để trống `VITE_API_BASE_URL`. Khi chạy development, Vite sẽ proxy các request `/api/v1/...` đến đúng backend port được cấu hình trong `frontend/vite.config.js`.

## Dừng Môi Trường

Dừng container nhưng giữ lại database volumes:

```powershell
docker compose -f infra/docker/docker-compose.yml down
```

Chỉ dùng `down --volumes` khi bạn thật sự muốn xóa dữ liệu PostgreSQL/RabbitMQ/Redis local.
