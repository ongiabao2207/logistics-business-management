# Identity Service

Hướng dẫn cài đặt và chạy Identity Service bằng Docker, không cần Traefik.

## 1. Chuẩn bị khóa JWT

Hai file sau phải tồn tại:

```text
services/identity-service/secrets/
├── jwt-private.pem
└── jwt-public.pem
```

Nếu chưa có, tạo bằng OpenSSL:

```powershell
cd D:\logistics-business-management\services\identity-service
New-Item -ItemType Directory -Force secrets

openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:3072 -out secrets/jwt-private.pem
openssl rsa -pubout -in secrets/jwt-private.pem -out secrets/jwt-public.pem
```

Không commit thư mục `secrets/` lên Git.

## 2. Chạy Docker

Đảm bảo Docker Desktop đang chạy, sau đó:

```powershell
cd D:\logistics-business-management\infra\docker
docker compose up --build -d identity-db identity-service
```

Kiểm tra container:

```powershell
docker compose ps identity-db identity-service
docker compose logs identity-service
```

Kiểm tra API:

```powershell
Invoke-RestMethod http://localhost:8005/api/v1/health
```

Swagger: `http://localhost:8005/docs`

## 3. Tạo admin đầu tiên

Chạy trong thư mục `infra/docker`:

```powershell
docker compose exec `
  -e IDENTITY_BOOTSTRAP_ADMIN_USERNAME=admin `
  -e IDENTITY_BOOTSTRAP_ADMIN_EMAIL=admin@gmail.com `
  -e IDENTITY_BOOTSTRAP_ADMIN_PASSWORD=admin@gmail.com `
  identity-service python -m app.scripts.bootstrap_admin
```

Kết quả mong đợi:

```text
Created administrator account: admin
```

## 4. Test đăng nhập

Mở `http://localhost:8005/docs` và gọi:

```text
POST /api/v1/auth/login
```

Body:

```json
{
  "username": "admin",
  "password": "admin@gmail.com"
}
```

Sao chép `access_token`, nhấn **Authorize** và dán token. Sau đó test:

```text
GET /api/v1/auth/me
GET /api/v1/roles
GET /api/v1/accounts
```

## 5. Chạy test tự động

```powershell
cd D:\logistics-business-management\services\identity-service
python -m pip install -e ".[test]"
python -m pytest
```

## 6. Dừng service

```powershell
cd D:\logistics-business-management\infra\docker
docker compose stop identity-service identity-db
```

Không dùng `docker compose down -v` nếu muốn giữ dữ liệu PostgreSQL.

## Các role trong hệ thống
`ROLE_SALE`: Nhân viên Kinh doanh, quản lý hợp đồng và bảng giá.
`ROLE_OPERATION`: Nhân viên Khai thác, quản lý dữ liệu sản lượng thực tế.
`ROLE_ACCOUNTANT`: Nhân viên Kế toán, kiểm tra tính tiền và quản lý hồ sơ thanh toán.
`ROLE_LEGAL`: Nhân viên Pháp chế, rà soát các hồ sơ nghiệp vụ.
`ROLE_DIRECTOR`: Ban Giám đốc, xem và phê duyệt hồ sơ được phân công.
`ROLE_ADMIN`: Quản trị hệ thống, quản lý tài khoản và role người dùng.
Mỗi tài khoản hiện được gán một role. Role xác định nhóm thao tác mà tài khoản có thể thực hiện, nhưng không phải điều kiện duy nhất để được phép xử lý hồ sơ. Người dùng vẫn phải đáp ứng các quy tắc nghiệp vụ như trạng thái hồ sơ hoặc người đang được phân công xử lý.

## Ma trận phân quyền JWT
### Identity Service
- Đăng nhập và xem `/auth/me`: mọi account đang hoạt động.
- Quản lý account và role: `ROLE_ADMIN`.
### Contract Service
- Xem danh sách và chi tiết hợp đồng: `ROLE_SALE`, `ROLE_LEGAL`, `ROLE_DIRECTOR`, `ROLE_ACCOUNTANT`.
- Tạo, sửa, xóa và đổi trạng thái hợp đồng: `ROLE_SALE`.
### Price Service
- Xem service và bảng giá: `ROLE_SALE`, `ROLE_ACCOUNTANT`, `ROLE_LEGAL`, `ROLE_DIRECTOR`.
- Tạo, sửa, xóa và submit service/bảng giá: `ROLE_SALE`.
- Approve hoặc reject bảng giá: `ROLE_DIRECTOR`.
### Production Service
- Xem sản lượng và kiểm tra trùng kỳ: `ROLE_OPERATION`, `ROLE_ACCOUNTANT`.
- Tạo, sửa và khóa kỳ sản lượng: `ROLE_OPERATION`.
### Payment Service
- Xem danh sách và chi tiết thanh toán: `ROLE_ACCOUNTANT`, `ROLE_DIRECTOR`, `ROLE_LEGAL`.
- Preview, tạo, sửa, submit và điều chỉnh thanh toán: `ROLE_ACCOUNTANT`.
Quy ước response:

- `401 Unauthorized`: thiếu token hoặc token sai/hết hạn;
- `403 Forbidden`: token hợp lệ nhưng role không được phép;
- role hợp lệ vẫn phải vượt qua các business rule của service, ví dụ trạng thái hồ sơ hoặc assignee hiện tại.

| Service | Swagger |
|---|---|
| Contract | `http://localhost:8001/docs` |
| Price | `http://localhost:8002/docs` |
| Production | `http://localhost:8003/docs` |
| Payment | `http://localhost:8004/docs` |
| Identity | `http://localhost:8005/docs` |

- Select xem user và mk hash trong mô hình dữ liệu:
docker compose exec identity-db `
  psql -U identity_user -d identity_db `
  -c "SELECT username, password_hash FROM account;"

- Chạy tất cả các service
cd D:\logistics-business-management\infra\docker

docker compose up -d `
  identity-service `
  contract-service `
  price-service `
  production-service `
  payment-service
