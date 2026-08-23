# Price Service

Price Service quản lý dịch vụ, bảng giá và cung cấp giá đang áp dụng cho các
service khác.

## Cài đặt

```powershell
cd D:\logistics-business-management\services\price-service
python -m pip install -e ".[test]"
```

Thiết lập kết nối PostgreSQL:

```powershell
$env:PRICE_DATABASE_URL="postgresql+psycopg://postgres:password@localhost:5432/price_db"
```

Database cần có sẵn các bảng `service`, `price_list` và `price_list_detail`.
Ứng dụng hiện không tự tạo bảng hoặc chạy migration.

## Chạy service

```powershell
python -m uvicorn app.main:app --reload --port 8001
```

- Swagger: `http://127.0.0.1:8001/docs`
- Health check: `http://127.0.0.1:8001/api/v1/health`

## Chạy bằng Docker

```powershell
docker compose up --build
```

Docker chạy Price Service tại `http://127.0.0.1:8001` và PostgreSQL tại cổng
`5433`. Dừng các container bằng:

```powershell
docker compose down
```

## API

### Service

- `POST /api/v1/services`: Tạo dịch vụ mới.
- `GET /api/v1/services`: Lấy danh sách dịch vụ.
- `DELETE /api/v1/services/{service_id}`: Ngừng cung cấp dịch vụ.

### Price List

- `POST /api/v1/price-lists`: Tạo bảng giá mới ở trạng thái `DRAFT`.
- `GET /api/v1/price-lists`: Lấy danh sách bảng giá.
- `GET /api/v1/price-lists/{price_list_id}`: Xem chi tiết bảng giá.
- `PATCH /api/v1/price-lists/{price_list_id}`: Cập nhật bảng giá `DRAFT`.
- `DELETE /api/v1/price-lists/{price_list_id}`: Xóa bảng giá `DRAFT`.
- `POST /api/v1/price-lists/{price_list_id}/submit`: Gửi bảng giá đi duyệt.
- `GET /api/v1/price-lists/active/services/{service_id}`: Tra giá hiện tại.

### System

- `GET /api/v1/health`: Kiểm tra Price Service có hoạt động không.

## Vòng đời bảng giá

```text
DRAFT → SUBMITTED → APPROVED → ACTIVE → EXPIRED
```

- `DRAFT`: Bảng giá mới tạo, được phép sửa hoặc xóa.
- `SUBMITTED`: Đã gửi đi duyệt.
- `APPROVED`: Đã được phê duyệt.
- `ACTIVE`: Bảng giá đang được áp dụng.
- `EXPIRED`: Bảng giá đã hết hiệu lực.

API hiện tại xử lý bước `DRAFT → SUBMITTED`. Các bước phê duyệt và kích hoạt
sẽ do quy trình phê duyệt xử lý.

## Chạy test

```powershell
python -m pytest -q
```

Test sử dụng SQLite tạm thời và không tác động PostgreSQL thật.
