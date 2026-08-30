# Môi trường Docker dùng chung

Thư mục này chứa file Docker Compose dùng chung cho các service hiện đã được
triển khai trong hệ thống. Tất cả lệnh bên dưới cần được chạy tại thư mục gốc
của repository.

## Yêu cầu

- Đã cài đặt và khởi động Docker Desktop.
- Docker Desktop đang sử dụng Linux containers.
- Các cổng được liệt kê bên dưới chưa bị ứng dụng khác sử dụng.

## Khởi động hệ thống

```powershell
docker compose -f infra/docker/docker-compose.yml up --build -d
docker compose -f infra/docker/docker-compose.yml ps
```

Traefik nhận request tại `http://localhost`. Dashboard phục vụ việc kiểm tra
trong môi trường phát triển tại `http://localhost:8080/dashboard/`.

## Routes và ports

| Thành phần | Route qua Traefik | Cổng truy cập trực tiếp |
| --- | --- | ---: |
| Contract Service | `http://localhost/api/v1/contracts` | `8001` |
| Price Service | `http://localhost/api/v1/services` | `8002` |
| Production Service | `http://localhost/api/v1/production-periods` | `8003` |
| Payment Service | `http://localhost/api/v1/payments` | `8004` |
| Contract PostgreSQL | Không áp dụng | `5432` |
| Price PostgreSQL | Không áp dụng | `5433` |
| Production PostgreSQL | Không áp dụng | `5434` |
| Payment PostgreSQL | Không áp dụng | `5435` |

Các cổng truy cập trực tiếp chỉ được bind vào `127.0.0.1` để phục vụ phát
triển cục bộ. Giao tiếp giữa các container sử dụng tên service và cổng nội bộ,
không sử dụng cổng được publish ra máy host.

Có thể truy cập trực tiếp từng API mà không qua Traefik:

| Service | URL truy cập trực tiếp |
| --- | --- |
| Contract | `http://localhost:8001/api/v1/contracts` |
| Price | `http://localhost:8002/api/v1/services` |
| Production | `http://localhost:8003/api/v1/production-periods` |
| Payment | `http://localhost:8004/api/v1/payments` |

## Kiểm tra hệ thống

Kiểm tra trạng thái container và database:

```powershell
docker compose -f infra/docker/docker-compose.yml ps -a
```

Bốn container PostgreSQL phải có trạng thái `healthy`; Traefik và bốn API phải
có trạng thái `Up`.

Kiểm tra các API qua Traefik bằng route theo đường dẫn:

```powershell
curl.exe -i http://127.0.0.1/api/v1/contracts
curl.exe -i http://127.0.0.1/api/v1/services
curl.exe -i http://127.0.0.1/api/v1/production-periods
curl.exe -i http://127.0.0.1/api/v1/payments
```

Kết quả `HTTP/1.1 200 OK` cùng với dữ liệu `[]` có nghĩa API hoạt động nhưng
database chưa có bản ghi.

Kiểm tra health endpoint của từng service qua Traefik:

```powershell
curl.exe -i -H "Host: contract.localhost" http://127.0.0.1/api/v1/health
curl.exe -i -H "Host: price.localhost" http://127.0.0.1/api/v1/health
curl.exe -i -H "Host: production.localhost" http://127.0.0.1/health
curl.exe -i -H "Host: payment.localhost" http://127.0.0.1/health
```

Kiểm tra các router được Traefik nạp từ Docker labels:

```powershell
curl.exe -s http://localhost:8080/api/http/routers
```

Danh sách phải có `contract@docker`, `price@docker`, `production@docker` và
`payment@docker` ở trạng thái `enabled`.

## Network và cô lập database

Traefik và các API container cùng tham gia network `lbm-gateway`. Mỗi API chỉ
tham gia thêm network database thuộc quyền sở hữu của chính service đó:

- `lbm-contract-data`
- `lbm-price-data`
- `lbm-production-data`
- `lbm-payment-data`

Các database container không tham gia gateway network. Nhờ đó, một service
không thể truy cập trực tiếp PostgreSQL của service khác thông qua cấu trúc
network của Docker Compose.

Mỗi PostgreSQL sử dụng một named volume riêng để giữ dữ liệu sau khi container
được khởi động lại.

## Dừng hệ thống

Dừng và xóa container nhưng giữ nguyên dữ liệu database:

```powershell
docker compose -f infra/docker/docker-compose.yml down
```

Chỉ sử dụng lệnh sau khi chắc chắn có thể xóa vĩnh viễn toàn bộ dữ liệu
PostgreSQL cục bộ của hệ thống:

```powershell
docker compose -f infra/docker/docker-compose.yml down --volumes
```

## Thay đổi ports

Có thể ghi đè các cổng được publish bằng biến môi trường mà không cần sửa file
Compose. Ví dụ trong PowerShell:

```powershell
$env:TRAEFIK_HTTP_PORT = "8088"
$env:CONTRACT_DB_PORT = "15432"
docker compose -f infra/docker/docker-compose.yml up --build -d
```

Thông tin đăng nhập database dùng cho môi trường phát triển cũng có thể được
ghi đè bằng biến môi trường. Không đưa mật khẩu thật vào file Compose và không
commit file `.env`.

## Xem logs khi có lỗi

Xem log của toàn bộ hệ thống:

```powershell
docker compose -f infra/docker/docker-compose.yml logs --tail=200
```

Xem log của một thành phần cụ thể, ví dụ Traefik:

```powershell
docker compose -f infra/docker/docker-compose.yml logs traefik --tail=200
```
