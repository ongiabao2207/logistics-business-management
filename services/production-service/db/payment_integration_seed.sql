BEGIN;

DELETE FROM production_periods
WHERE contract_id IN ('HD2026001', 'HD2026002', 'HD2026003', 'HD2026004', 'HD2026005', 'HD2026006', 'HD2026007', 'HD2026008')
  AND from_date >= DATE '2026-01-01'
  AND to_date <= DATE '2026-12-31';

INSERT INTO production_periods (
  customer_id, contract_id, period_name, from_date, to_date, status,
  locked_at, locked_by, created_at, updated_at
)
SELECT
  contract.customer_id,
  contract.contract_id,
  'Sản lượng tháng ' || TO_CHAR(month.period_start, 'MM/YYYY'),
  month.period_start,
  (month.period_start + INTERVAL '1 month - 1 day')::date,
  'APPROVED', NOW(), 'seed-payment-integration', NOW(), NOW()
FROM (VALUES
  ('KH0001', 'HD2026001'),
  ('KH0002', 'HD2026002'),
  ('KH0005', 'HD2026003'),
  ('KH0001', 'HD2026004'),
  ('KH0002', 'HD2026005'),
  ('KH0003', 'HD2026006'),
  ('KH0004', 'HD2026007'),
  ('KH0005', 'HD2026008')
) AS contract(customer_id, contract_id)
CROSS JOIN (
  SELECT generate_series(DATE '2026-01-01', DATE '2026-12-01', INTERVAL '1 month')::date AS period_start
) AS month;

INSERT INTO production_details (
  production_period_id, service_code, recorded_date, quantity, unit, notes, created_at, updated_at
)
SELECT p.id, sample.service_code, p.to_date, sample.quantity, sample.unit, sample.notes, NOW(), NOW()
FROM production_periods p
JOIN (VALUES
  ('HD2026001', '1', 30.000, 'Container', 'Bốc xếp Container 20ft'),
  ('HD2026001', '2', 15.000, 'Container', 'Bốc xếp Container 40ft'),
  ('HD2026001', '3', 200.000, 'Ngày', 'Lưu kho'),
  ('HD2026001', '4', 8.000, 'Chuyến', 'Vận chuyển nội địa'),
  ('HD2026001', '5', 50.000, 'Lô hàng', 'Kiểm đếm hàng hóa'),
  ('HD2026002', '1', 20.000, 'Container', 'Bốc xếp Container 20ft'),
  ('HD2026002', '3', 150.000, 'Ngày', 'Lưu kho'),
  ('HD2026002', '4', 6.000, 'Chuyến', 'Vận chuyển nội địa'),
  ('HD2026003', '2', 25.000, 'Container', 'Bốc xếp Container 40ft'),
  ('HD2026003', '3', 220.000, 'Ngày', 'Lưu kho'),
  ('HD2026003', '4', 10.000, 'Chuyến', 'Vận chuyển nội địa'),
  ('HD2026003', '5', 50.000, 'Lô hàng', 'Kiểm đếm hàng hóa'),
  ('HD2026004', '1', 12.000, 'Container', 'Bốc xếp Container 20ft'),
  ('HD2026004', '2', 8.000, 'Container', 'Bốc xếp Container 40ft'),
  ('HD2026004', '3', 100.000, 'Ngày', 'Lưu kho'),
  ('HD2026005', '1', 18.000, 'Container', 'Bốc xếp Container 20ft'),
  ('HD2026005', '3', 140.000, 'Ngày', 'Lưu kho'),
  ('HD2026006', '2', 10.000, 'Container', 'Bốc xếp Container 40ft'),
  ('HD2026006', '3', 80.000, 'Ngày', 'Lưu kho'),
  ('HD2026007', '1', 20.000, 'Container', 'Bốc xếp Container 20ft'),
  ('HD2026007', '2', 12.000, 'Container', 'Bốc xếp Container 40ft'),
  ('HD2026008', '2', 16.000, 'Container', 'Bốc xếp Container 40ft'),
  ('HD2026008', '3', 160.000, 'Ngày', 'Lưu kho')
) AS sample(contract_id, service_code, quantity, unit, notes)
  ON sample.contract_id = p.contract_id
WHERE p.from_date >= DATE '2026-01-01' AND p.to_date <= DATE '2026-12-31';

COMMIT;
