CREATE TABLE IF NOT EXISTS customer_info (
    id VARCHAR(20) PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    company_type VARCHAR(100) NOT NULL,
    tax_code VARCHAR(50) NOT NULL UNIQUE,
    address VARCHAR(500) NOT NULL,
    contact_name VARCHAR(255) NOT NULL,
    contact_email VARCHAR(255) NOT NULL,
    contact_phone VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO customer_info (
    id,
    company_name,
    company_type,
    tax_code,
    address,
    contact_name,
    contact_email,
    contact_phone,
    status
)
VALUES
    (
        'KH0001',
        'Samsung Electronics HCMC',
        'Logistics',
        '0312345678',
        'Ho Chi Minh City',
        'Nguyen Van An',
        'an.nguyen@samsung.example',
        '0901234567',
        'ACTIVE'
    ),
    (
        'KH0002',
        'Vinamilk',
        'FMCG',
        '0300588569',
        'Ho Chi Minh City',
        'Tran Thi Binh',
        'binh.tran@vinamilk.example',
        '0902345678',
        'ACTIVE'
    ),
    (
        'KH0003',
        'Thaco Logistics',
        'Logistics',
        '4000123456',
        'Quang Nam',
        'Le Minh Cuong',
        'cuong.le@thacologistics.example',
        '0903456789',
        'ACTIVE'
    ),
    (
        'KH0004',
        'Nestle Viet Nam',
        'FMCG',
        '0302012345',
        'Dong Nai',
        'Pham Thu Dung',
        'dung.pham@nestle.example',
        '0904567890',
        'ACTIVE'
    ),
    (
        'KH0005',
        'Intel Products Vietnam',
        'Manufacturing',
        '0309876543',
        'Ho Chi Minh City',
        'Hoang Gia Huy',
        'huy.hoang@intel.example',
        '0905678901',
        'ACTIVE'
    )
ON CONFLICT (id) DO NOTHING;
