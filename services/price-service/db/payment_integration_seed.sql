BEGIN;

INSERT INTO service (id, name, description, is_active, unit, created_at, updated_at)
VALUES
  (1, 'Bốc xếp Container 20ft', 'DV001', TRUE, 'Container', NOW(), NOW()),
  (2, 'Bốc xếp Container 40ft', 'DV002', TRUE, 'Container', NOW(), NOW()),
  (3, 'Lưu kho', 'DV003', TRUE, 'Ngày', NOW(), NOW()),
  (4, 'Vận chuyển nội địa', 'DV004', TRUE, 'Chuyến', NOW(), NOW()),
  (5, 'Kiểm đếm hàng hóa', 'DV005', TRUE, 'Lô hàng', NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name,
  description = EXCLUDED.description,
  is_active = TRUE,
  unit = EXCLUDED.unit,
  updated_at = NOW();

INSERT INTO price_list (id, description, effective_from, effective_to, status, created_at, updated_at)
VALUES ('BG-PAYMENT-2026', 'Bảng giá tích hợp Payment 2026', DATE '2026-01-01', DATE '2026-12-31', 'EFFECTIVE', NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET
  description = EXCLUDED.description,
  effective_from = EXCLUDED.effective_from,
  effective_to = EXCLUDED.effective_to,
  status = EXCLUDED.status,
  updated_at = NOW();

DELETE FROM price_list_detail WHERE price_list_id = 'BG-PAYMENT-2026';
INSERT INTO price_list_detail (price_list_id, service_id, unit_price)
VALUES
  ('BG-PAYMENT-2026', 1, 350000.00),
  ('BG-PAYMENT-2026', 2, 550000.00),
  ('BG-PAYMENT-2026', 3, 120000.00),
  ('BG-PAYMENT-2026', 4, 2500000.00),
  ('BG-PAYMENT-2026', 5, 80000.00);

COMMIT;
