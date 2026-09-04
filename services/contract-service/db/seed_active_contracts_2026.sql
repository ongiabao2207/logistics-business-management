-- Development seed for the Production Service API integration.
-- Customer ids are obtained through Customer Service's public API.

INSERT INTO contract (id, customer_id, valid_from, valid_to, payment_terms, status, created_at, updated_at)
VALUES
  ('HD-2026-002', 'KH0002', DATE '2026-01-01', DATE '2026-12-31', 'Thanh toán trong 30 ngày', 'ACTIVE', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  ('HD-2026-003', 'KH0003', DATE '2026-01-01', DATE '2026-12-31', 'Thanh toán trong 30 ngày', 'ACTIVE', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  ('HD-2026-004', 'KH0004', DATE '2026-01-01', DATE '2026-12-31', 'Thanh toán trong 30 ngày', 'ACTIVE', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  ('HD-2026-005', 'KH0005', DATE '2026-01-01', DATE '2026-12-31', 'Thanh toán trong 30 ngày', 'ACTIVE', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
  ('HD-2026-006', 'KH0001', DATE '2026-01-01', DATE '2026-12-31', 'Thanh toán trong 30 ngày', 'ACTIVE', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (id) DO UPDATE SET
  customer_id = EXCLUDED.customer_id,
  valid_from = EXCLUDED.valid_from,
  valid_to = EXCLUDED.valid_to,
  payment_terms = EXCLUDED.payment_terms,
  status = EXCLUDED.status,
  updated_at = CURRENT_TIMESTAMP;

DELETE FROM contract_service
WHERE contract_id IN ('HD-2026-002', 'HD-2026-003', 'HD-2026-004', 'HD-2026-005', 'HD-2026-006');

INSERT INTO contract_service (contract_id, service_id, service_name, service_unit, service_price, quantity)
SELECT contract_id, service_id, service_name, service_unit, service_price, quantity
FROM (
  SELECT contract_id, service_id, service_name, service_unit, service_price, quantity
  FROM (VALUES
    ('HD-2026-002', 1, 'Bốc xếp Container 20ft', 'Container', 1200000.00, 100),
    ('HD-2026-002', 2, 'Bốc xếp Container 40ft', 'Container', 1800000.00, 80),
    ('HD-2026-002', 3, 'Lưu kho', 'Ngày', 150000.00, 365),
    ('HD-2026-002', 4, 'Vận chuyển nội địa', 'Chuyến', 2500000.00, 120),
    ('HD-2026-002', 5, 'Kiểm đếm hàng hóa', 'Lô hàng', 350000.00, 150),
    ('HD-2026-002', 6, 'Nâng hạ Container', 'Lần', 450000.00, 120),
    ('HD-2026-003', 1, 'Bốc xếp Container 20ft', 'Container', 1200000.00, 100),
    ('HD-2026-003', 2, 'Bốc xếp Container 40ft', 'Container', 1800000.00, 80),
    ('HD-2026-003', 3, 'Lưu kho', 'Ngày', 150000.00, 365),
    ('HD-2026-003', 4, 'Vận chuyển nội địa', 'Chuyến', 2500000.00, 120),
    ('HD-2026-003', 5, 'Kiểm đếm hàng hóa', 'Lô hàng', 350000.00, 150),
    ('HD-2026-003', 6, 'Nâng hạ Container', 'Lần', 450000.00, 120),
    ('HD-2026-004', 1, 'Bốc xếp Container 20ft', 'Container', 1200000.00, 100),
    ('HD-2026-004', 2, 'Bốc xếp Container 40ft', 'Container', 1800000.00, 80),
    ('HD-2026-004', 3, 'Lưu kho', 'Ngày', 150000.00, 365),
    ('HD-2026-004', 4, 'Vận chuyển nội địa', 'Chuyến', 2500000.00, 120),
    ('HD-2026-004', 5, 'Kiểm đếm hàng hóa', 'Lô hàng', 350000.00, 150),
    ('HD-2026-004', 6, 'Nâng hạ Container', 'Lần', 450000.00, 120),
    ('HD-2026-005', 1, 'Bốc xếp Container 20ft', 'Container', 1200000.00, 100),
    ('HD-2026-005', 2, 'Bốc xếp Container 40ft', 'Container', 1800000.00, 80),
    ('HD-2026-005', 3, 'Lưu kho', 'Ngày', 150000.00, 365),
    ('HD-2026-005', 4, 'Vận chuyển nội địa', 'Chuyến', 2500000.00, 120),
    ('HD-2026-005', 5, 'Kiểm đếm hàng hóa', 'Lô hàng', 350000.00, 150),
    ('HD-2026-005', 6, 'Nâng hạ Container', 'Lần', 450000.00, 120),
    ('HD-2026-006', 1, 'Bốc xếp Container 20ft', 'Container', 1200000.00, 100),
    ('HD-2026-006', 2, 'Bốc xếp Container 40ft', 'Container', 1800000.00, 80),
    ('HD-2026-006', 3, 'Lưu kho', 'Ngày', 150000.00, 365),
    ('HD-2026-006', 4, 'Vận chuyển nội địa', 'Chuyến', 2500000.00, 120),
    ('HD-2026-006', 5, 'Kiểm đếm hàng hóa', 'Lô hàng', 350000.00, 150),
    ('HD-2026-006', 6, 'Nâng hạ Container', 'Lần', 450000.00, 120)
  ) AS seed(contract_id, service_id, service_name, service_unit, service_price, quantity)
) AS contract_services;

INSERT INTO contract_year_sequence (year, last_number)
VALUES (2026, 6)
ON CONFLICT (year) DO UPDATE
SET last_number = GREATEST(contract_year_sequence.last_number, EXCLUDED.last_number);
