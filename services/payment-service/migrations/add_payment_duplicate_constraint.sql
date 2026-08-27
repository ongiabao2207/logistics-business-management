ALTER TABLE payments
ADD CONSTRAINT uq_payments_contract_period
UNIQUE (contract_id, period_start, period_end);