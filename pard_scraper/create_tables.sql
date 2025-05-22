-- Create pard_companies table
CREATE TABLE pard_companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    man_organisation_id INTEGER,
    man_created_date TIMESTAMPTZ,
    man_organisation_name TEXT,
    man_addr_line_1 TEXT,
    man_addr_line_2 TEXT,
    man_addr_line_3 TEXT,
    man_addr_line_4 TEXT,
    man_city TEXT,
    man_countystateprovince TEXT,
    man_country TEXT,
    rep_name TEXT,
    rep_address_line_1 TEXT,
    rep_address_line_2 TEXT,
    rep_address_line_3 TEXT,
    rep_address_line_4 TEXT,
    rep_city TEXT,
    rep_county_state_province TEXT,
    rep_country TEXT,
    relationship TEXT,
    last_updated_date TIMESTAMPTZ,
    man_account_number INTEGER,
    man_postcode TEXT,
    rep_postcode TEXT,
    rep_organisation_id INTEGER,
    customer_service_email_address TEXT,
    customer_service_telephone_number TEXT,
    rep_customer_service_email_address TEXT,
    rep_customer_service_telephone_number TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create pard_devices table
CREATE TABLE pard_devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pard_companies_id UUID REFERENCES pard_companies(id),
    man_organisation_id INTEGER,
    device_id INTEGER,
    gmdn_code INTEGER,
    gmdn_term_name TEXT,
    device_sub_type_desc TEXT,
    is_custom_made TEXT,
    is_performance_studies TEXT,
    device_reg_status_code TEXT,
    device_type_name TEXT,
    last_updated_date TIMESTAMPTZ,
    certificate_id INTEGER,
    is_incorpporate_custommade_medical_device TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_pard_companies_man_organisation_id ON pard_companies(man_organisation_id);
CREATE INDEX idx_pard_devices_device_id ON pard_devices(device_id);
CREATE INDEX idx_pard_devices_man_organisation_id ON pard_devices(man_organisation_id); 