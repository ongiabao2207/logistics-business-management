# Payment Service – Quản lý bảng thanh toán

Payment Service quản lý việc lập, tính toán, lưu, điều chỉnh và theo dõi trạng thái bảng thanh toán định kỳ trong hệ thống Logistics Business Management.

Service được xây dựng bằng FastAPI, SQLAlchemy và PostgreSQL. Payment Service chỉ sở hữu dữ liệu thanh toán; dữ liệu hợp đồng, sản lượng và bảng giá được lấy qua HTTP API của các service tương ứng.

## 1. Chức năng

- Tính xem trước bảng thanh toán theo hợp đồng và kỳ.
- Lưu bảng thanh toán dưới dạng nháp.
- Lưu đơn giá tại thời điểm lập bảng (`unit_price_snapshot`).
- Cho phép kế toán sửa sản lượng thanh toán khi bảng còn là nháp.
- Gửi bảng thanh toán sang trạng thái chờ phê duyệt.
- Ghi lại lịch sử điều chỉnh.
- Ngăn tạo trùng bảng cho cùng hợp đồng và kỳ.
- Sinh mã dạng `TT-<năm>-<số thứ tự>`, ví dụ `TT-2026-001`.

## 2. Nguồn dữ liệu

| Dữ liệu | Nguồn | Cách sử dụng |
| --- | --- | --- |
| Hợp đồng và dịch vụ thuộc hợp đồng | Contract Service | Gọi HTTP API |
| Sản lượng đã xác nhận theo kỳ | Production Service | Gọi HTTP API |
| Tên dịch vụ, đơn vị tính và đơn giá | Price Service | Gọi HTTP API |
| Người dùng và quyền | Identity Service | Xác thực JWT |
| Phê duyệt | Mock/local | Approval Service chưa hoàn chỉnh |
| Bảng thanh toán và lịch sử | Payment PostgreSQL | Payment Service tự quản lý |

File seed chỉ nạp dữ liệu mẫu vào PostgreSQL của từng service. Khi chạy, Payment vẫn lấy Contract, Production và Price qua API thật, không truy cập trực tiếp database của service khác.

## 3. Luồng lập bảng thanh toán

1. Kế toán chọn kỳ và hợp đồng.
2. Frontend yêu cầu Payment tính xem trước.
3. Payment kiểm tra hợp đồng qua Contract Service.
4. Payment lấy sản lượng đúng kỳ từ Production Service.
5. Payment lấy đơn giá hiệu lực từ Price Service.
6. Payment tính tiền từng dòng, thuế và tổng tiền.
7. Kế toán có thể giảm `billing_quantity`, nhưng không được sửa `confirmed_quantity`.
8. Bấm **Lưu nháp** để ghi dữ liệu vào Payment PostgreSQL.
9. Bấm **Lưu và gửi phê duyệt** để tạo Payment rồi chuyển sang `PENDING_APPROVAL`.

`POST /preview` chỉ tính và trả dữ liệu xem trước, không lưu database.

## 4. Quy tắc nghiệp vụ

- Không tạo hai bảng có cùng `contract_id`, `period_start` và `period_end`.
- `period_end` phải lớn hơn hoặc bằng `period_start`.
- Chỉ lấy sản lượng Production đủ điều kiện.
- Mỗi dịch vụ phải có đơn giá hiệu lực tại ngày kết thúc kỳ.
- Sản lượng thanh toán phải thỏa `0 < billing_quantity <= confirmed_quantity`.
- Thuế suất từ `0` đến `1`; VAT 10% được gửi là `0.10`.
- Chỉ bảng `DRAFT` được sửa bằng `PATCH`.
- Bảng `REJECTED` hoặc `REVISION_REQUESTED` được sửa qua endpoint `adjustments`.
- Bảng `APPROVED` hoặc `SIGNED` không được sửa trực tiếp.
- Đơn giá đã lưu là ảnh chụp tại lúc lập bảng, không tự đổi theo bảng giá mới.

## 5. Trạng thái

| Trạng thái | Ý nghĩa |
| --- | --- |
| `DRAFT` | Bản nháp, kế toán còn được chỉnh sửa |
| `PENDING_APPROVAL` | Đã gửi và đang chờ phê duyệt |
| `REVISION_REQUESTED` | Người duyệt yêu cầu chỉnh sửa |
| `REJECTED` | Bảng bị từ chối |
| `APPROVED` | Đã được duyệt |
| `SIGNED` | Đã ký và hoàn tất |

## 6. API

Tất cả API Payment dùng tiền tố `/api/v1`.

| Phương thức | Endpoint | Quyền | Chức năng |
| --- | --- | --- | --- |
| `POST` | `/api/v1/payments/preview` | `ROLE_ACCOUNTANT` | Tính xem trước, không lưu DB |
| `POST` | `/api/v1/payments` | `ROLE_ACCOUNTANT` | Tạo bản nháp |
| `GET` | `/api/v1/payments` | Accountant, Director, Legal | Lấy danh sách |
| `GET` | `/api/v1/payments/{payment_id}` | Accountant, Director, Legal | Xem chi tiết |
| `PATCH` | `/api/v1/payments/{payment_id}` | `ROLE_ACCOUNTANT` | Sửa bản nháp |
| `POST` | `/api/v1/payments/{payment_id}/submit` | `ROLE_ACCOUNTANT` | Gửi phê duyệt |
| `POST` | `/api/v1/payments/{payment_id}/review` | Director hoặc Legal | Duyệt/từ chối mock |
| `POST` | `/api/v1/payments/{payment_id}/adjustments` | `ROLE_ACCOUNTANT` | Điều chỉnh bảng bị trả lại |

API danh sách hỗ trợ `offset`, `limit`, `contract_id`, `period_start` và `period_end`.

Ví dụ kiểm tra bảng đã tồn tại:

```http
GET /api/v1/payments?contract_id=HD2026004&period_start=2026-09-01&period_end=2026-09-30
```

## 7. Ví dụ request

### Tính xem trước

```json
{
  "customer_id": "KH0001",
  "contract_id": "HD2026004",
  "period_start": "2026-09-01",
  "period_end": "2026-09-30",
  "tax_rate": 0.10
}
```

### Lưu bản nháp

Nếu không gửi `lines`, hệ thống sử dụng toàn bộ sản lượng hợp lệ từ Production.

```json
{
  "customer_id": "KH0001",
  "contract_id": "HD2026004",
  "period_start": "2026-09-01",
  "period_end": "2026-09-30",
  "tax_rate": 0.10,
  "lines": [
    { "service_id": "1", "billing_quantity": 12 },
    { "service_id": "2", "billing_quantity": 8 },
    { "service_id": "3", "billing_quantity": 100 }
  ]
}
```

### Sửa bản nháp

```json
{
  "reason": "Điều chỉnh theo biên bản đối soát",
  "lines": [
    { "service_id": "1", "billing_quantity": 10 }
  ]
}
```

Xóa một hạng mục khỏi bản nháp:

```json
{
  "reason": "Hạng mục chưa đủ chứng từ thanh toán",
  "lines": [
    { "service_id": "2", "remove": true }
  ]
}
```

### Điều chỉnh bảng bị trả lại

```json
{
  "revision_request_id": "revision-request-001",
  "adjustment_note": "Điều chỉnh sản lượng theo yêu cầu đối soát",
  "lines": [
    { "service_id": "1", "billing_quantity": 9 }
  ]
}
```

`revision_request_id` hiện là mã mô phỏng vì Approval Service chưa hoàn chỉnh.

## 8. Chạy bằng Docker

Chạy tại thư mục gốc repository:

```powershell
docker compose -f infra/docker/docker-compose.yml up -d --build
docker compose -f infra/docker/docker-compose.yml ps
```

| Thành phần | Địa chỉ |
| --- | --- |
| Payment API | `http://localhost:8004` |
| Swagger | `http://localhost:8004/docs` |
| Health check | `http://localhost:8004/health` |
| Qua Traefik | `http://payment.localhost` |
| Payment PostgreSQL | `localhost:5435` |

Kiểm tra health:

```powershell
Invoke-RestMethod http://localhost:8004/health
```

Kết quả:

```json
{ "status": "ok", "service": "payment" }
```

## 9. Seed dữ liệu trên máy mới

Database trong Docker volume chỉ tồn tại trên máy đã chạy container. Dữ liệu database không đi theo Git, nhưng file seed nằm trong source để thành viên khác tạo lại dữ liệu demo.

Sau khi container đã chạy:

```powershell
powershell -ExecutionPolicy Bypass -File .\infra\docker\seed-payment-integration.ps1
```

Script seed lần lượt Contract, Price, Production và Payment PostgreSQL.

Dữ liệu demo gồm:

- 8 hợp đồng `HD2026001` đến `HD2026008`.
- Sản lượng đủ 12 tháng năm 2026 cho các hợp đồng demo.
- 5 dịch vụ trong Price Service.
- Các hợp đồng Payment demo sử dụng service ID từ `1` đến `5`, tùy hợp đồng.
- Ít nhất 18 bảng thanh toán ở nhiều trạng thái để thử bộ lọc và phân trang.

Các file seed:

```text
services/contract-service/db/payment_integration_seed.sql
services/price-service/db/payment_integration_seed.sql
services/production-service/db/payment_integration_seed.sql
services/payment-service/db/seed.sql
infra/docker/seed-payment-integration.ps1
```

Script có thể chạy lại cho dữ liệu demo. Không dùng `docker compose down -v` nếu muốn giữ database vì `-v` sẽ xóa volume.

## 10. Kiểm tra PostgreSQL

Đếm Payment:

```powershell
docker compose -f infra/docker/docker-compose.yml exec -T payment-db `
  psql -U payment_user -d payment_db -Atc "SELECT COUNT(*) FROM payments;"
```

Xem danh sách:

```powershell
docker compose -f infra/docker/docker-compose.yml exec -T payment-db `
  psql -U payment_user -d payment_db --csv `
  -c "SELECT id, customer_id, contract_id, period_start, period_end, status, total_amount FROM payments ORDER BY created_at DESC;"
```

Xem hạng mục:

```powershell
docker compose -f infra/docker/docker-compose.yml exec -T payment-db `
  psql -U payment_user -d payment_db --csv `
  -c "SELECT payment_id, service_id, description, confirmed_quantity, billing_quantity, unit_price_snapshot, line_amount FROM payment_lines ORDER BY payment_id;"
```

| Bảng | Nội dung |
| --- | --- |
| `payments` | Thông tin chung, kỳ, tổng tiền và trạng thái |
| `payment_lines` | Dịch vụ và sản lượng thanh toán |
| `payment_adjustments` | Lịch sử chỉnh sửa/điều chỉnh |
| `payment_number_sequences` | Số thứ tự mã Payment theo năm |

## 11. Biến môi trường

| Biến | Ý nghĩa |
| --- | --- |
| `PAYMENT_DATABASE_URL` | Chuỗi kết nối database Payment |
| `PAYMENT_USE_FAKE_CLIENTS` | `false` để gọi Contract, Production và Price thật |
| `PAYMENT_CONTRACT_SERVICE_URL` | URL Contract Service |
| `PAYMENT_PRODUCTION_SERVICE_URL` | URL Production Service |
| `PAYMENT_PRICE_SERVICE_URL` | URL Price Service |
| `PAYMENT_UPSTREAM_TIMEOUT_SECONDS` | Thời gian chờ service khác |
| `PAYMENT_IDENTITY_JWKS_URL` | URL public key xác thực JWT |
| `PAYMENT_JWT_ISSUER` | JWT issuer |
| `PAYMENT_JWT_AUDIENCE` | JWT audience |
| `PAYMENT_RABBITMQ_URL` | URL RabbitMQ |
| `PAYMENT_RABBITMQ_ENABLED` | Bật/tắt phát sự kiện RabbitMQ |

Docker Compose đặt `PAYMENT_USE_FAKE_CLIENTS=false`, nên Contract, Production và Price được gọi bằng HTTP API thật. Approval vẫn mock/local.

## 12. Chạy service độc lập

Yêu cầu Python 3.11 trở lên:

```powershell
cd services/payment-service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[test]"
uvicorn app.main:app --reload --port 8004
```

Khi chạy ngoài Docker, phải cấu hình biến môi trường và khởi động PostgreSQL cùng các service phụ thuộc.

## 13. Kiểm thử

```powershell
cd services/payment-service
pytest
```

Hoặc chạy riêng:

```powershell
pytest tests/unit
pytest tests/integration
```

## 14. Lỗi thường gặp

### `401 Unauthorized`

Token thiếu, không hợp lệ hoặc hết hạn. Đăng xuất rồi đăng nhập lại.

### Không có dữ liệu sản lượng trong kỳ đã chọn

Production chưa có dữ liệu đúng hợp đồng và kỳ. Chạy lại seed hoặc chọn kỳ có sản lượng.

### Đã tồn tại bảng thanh toán cho hợp đồng và kỳ này

Hệ thống đang ngăn tạo trùng. Mở bảng đã tồn tại thay vì lập mới.

### Không tìm thấy đơn giá hiệu lực

Price chưa có bảng giá áp dụng tại ngày kết thúc kỳ hoặc dịch vụ chưa nằm trong bảng giá.

### `403 Forbidden`

Tài khoản đã đăng nhập nhưng không có role phù hợp.

### Không kết nối được service phụ thuộc

```powershell
docker compose -f infra/docker/docker-compose.yml ps
docker compose -f infra/docker/docker-compose.yml logs payment-service --tail 100
```

## 15. Lưu ý Git và dữ liệu

- Không commit `.env` hoặc mật khẩu thật.
- Payment không truy cập trực tiếp database của service khác.
- Docker volume không được đẩy lên Git.
- File seed nên được commit để thành viên khác tự tạo dữ liệu demo.
- `docker compose down` giữ lại volume.
- `docker compose down -v` xóa dữ liệu PostgreSQL.
