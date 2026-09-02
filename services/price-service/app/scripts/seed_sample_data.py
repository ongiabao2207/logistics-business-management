from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.price_model import PriceList, PriceListDetail, Service


SAMPLE_SERVICES = (
    (1, "Vận chuyển container 20 feet", "VC-CONT-20", "Chuyến"),
    (2, "Vận chuyển container 40 feet", "VC-CONT-40", "Chuyến"),
    (3, "Lưu kho hàng thường", "KHO-THUONG", "Pallet/ngày"),
    (4, "Lưu kho lạnh", "KHO-LANH", "Pallet/ngày"),
    (5, "Khai báo hải quan", "HQ-TK-01", "Tờ khai"),
)

SAMPLE_PRICE_LISTS = (
    ("BG-2026-001", "Bảng giá Logistics tiêu chuẩn", date(2026, 1, 1), date(2026, 12, 31), "EFFECTIVE", 1, Decimal("4500000")),
    ("BG-KHO-2026", "Bảng giá dịch vụ lưu kho", date(2026, 3, 1), date(2027, 2, 28), "SUBMITTED", 3, Decimal("85000")),
    ("BG-VC-2026", "Bảng giá vận chuyển nội địa", date(2026, 9, 1), date(2027, 8, 31), "DRAFT", 2, Decimal("6500000")),
    ("BG-XNK-2026", "Bảng giá khách hàng xuất nhập khẩu", date(2026, 10, 1), date(2027, 9, 30), "SUBMITTED", 5, Decimal("1200000")),
    ("BG-VIP-2026", "Bảng giá khách hàng chiến lược", date(2025, 1, 1), date(2025, 12, 31), "EXPIRED", 4, Decimal("180000")),
)


def seed_sample_prices(db) -> tuple[int, int]:
    for service_id, name, code, unit in SAMPLE_SERVICES:
        service = db.get(Service, service_id)
        if service is None:
            service = Service(id=service_id, name=name, description=code, unit=unit, is_active=True)
            db.add(service)
        else:
            service.name, service.description, service.unit, service.is_active = name, code, unit, True
    db.flush()

    for list_id, description, effective_from, effective_to, status, service_id, unit_price in SAMPLE_PRICE_LISTS:
        price_list = db.get(PriceList, list_id)
        if price_list is None:
            price_list = PriceList(id=list_id, description=description, effective_from=effective_from, effective_to=effective_to, status=status)
            db.add(price_list)
        else:
            price_list.description, price_list.effective_from, price_list.effective_to, price_list.status = description, effective_from, effective_to, status
        db.flush()
        detail = db.scalar(select(PriceListDetail).where(PriceListDetail.price_list_id == list_id, PriceListDetail.service_id == service_id))
        if detail is None:
            db.add(PriceListDetail(price_list_id=list_id, service_id=service_id, unit_price=unit_price))
        else:
            detail.unit_price = unit_price
    db.commit()
    return len(SAMPLE_SERVICES), len(SAMPLE_PRICE_LISTS)


def main() -> None:
    with SessionLocal() as db:
        services, price_lists = seed_sample_prices(db)
    print(f"Seeded {services} services and {price_lists} price lists")


if __name__ == "__main__":
    main()
