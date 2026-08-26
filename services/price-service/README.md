# Price Service

Price Service quản lý dịch vụ, bảng giá và cung cấp giá đang áp dụng cho các
service khác.

Mã bảng giá do hệ thống tự sinh theo dạng `BG-{năm}-{số thứ tự}`, ví dụ
`BG-2026-001`, `BG-2026-002`. Số thứ tự tăng riêng trong từng năm.

## Chạy bằng Docker

```powershell
cd D:\logistics-business-management\services\price-service
docker compose up
```

- Swagger: `http://localhost:8002/docs`
- Health check: `http://localhost:8002/api/v1/health`
- PostgreSQL: `localhost:5433`

Kiểm tra container và xem log:

```powershell
docker compose ps
docker compose logs -f api
```

Dừng và xóa container nhưng vẫn giữ dữ liệu PostgreSQL:

```powershell
docker compose down
```

Khi chạy bằng Docker, không chạy thêm Uvicorn local trên cổng `8001`.

## Chạy local không dùng Docker API

PostgreSQL Docker phải đang chạy tại cổng `5433`:

```powershell
cd D:\logistics-business-management\services\price-service
python -m pip install -e ".[test]"
$env:PRICE_DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5433/price_db"
python -m uvicorn app.main:app --reload --port 8001
```

- Swagger local: `http://localhost:8001/docs`
- Chỉ dùng cách này khi không chạy container `api`.

## API

### Service

- `POST /api/v1/services`: Tạo dịch vụ mới.
- `GET /api/v1/services`: Lấy danh sách dịch vụ.
- `DELETE /api/v1/services/{service_id}`: Ngừng cung cấp dịch vụ.

### Price List

- `POST /api/v1/price-lists`: Tạo bảng giá mới ở trạng thái `DRAFT`.
- `GET /api/v1/price-lists`: Lấy danh sách bảng giá.
- `GET /api/v1/price-lists/{price_list_id}`: Xem chi tiết bảng giá.
- `PATCH /api/v1/price-lists/{price_list_id}`: Cập nhật bảng giá `DRAFT` hoặc `REJECTED`.
- `DELETE /api/v1/price-lists/{price_list_id}`: Xóa bảng giá `DRAFT`.
- `POST /api/v1/price-lists/{price_list_id}/submit`: Gửi bảng giá đi duyệt.
- `POST /api/v1/price-lists/{price_list_id}/approve`: Phê duyệt bảng giá.
- `POST /api/v1/price-lists/{price_list_id}/reject`: Từ chối bảng giá.
- `GET /api/v1/price-lists/effective/services/{service_id}`: Tra giá đang áp dụng.

### System

- `GET /api/v1/health`: Kiểm tra Price Service có hoạt động không.

## Vòng đời bảng giá

```text
DRAFT → SUBMITTED → APPROVED → EFFECTIVE → EXPIRED
          ↓             ↓
       REJECTED      SUPERSEDED
          ↓
        DRAFT
```

- `DRAFT`: Bảng giá mới tạo, được phép sửa hoặc xóa.
- `SUBMITTED`: Đã gửi đi duyệt.
- `APPROVED`: Đã được phê duyệt nhưng chưa áp dụng.
- `REJECTED`: Bị từ chối; khi chỉnh sửa bằng `PATCH` sẽ trở về `DRAFT`.
- `EFFECTIVE`: Đang được áp dụng.
- `SUPERSEDED`: Đã bị phiên bản mới thay thế.
- `EXPIRED`: Bảng giá đã hết hiệu lực.

Phê duyệt trước ngày hiệu lực của bảng giá mới: submit -> approved -> effective
Phê duyệt đúng ngày hiệu lực của bảng giá mới: submit -> effective

Khi phê duyệt, bảng giá chưa tới ngày hiệu lực sẽ thành `APPROVED`. Nếu đang trong
thời gian hiệu lực, bảng giá thành `EFFECTIVE` và phiên bản cũ thành `SUPERSEDED`.
Khi trạng thái được truy vấn, hệ thống đồng bộ `APPROVED → EFFECTIVE` từ ngày bắt
đầu và `EFFECTIVE → EXPIRED` sau ngày kết thúc.

Mỗi mã `BG-...` là một phiên bản được lưu lại trong lịch sử. Hai bảng giá
`APPROVED` không được chồng thời gian. Khi phiên bản mới được áp dụng, phiên bản
`EFFECTIVE` cũ bị chồng thời gian sẽ chuyển thành `SUPERSEDED`.

## Chạy test

```powershell
python -m pytest -q
```

Test sử dụng SQLite tạm thời và không tác động PostgreSQL thật.
