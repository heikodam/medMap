-- Create cognism_companies table
CREATE TABLE IF NOT EXISTS cognism_companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    apollo_company_id TEXT REFERENCES apollo_companies(apollo_id),
    eudamed_company_id UUID REFERENCES eudamed_companies(id),
    cognism_id TEXT UNIQUE NOT NULL,
    name TEXT,
    domain TEXT,
    type TEXT,
    headcount INTEGER,
    size_from INTEGER,
    size_to INTEGER,
    revenue DECIMAL,
    linkedin_url TEXT,
    website TEXT,
    founded INTEGER,
    last_confirmed TIMESTAMP WITH TIME ZONE,
    short_description TEXT,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create cognism_locations table
CREATE TABLE IF NOT EXISTS cognism_locations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cognism_company_id UUID REFERENCES cognism_companies(id) ON DELETE CASCADE,
    city_id INTEGER REFERENCES cities(id),
    country_iso_code CHAR(2) REFERENCES countries(iso_code),
    address_type TEXT,
    state TEXT,
    street TEXT,
    zip TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create cognism_contacts table
CREATE TABLE IF NOT EXISTS cognism_contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cognism_id TEXT UNIQUE NOT NULL,
    cognism_redeem_id TEXT,
    first_name TEXT,
    last_name TEXT,
    full_name TEXT,
    job_title TEXT,
    email TEXT,
    email_quality TEXT,
    email_sha256 TEXT,
    linkedin_url TEXT,
    country TEXT,
    management_level TEXT,
    position_start_date TEXT,
    last_confirmed TIMESTAMP WITH TIME ZONE,
    privacy_notification_sent BOOLEAN,
    cognism_company_id UUID REFERENCES cognism_companies(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE
);

-- Create tags table
CREATE TABLE IF NOT EXISTS tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cognism_company_id UUID REFERENCES cognism_companies(id) ON DELETE CASCADE,
    cognism_contact_id UUID REFERENCES cognism_contacts(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    category TEXT NOT NULL, -- 'technology', 'industry', etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT require_one_reference CHECK (
        (cognism_company_id IS NOT NULL AND cognism_contact_id IS NULL) OR
        (cognism_company_id IS NULL AND cognism_contact_id IS NOT NULL)
    )
);

-- Create cognism_employment_history table
CREATE TABLE IF NOT EXISTS cognism_employment_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cognism_contact_id UUID REFERENCES cognism_contacts(id) ON DELETE CASCADE,
    company_name TEXT,
    title TEXT,
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create cognism_education table
CREATE TABLE IF NOT EXISTS cognism_education (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cognism_contact_id UUID REFERENCES cognism_contacts(id) ON DELETE CASCADE,
    school TEXT,
    degree TEXT,
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create cognism_job_events table
CREATE TABLE IF NOT EXISTS cognism_job_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cognism_contact_id UUID REFERENCES cognism_contacts(id) ON DELETE CASCADE,
    event_date DATE,
    event_type TEXT, -- 'leave' or 'join'
    from_company TEXT,
    from_title TEXT,
    to_company TEXT,
    to_title TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Modify phone_numbers table to include cognism-specific fields
ALTER TABLE phone_numbers
ADD COLUMN IF NOT EXISTS score INTEGER,
ADD COLUMN IF NOT EXISTS cognism_company_id UUID REFERENCES cognism_companies(id) ON DELETE CASCADE,
ADD COLUMN IF NOT EXISTS cognism_contact_id UUID REFERENCES cognism_contacts(id) ON DELETE CASCADE;

-- Create updated_at triggers for all new tables
CREATE TRIGGER update_cognism_companies_updated_at
    BEFORE UPDATE ON cognism_companies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cognism_locations_updated_at
    BEFORE UPDATE ON cognism_locations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tags_updated_at
    BEFORE UPDATE ON tags
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cognism_contacts_updated_at
    BEFORE UPDATE ON cognism_contacts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cognism_employment_history_updated_at
    BEFORE UPDATE ON cognism_employment_history
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cognism_education_updated_at
    BEFORE UPDATE ON cognism_education
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cognism_job_events_updated_at
    BEFORE UPDATE ON cognism_job_events
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_cognism_companies_apollo_company_id
ON cognism_companies(apollo_company_id);

CREATE INDEX IF NOT EXISTS idx_cognism_companies_eudamed_company_id
ON cognism_companies(eudamed_company_id);

CREATE INDEX IF NOT EXISTS idx_cognism_companies_cognism_id
ON cognism_companies(cognism_id);

CREATE INDEX IF NOT EXISTS idx_cognism_locations_company_id
ON cognism_locations(cognism_company_id);

CREATE INDEX IF NOT EXISTS idx_tags_company_id
ON tags(cognism_company_id);

CREATE INDEX IF NOT EXISTS idx_tags_contact_id
ON tags(cognism_contact_id);

CREATE INDEX IF NOT EXISTS idx_cognism_contacts_company_id
ON cognism_contacts(cognism_company_id);

CREATE INDEX IF NOT EXISTS idx_cognism_contacts_cognism_id
ON cognism_contacts(cognism_id);

CREATE INDEX IF NOT EXISTS idx_cognism_employment_history_contact_id
ON cognism_employment_history(cognism_contact_id);

CREATE INDEX IF NOT EXISTS idx_cognism_education_contact_id
ON cognism_education(cognism_contact_id);

CREATE INDEX IF NOT EXISTS idx_cognism_job_events_contact_id
ON cognism_job_events(cognism_contact_id); 