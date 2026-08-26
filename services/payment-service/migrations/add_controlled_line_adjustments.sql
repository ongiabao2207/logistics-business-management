ALTER TABLE payment_lines
RENAME COLUMN quantity TO confirmed_quantity;

ALTER TABLE payment_lines
ADD COLUMN billing_quantity NUMERIC(18, 4);

UPDATE payment_lines
SET billing_quantity = confirmed_quantity;

ALTER TABLE payment_lines
ALTER COLUMN billing_quantity SET NOT NULL;

ALTER TABLE payment_lines
ADD CONSTRAINT ck_payment_lines_confirmed_quantity_positive
CHECK (confirmed_quantity > 0);

ALTER TABLE payment_lines
ADD CONSTRAINT ck_payment_lines_billing_quantity_range
CHECK (
    billing_quantity > 0
    AND billing_quantity <= confirmed_quantity
);

ALTER TABLE payment_lines
ADD CONSTRAINT ck_payment_lines_unit_price_non_negative
CHECK (unit_price_snapshot >= 0);

ALTER TABLE payment_lines
ADD CONSTRAINT ck_payment_lines_tax_rate_range
CHECK (tax_rate >= 0 AND tax_rate <= 1);

ALTER TABLE payment_adjustments
ADD COLUMN change_type VARCHAR(30) NOT NULL DEFAULT 'MANUAL_AMOUNT',
ADD COLUMN action VARCHAR(20),
ADD COLUMN revision_request_id VARCHAR(100),
ADD COLUMN service_id VARCHAR(100),
ADD COLUMN confirmed_quantity NUMERIC(18, 4),
ADD COLUMN previous_billing_quantity NUMERIC(18, 4),
ADD COLUMN new_billing_quantity NUMERIC(18, 4),
ADD COLUMN previous_tax_rate NUMERIC(5, 4),
ADD COLUMN new_tax_rate NUMERIC(5, 4);
