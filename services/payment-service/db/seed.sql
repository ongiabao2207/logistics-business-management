-- Dữ liệu minh họa Payment Service, dựa trên docs/source/Data sample.pdf.
-- Có thể chạy lại nhiều lần mà không tạo thêm bảng thanh toán trùng kỳ.

BEGIN;

INSERT INTO payment_number_sequences (year, last_number)
VALUES (2026, 6)
ON CONFLICT (year) DO UPDATE
SET last_number = GREATEST(payment_number_sequences.last_number, EXCLUDED.last_number);

INSERT INTO payments (
    id, customer_id, contract_id, period_start, period_end,
    subtotal, tax_amount, total_amount, status,
    approval_instance_id, created_at, updated_at
)
VALUES
    ('TT-2026-001', 'KH0001', 'HD2026001', DATE '2026-08-01', DATE '2026-08-31',
     50500000.00, 5050000.00, 55550000.00, 'DRAFT',
     NULL, TIMESTAMPTZ '2026-08-31 08:15:00+07', TIMESTAMPTZ '2026-08-31 08:15:00+07'),
    ('TT-2026-002', 'KH0002', 'HD2026002', DATE '2026-09-01', DATE '2026-09-30',
     29300000.00, 2930000.00, 32230000.00, 'PENDING_APPROVAL',
     'approval-2026-002', TIMESTAMPTZ '2026-09-30 09:20:00+07', TIMESTAMPTZ '2026-09-30 09:35:00+07'),
    ('TT-2026-003', 'KH0005', 'HD2026003', DATE '2026-07-01', DATE '2026-07-31',
     38300000.00, 3830000.00, 42130000.00, 'REVISION_REQUESTED',
     'approval-2026-003', TIMESTAMPTZ '2026-07-31 10:00:00+07', TIMESTAMPTZ '2026-08-01 14:10:00+07'),
    ('TT-2026-004', 'KH0001', 'HD2026001', DATE '2026-09-01', DATE '2026-09-30',
     62750000.00, 6275000.00, 69025000.00, 'SIGNED',
     'approval-2026-004', TIMESTAMPTZ '2026-09-30 11:25:00+07', TIMESTAMPTZ '2026-10-02 15:05:00+07'),
    ('TT-2026-005', 'KH0002', 'HD2026002', DATE '2026-10-01', DATE '2026-10-31',
     24500000.00, 2450000.00, 26950000.00, 'REJECTED',
     'approval-2026-005', TIMESTAMPTZ '2026-10-31 13:00:00+07', TIMESTAMPTZ '2026-11-01 09:30:00+07'),
    ('TT-2026-006', 'KH0005', 'HD2026003', DATE '2026-08-01', DATE '2026-08-31',
     71550000.00, 7155000.00, 78705000.00, 'APPROVED',
     'approval-2026-006', TIMESTAMPTZ '2026-08-31 14:20:00+07', TIMESTAMPTZ '2026-09-02 16:00:00+07')
ON CONFLICT (contract_id, period_start, period_end) DO UPDATE
SET customer_id = EXCLUDED.customer_id,
    subtotal = EXCLUDED.subtotal,
    tax_amount = EXCLUDED.tax_amount,
    total_amount = EXCLUDED.total_amount,
    status = EXCLUDED.status,
    approval_instance_id = EXCLUDED.approval_instance_id,
    created_at = EXCLUDED.created_at,
    updated_at = EXCLUDED.updated_at;

-- Thay lại các dòng thuộc đúng sáu kỳ demo, không đụng tới dữ liệu khác.
DELETE FROM payment_adjustments
WHERE payment_id IN (
    SELECT id FROM payments
    WHERE (contract_id, period_start, period_end) IN (
        ('HD2026001', DATE '2026-08-01', DATE '2026-08-31'),
        ('HD2026002', DATE '2026-09-01', DATE '2026-09-30'),
        ('HD2026003', DATE '2026-07-01', DATE '2026-07-31'),
        ('HD2026001', DATE '2026-09-01', DATE '2026-09-30'),
        ('HD2026002', DATE '2026-10-01', DATE '2026-10-31'),
        ('HD2026003', DATE '2026-08-01', DATE '2026-08-31')
    )
);

DELETE FROM payment_lines
WHERE payment_id IN (
    SELECT id FROM payments
    WHERE (contract_id, period_start, period_end) IN (
        ('HD2026001', DATE '2026-08-01', DATE '2026-08-31'),
        ('HD2026002', DATE '2026-09-01', DATE '2026-09-30'),
        ('HD2026003', DATE '2026-07-01', DATE '2026-07-31'),
        ('HD2026001', DATE '2026-09-01', DATE '2026-09-30'),
        ('HD2026002', DATE '2026-10-01', DATE '2026-10-31'),
        ('HD2026003', DATE '2026-08-01', DATE '2026-08-31')
    )
);

WITH sample_lines (
    contract_id, period_start, period_end, service_id, description,
    confirmed_quantity, billing_quantity, unit_price, line_amount, tax_rate, tax_amount
) AS (
    VALUES
        ('HD2026001', DATE '2026-08-01', DATE '2026-08-31', 'DV001', 'Bốc xếp Container 20ft', 20.0000, 20.0000, 350000.00,  7000000.00, 0.1000,  700000.00),
        ('HD2026001', DATE '2026-08-01', DATE '2026-08-31', 'DV002', 'Bốc xếp Container 40ft', 10.0000, 10.0000, 550000.00,  5500000.00, 0.1000,  550000.00),
        ('HD2026001', DATE '2026-08-01', DATE '2026-08-31', 'DV003', 'Lưu kho',                  175.0000,175.0000, 120000.00, 21000000.00, 0.1000, 2100000.00),
        ('HD2026001', DATE '2026-08-01', DATE '2026-08-31', 'DV004', 'Vận chuyển nội địa',       6.0000,  6.0000,2500000.00, 15000000.00, 0.1000, 1500000.00),
        ('HD2026001', DATE '2026-08-01', DATE '2026-08-31', 'DV005', 'Kiểm đếm hàng hóa',        25.0000, 25.0000,  80000.00,  2000000.00, 0.1000,  200000.00),

        ('HD2026002', DATE '2026-09-01', DATE '2026-09-30', 'DV001', 'Bốc xếp Container 20ft', 14.0000, 14.0000, 350000.00,  4900000.00, 0.1000,  490000.00),
        ('HD2026002', DATE '2026-09-01', DATE '2026-09-30', 'DV003', 'Lưu kho',                  120.0000,120.0000, 120000.00, 14400000.00, 0.1000, 1440000.00),
        ('HD2026002', DATE '2026-09-01', DATE '2026-09-30', 'DV004', 'Vận chuyển nội địa',       4.0000,  4.0000,2500000.00, 10000000.00, 0.1000, 1000000.00),

        ('HD2026003', DATE '2026-07-01', DATE '2026-07-31', 'DV002', 'Bốc xếp Container 40ft', 18.0000, 18.0000, 550000.00,  9900000.00, 0.1000,  990000.00),
        ('HD2026003', DATE '2026-07-01', DATE '2026-07-31', 'DV003', 'Lưu kho',                  210.0000,210.0000, 120000.00, 25200000.00, 0.1000, 2520000.00),
        ('HD2026003', DATE '2026-07-01', DATE '2026-07-31', 'DV005', 'Kiểm đếm hàng hóa',        40.0000, 40.0000,  80000.00,  3200000.00, 0.1000,  320000.00),

        ('HD2026001', DATE '2026-09-01', DATE '2026-09-30', 'DV001', 'Bốc xếp Container 20ft', 30.0000, 30.0000, 350000.00, 10500000.00, 0.1000, 1050000.00),
        ('HD2026001', DATE '2026-09-01', DATE '2026-09-30', 'DV002', 'Bốc xếp Container 40ft', 15.0000, 15.0000, 550000.00,  8250000.00, 0.1000,  825000.00),
        ('HD2026001', DATE '2026-09-01', DATE '2026-09-30', 'DV003', 'Lưu kho',                  200.0000,200.0000, 120000.00, 24000000.00, 0.1000, 2400000.00),
        ('HD2026001', DATE '2026-09-01', DATE '2026-09-30', 'DV004', 'Vận chuyển nội địa',       8.0000,  8.0000,2500000.00, 20000000.00, 0.1000, 2000000.00),

        ('HD2026002', DATE '2026-10-01', DATE '2026-10-31', 'DV001', 'Bốc xếp Container 20ft', 10.0000, 10.0000, 350000.00,  3500000.00, 0.1000,  350000.00),
        ('HD2026002', DATE '2026-10-01', DATE '2026-10-31', 'DV003', 'Lưu kho',                   90.0000, 90.0000, 150000.00, 13500000.00, 0.1000, 1350000.00),
        ('HD2026002', DATE '2026-10-01', DATE '2026-10-31', 'DV004', 'Vận chuyển nội địa',        3.0000,  3.0000,2500000.00,  7500000.00, 0.1000,  750000.00),

        ('HD2026003', DATE '2026-08-01', DATE '2026-08-31', 'DV002', 'Bốc xếp Container 40ft', 25.0000, 25.0000, 550000.00, 13750000.00, 0.1000, 1375000.00),
        ('HD2026003', DATE '2026-08-01', DATE '2026-08-31', 'DV003', 'Lưu kho',                  240.0000,240.0000, 120000.00, 28800000.00, 0.1000, 2880000.00),
        ('HD2026003', DATE '2026-08-01', DATE '2026-08-31', 'DV004', 'Vận chuyển nội địa',       10.0000, 10.0000,2500000.00, 25000000.00, 0.1000, 2500000.00),
        ('HD2026003', DATE '2026-08-01', DATE '2026-08-31', 'DV005', 'Kiểm đếm hàng hóa',        50.0000, 50.0000,  80000.00,  4000000.00, 0.1000,  400000.00)
)
INSERT INTO payment_lines (
    id, payment_id, service_id, description, confirmed_quantity,
    billing_quantity, unit_price_snapshot, line_amount, tax_rate, tax_amount
)
SELECT
    md5(p.id || ':' || s.service_id), p.id, s.service_id, s.description,
    s.confirmed_quantity, s.billing_quantity, s.unit_price,
    s.line_amount, s.tax_rate, s.tax_amount
FROM sample_lines s
JOIN payments p
  ON p.contract_id = s.contract_id
 AND p.period_start = s.period_start
 AND p.period_end = s.period_end;

-- Một lịch sử minh họa cho hồ sơ đang được yêu cầu điều chỉnh.
INSERT INTO payment_adjustments (
    id, payment_id, reason, amount, status, change_type, action,
    revision_request_id, service_id, confirmed_quantity,
    previous_billing_quantity, new_billing_quantity,
    previous_tax_rate, new_tax_rate, created_at
)
SELECT
    md5(p.id || ':revision:DV003'), p.id,
    'Pháp chế yêu cầu kiểm tra lại sản lượng lưu kho theo biên bản đối soát.',
    0.00, 'PENDING', 'REVISION_ADJUSTMENT', 'UPDATE',
    'revision-request-2026-003', 'DV003', 210.0000,
    210.0000, 210.0000, 0.1000, 0.1000,
    TIMESTAMPTZ '2026-08-01 14:10:00+07'
FROM payments p
WHERE p.contract_id = 'HD2026003'
  AND p.period_start = DATE '2026-07-01'
  AND p.period_end = DATE '2026-07-31';

COMMIT;
