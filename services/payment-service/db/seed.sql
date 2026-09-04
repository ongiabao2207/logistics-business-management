-- Dữ liệu minh họa Payment Service, dựa trên docs/source/Data sample.pdf.
-- Có thể chạy lại nhiều lần mà không tạo thêm bảng thanh toán trùng kỳ.

BEGIN;

INSERT INTO payment_number_sequences (year, last_number)
VALUES (2026, 206)
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

-- Thêm dữ liệu lịch sử để kiểm thử tìm kiếm, lọc và phân trang danh sách.
INSERT INTO payments (
    id, customer_id, contract_id, period_start, period_end,
    subtotal, tax_amount, total_amount, status,
    approval_instance_id, created_at, updated_at
)
VALUES
    ('TT-2026-101', 'KH0001', 'HD2026001', DATE '2026-01-01', DATE '2026-01-31',  7000000,  700000,  7700000, 'SIGNED', 'approval-2026-101', TIMESTAMPTZ '2026-01-31 08:00:00+07', TIMESTAMPTZ '2026-02-02 08:00:00+07'),
    ('TT-2026-102', 'KH0002', 'HD2026002', DATE '2026-01-01', DATE '2026-01-31',  8250000,  825000,  9075000, 'APPROVED', 'approval-2026-102', TIMESTAMPTZ '2026-01-31 09:00:00+07', TIMESTAMPTZ '2026-02-01 09:00:00+07'),
    ('TT-2026-103', 'KH0005', 'HD2026003', DATE '2026-01-01', DATE '2026-01-31', 12000000, 1200000, 13200000, 'SIGNED', 'approval-2026-103', TIMESTAMPTZ '2026-01-31 10:00:00+07', TIMESTAMPTZ '2026-02-02 10:00:00+07'),
    ('TT-2026-104', 'KH0001', 'HD2026001', DATE '2026-02-01', DATE '2026-02-28', 10500000, 1050000, 11550000, 'PENDING_APPROVAL', 'approval-2026-104', TIMESTAMPTZ '2026-02-28 08:00:00+07', TIMESTAMPTZ '2026-02-28 08:30:00+07'),
    ('TT-2026-105', 'KH0002', 'HD2026002', DATE '2026-02-01', DATE '2026-02-28', 11000000, 1100000, 12100000, 'DRAFT', NULL, TIMESTAMPTZ '2026-02-28 09:00:00+07', TIMESTAMPTZ '2026-02-28 09:00:00+07'),
    ('TT-2026-106', 'KH0005', 'HD2026003', DATE '2026-02-01', DATE '2026-02-28', 14400000, 1440000, 15840000, 'REVISION_REQUESTED', 'approval-2026-106', TIMESTAMPTZ '2026-02-28 10:00:00+07', TIMESTAMPTZ '2026-03-01 10:00:00+07'),
    ('TT-2026-107', 'KH0001', 'HD2026001', DATE '2026-03-01', DATE '2026-03-31', 14000000, 1400000, 15400000, 'APPROVED', 'approval-2026-107', TIMESTAMPTZ '2026-03-31 08:00:00+07', TIMESTAMPTZ '2026-04-01 08:00:00+07'),
    ('TT-2026-108', 'KH0002', 'HD2026002', DATE '2026-03-01', DATE '2026-03-31', 13750000, 1375000, 15125000, 'REJECTED', 'approval-2026-108', TIMESTAMPTZ '2026-03-31 09:00:00+07', TIMESTAMPTZ '2026-04-01 09:00:00+07'),
    ('TT-2026-109', 'KH0005', 'HD2026003', DATE '2026-03-01', DATE '2026-03-31', 18000000, 1800000, 19800000, 'SIGNED', 'approval-2026-109', TIMESTAMPTZ '2026-03-31 10:00:00+07', TIMESTAMPTZ '2026-04-02 10:00:00+07'),
    ('TT-2026-110', 'KH0001', 'HD2026001', DATE '2026-04-01', DATE '2026-04-30', 17500000, 1750000, 19250000, 'DRAFT', NULL, TIMESTAMPTZ '2026-04-30 08:00:00+07', TIMESTAMPTZ '2026-04-30 08:00:00+07'),
    ('TT-2026-111', 'KH0002', 'HD2026002', DATE '2026-04-01', DATE '2026-04-30', 16500000, 1650000, 18150000, 'PENDING_APPROVAL', 'approval-2026-111', TIMESTAMPTZ '2026-04-30 09:00:00+07', TIMESTAMPTZ '2026-04-30 09:30:00+07'),
    ('TT-2026-112', 'KH0005', 'HD2026003', DATE '2026-04-01', DATE '2026-04-30', 24000000, 2400000, 26400000, 'APPROVED', 'approval-2026-112', TIMESTAMPTZ '2026-04-30 10:00:00+07', TIMESTAMPTZ '2026-05-01 10:00:00+07'),
    ('TT-2026-201', 'KH0001', 'HD2026004', DATE '2026-05-01', DATE '2026-05-31',  4200000,  420000,  4620000, 'REVISION_REQUESTED', 'approval-2026-201', TIMESTAMPTZ '2026-05-31 08:00:00+07', TIMESTAMPTZ '2026-06-01 08:20:00+07'),
    ('TT-2026-202', 'KH0002', 'HD2026005', DATE '2026-06-01', DATE '2026-06-30', 16800000, 1680000, 18480000, 'REVISION_REQUESTED', 'approval-2026-202', TIMESTAMPTZ '2026-06-30 09:00:00+07', TIMESTAMPTZ '2026-07-01 09:15:00+07'),
    ('TT-2026-203', 'KH0003', 'HD2026006', DATE '2026-07-01', DATE '2026-07-31',  5500000,  550000,  6050000, 'REVISION_REQUESTED', 'approval-2026-203', TIMESTAMPTZ '2026-07-31 10:00:00+07', TIMESTAMPTZ '2026-08-01 10:10:00+07'),
    ('TT-2026-204', 'KH0004', 'HD2026007', DATE '2026-08-01', DATE '2026-08-31',  7000000,  700000,  7700000, 'REVISION_REQUESTED', 'approval-2026-204', TIMESTAMPTZ '2026-08-31 11:00:00+07', TIMESTAMPTZ '2026-09-01 11:25:00+07'),
    ('TT-2026-205', 'KH0005', 'HD2026008', DATE '2026-09-01', DATE '2026-09-30', 19200000, 1920000, 21120000, 'REVISION_REQUESTED', 'approval-2026-205', TIMESTAMPTZ '2026-09-30 13:00:00+07', TIMESTAMPTZ '2026-10-01 13:20:00+07'),
    ('TT-2026-206', 'KH0001', 'HD2026001', DATE '2026-05-01', DATE '2026-05-31', 17500000, 1750000, 19250000, 'REVISION_REQUESTED', 'approval-2026-206', TIMESTAMPTZ '2026-05-31 14:00:00+07', TIMESTAMPTZ '2026-06-01 14:30:00+07')
ON CONFLICT (contract_id, period_start, period_end) DO UPDATE
SET customer_id = EXCLUDED.customer_id,
    subtotal = EXCLUDED.subtotal,
    tax_amount = EXCLUDED.tax_amount,
    total_amount = EXCLUDED.total_amount,
    status = EXCLUDED.status,
    approval_instance_id = EXCLUDED.approval_instance_id,
    created_at = EXCLUDED.created_at,
    updated_at = EXCLUDED.updated_at;

DELETE FROM payment_adjustments WHERE payment_id IN (
    'TT-2026-101', 'TT-2026-102', 'TT-2026-103', 'TT-2026-104',
    'TT-2026-105', 'TT-2026-106', 'TT-2026-107', 'TT-2026-108',
    'TT-2026-109', 'TT-2026-110', 'TT-2026-111', 'TT-2026-112',
    'TT-2026-201', 'TT-2026-202', 'TT-2026-203', 'TT-2026-204',
    'TT-2026-205', 'TT-2026-206'
);

DELETE FROM payment_lines WHERE payment_id IN (
    'TT-2026-101', 'TT-2026-102', 'TT-2026-103', 'TT-2026-104',
    'TT-2026-105', 'TT-2026-106', 'TT-2026-107', 'TT-2026-108',
    'TT-2026-109', 'TT-2026-110', 'TT-2026-111', 'TT-2026-112',
    'TT-2026-201', 'TT-2026-202', 'TT-2026-203', 'TT-2026-204',
    'TT-2026-205', 'TT-2026-206'
);

INSERT INTO payment_lines (
    id, payment_id, service_id, description, confirmed_quantity,
    billing_quantity, unit_price_snapshot, line_amount, tax_rate, tax_amount
)
SELECT md5(p.id || ':history-line'), p.id, seed.service_id, seed.description,
       seed.quantity, seed.quantity, seed.unit_price, p.subtotal, 0.1000, p.tax_amount
FROM payments p
JOIN (VALUES
    ('TT-2026-101', 'DV001', 'Bốc xếp Container 20ft', 20.0000, 350000.00),
    ('TT-2026-102', 'DV002', 'Bốc xếp Container 40ft', 15.0000, 550000.00),
    ('TT-2026-103', 'DV003', 'Lưu kho', 100.0000, 120000.00),
    ('TT-2026-104', 'DV001', 'Bốc xếp Container 20ft', 30.0000, 350000.00),
    ('TT-2026-105', 'DV002', 'Bốc xếp Container 40ft', 20.0000, 550000.00),
    ('TT-2026-106', 'DV003', 'Lưu kho', 120.0000, 120000.00),
    ('TT-2026-107', 'DV001', 'Bốc xếp Container 20ft', 40.0000, 350000.00),
    ('TT-2026-108', 'DV002', 'Bốc xếp Container 40ft', 25.0000, 550000.00),
    ('TT-2026-109', 'DV003', 'Lưu kho', 150.0000, 120000.00),
    ('TT-2026-110', 'DV001', 'Bốc xếp Container 20ft', 50.0000, 350000.00),
    ('TT-2026-111', 'DV002', 'Bốc xếp Container 40ft', 30.0000, 550000.00),
    ('TT-2026-112', 'DV003', 'Lưu kho', 200.0000, 120000.00),
    ('TT-2026-201', 'DV001', 'Bốc xếp Container 20ft', 12.0000, 350000.00),
    ('TT-2026-202', 'DV003', 'Lưu kho', 140.0000, 120000.00),
    ('TT-2026-203', 'DV002', 'Bốc xếp Container 40ft', 10.0000, 550000.00),
    ('TT-2026-204', 'DV001', 'Bốc xếp Container 20ft', 20.0000, 350000.00),
    ('TT-2026-205', 'DV003', 'Lưu kho', 160.0000, 120000.00),
    ('TT-2026-206', 'DV001', 'Bốc xếp Container 20ft', 50.0000, 350000.00)
) AS seed(payment_id, service_id, description, quantity, unit_price)
  ON seed.payment_id = p.id;

-- Hồ sơ REVISION_REQUESTED chưa có REVISION_ADJUSTMENT.
-- Bản ghi lịch sử chỉ được tạo sau khi kế toán thực sự sửa thuế suất và gửi lại.

COMMIT;
