CREATE TABLE payment_number_sequences (
    year INTEGER PRIMARY KEY,
    last_number INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT ck_payment_number_sequences_range
        CHECK (last_number >= 0 AND last_number <= 999)
);

CREATE TABLE payments (
    id VARCHAR(36) PRIMARY KEY,
    customer_id VARCHAR(100) NOT NULL,
    contract_id VARCHAR(100) NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    subtotal NUMERIC(18, 2) NOT NULL,
    tax_amount NUMERIC(18, 2) NOT NULL,
    total_amount NUMERIC(18, 2) NOT NULL,
    status VARCHAR(30) NOT NULL,
    approval_instance_id VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_payments_customer_id ON payments(customer_id);
CREATE INDEX ix_payments_contract_id ON payments(contract_id);

CREATE TABLE payment_lines (
    id VARCHAR(36) PRIMARY KEY,
    payment_id VARCHAR(36) NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
    service_id VARCHAR(100) NOT NULL,
    description VARCHAR(255) NOT NULL,
    confirmed_quantity NUMERIC(18, 4) NOT NULL CHECK (confirmed_quantity > 0),
    billing_quantity NUMERIC(18, 4) NOT NULL CHECK (
        billing_quantity > 0 AND billing_quantity <= confirmed_quantity
    ),
    unit_price_snapshot NUMERIC(18, 2) NOT NULL CHECK (unit_price_snapshot >= 0),
    line_amount NUMERIC(18, 2) NOT NULL,
    tax_rate NUMERIC(5, 4) NOT NULL CHECK (tax_rate >= 0 AND tax_rate <= 1),
    tax_amount NUMERIC(18, 2) NOT NULL
);

CREATE INDEX ix_payment_lines_payment_id ON payment_lines(payment_id);

CREATE TABLE payment_adjustments (
    id VARCHAR(36) PRIMARY KEY,
    payment_id VARCHAR(36) NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
    reason TEXT NOT NULL,
    amount NUMERIC(18, 2) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'DRAFT',
    change_type VARCHAR(30) NOT NULL DEFAULT 'MANUAL_AMOUNT',
    action VARCHAR(20),
    revision_request_id VARCHAR(100),
    service_id VARCHAR(100),
    confirmed_quantity NUMERIC(18, 4),
    previous_billing_quantity NUMERIC(18, 4),
    new_billing_quantity NUMERIC(18, 4),
    previous_tax_rate NUMERIC(5, 4),
    new_tax_rate NUMERIC(5, 4),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_payment_adjustments_payment_id ON payment_adjustments(payment_id);
