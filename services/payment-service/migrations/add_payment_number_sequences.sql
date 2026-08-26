CREATE TABLE payment_number_sequences (
    year INTEGER PRIMARY KEY,
    last_number INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT ck_payment_number_sequences_range
        CHECK (last_number >= 0 AND last_number <= 999)
);
