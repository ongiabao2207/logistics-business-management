BEGIN;

INSERT INTO contract (id, customer_id, valid_from, valid_to, payment_terms, status, created_at, updated_at)
VALUES
  ('HD2026001', 'KH0001', DATE '2026-01-01', DATE '2026-12-31', 'Thanh toán trong 30 ngày', 'ACTIVE', NOW(), NOW()),
  ('HD2026002', 'KH0002', DATE '2026-01-01', DATE '2026-12-31', 'Thanh toán trong 30 ngày', 'ACTIVE', NOW(), NOW()),
  ('HD2026003', 'KH0005', DATE '2026-01-01', DATE '2026-12-31', 'Thanh toán trong 45 ngày', 'ACTIVE', NOW(), NOW()),
  ('HD2026004', 'KH0001', DATE '2026-01-01', DATE '2026-12-31', 'Thanh toán trong 30 ngày', 'ACTIVE', NOW(), NOW()),
  ('HD2026005', 'KH0002', DATE '2026-01-01', DATE '2026-12-31', 'Thanh toán trong 30 ngày', 'ACTIVE', NOW(), NOW()),
  ('HD2026006', 'KH0003', DATE '2026-02-01', DATE '2026-12-31', 'Thanh toán trong 15 ngày', 'ACTIVE', NOW(), NOW()),
  ('HD2026007', 'KH0004', DATE '2026-03-01', DATE '2026-12-31', 'Thanh toán trong 30 ngày', 'ACTIVE', NOW(), NOW()),
  ('HD2026008', 'KH0005', DATE '2026-01-01', DATE '2026-12-31', 'Thanh toán trong 45 ngày', 'ACTIVE', NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET
  customer_id = EXCLUDED.customer_id,
  valid_from = EXCLUDED.valid_from,
  valid_to = EXCLUDED.valid_to,
  payment_terms = EXCLUDED.payment_terms,
  status = EXCLUDED.status,
  updated_at = NOW();

DELETE FROM contract_service WHERE contract_id IN ('HD2026001', 'HD2026002', 'HD2026003', 'HD2026004', 'HD2026005', 'HD2026006', 'HD2026007', 'HD2026008');
INSERT INTO contract_service (contract_id, service_id, service_name, service_unit, service_price, quantity)
VALUES
  ('HD2026001', 1, 'Bốc xếp Container 20ft', 'Container', 350000.00, 50),
  ('HD2026001', 2, 'Bốc xếp Container 40ft', 'Container', 550000.00, 30),
  ('HD2026001', 3, 'Lưu kho', 'Ngày', 120000.00, 250),
  ('HD2026001', 4, 'Vận chuyển nội địa', 'Chuyến', 2500000.00, 12),
  ('HD2026001', 5, 'Kiểm đếm hàng hóa', 'Lô hàng', 80000.00, 60),
  ('HD2026002', 1, 'Bốc xếp Container 20ft', 'Container', 350000.00, 30),
  ('HD2026002', 3, 'Lưu kho', 'Ngày', 120000.00, 180),
  ('HD2026002', 4, 'Vận chuyển nội địa', 'Chuyến', 2500000.00, 8),
  ('HD2026003', 2, 'Bốc xếp Container 40ft', 'Container', 550000.00, 35),
  ('HD2026003', 3, 'Lưu kho', 'Ngày', 120000.00, 260),
  ('HD2026003', 4, 'Vận chuyển nội địa', 'Chuyến', 2500000.00, 12),
  ('HD2026003', 5, 'Kiểm đếm hàng hóa', 'Lô hàng', 80000.00, 70),
  ('HD2026004', 1, 'Bốc xếp Container 20ft', 'Container', 350000.00, 12),
  ('HD2026004', 2, 'Bốc xếp Container 40ft', 'Container', 550000.00, 8),
  ('HD2026004', 3, 'Lưu kho', 'Ngày', 120000.00, 100),
  ('HD2026005', 1, 'Bốc xếp Container 20ft', 'Container', 350000.00, 18),
  ('HD2026005', 3, 'Lưu kho', 'Ngày', 120000.00, 140),
  ('HD2026006', 2, 'Bốc xếp Container 40ft', 'Container', 550000.00, 10),
  ('HD2026006', 3, 'Lưu kho', 'Ngày', 120000.00, 80),
  ('HD2026007', 1, 'Bốc xếp Container 20ft', 'Container', 350000.00, 20),
  ('HD2026007', 2, 'Bốc xếp Container 40ft', 'Container', 550000.00, 12),
  ('HD2026008', 2, 'Bốc xếp Container 40ft', 'Container', 550000.00, 16),
  ('HD2026008', 3, 'Lưu kho', 'Ngày', 120000.00, 160);

COMMIT;
