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
- Health check: `http://127.0.0.1:8001/health`

## API

### Service

- `POST /services`: Tạo dịch vụ mới.
- `GET /services`: Lấy danh sách dịch vụ.
- `DELETE /services/{service_id}`: Ngừng cung cấp dịch vụ.

### Price List

- `POST /price-lists`: Tạo bảng giá mới ở trạng thái `DRAFT`.
- `GET /price-lists`: Lấy danh sách bảng giá.
- `GET /price-lists/{price_list_id}`: Xem chi tiết bảng giá.
- `PATCH /price-lists/{price_list_id}`: Cập nhật bảng giá `DRAFT`.
- `DELETE /price-lists/{price_list_id}`: Xóa bảng giá `DRAFT`.
- `POST /price-lists/{price_list_id}/submit`: Gửi bảng giá đi duyệt.
- `GET /price-lists/active/services/{service_id}`: Tra giá hiện tại của dịch vụ.

### System

- `GET /health`: Kiểm tra Price Service có hoạt động không.

## Chạy test

```powershell
python -m pytest -q
```

Test sử dụng SQLite tạm thời và không tác động PostgreSQL thật.
