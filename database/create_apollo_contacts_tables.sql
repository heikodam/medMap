-- Create contacts table (renamed from apollo_contacts)
CREATE TABLE IF NOT EXISTS contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    apollo_id TEXT UNIQUE NOT NULL,
    first_name TEXT,
    last_name TEXT,
    name TEXT,
    linkedin_url TEXT,
    title TEXT,
    email_status TEXT,
    photo_url TEXT,
    twitter_url TEXT,
    github_url TEXT,
    facebook_url TEXT,
    extrapolated_email_confidence TEXT,
    headline TEXT,
    email TEXT,
    organization_apollo_id TEXT,
    organization_name TEXT,
    organization_website TEXT,
    organization_linkedin_url TEXT,
    state TEXT,
    city TEXT,
    country TEXT,
    seniority TEXT,
    email_domain_catchall BOOLEAN,
    is_relevant BOOLEAN,
    job_category TEXT,
    scraping_status TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_organization
        FOREIGN KEY (organization_apollo_id)
        REFERENCES apollo_companies(apollo_id)
        ON DELETE SET NULL
);

-- Create apollo_employment_history table
CREATE TABLE IF NOT EXISTS apollo_employment_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_id UUID NOT NULL,
    current BOOLEAN,
    description TEXT,
    end_date DATE,
    organization_apollo_id TEXT,
    organization_name TEXT,
    raw_address TEXT,
    start_date DATE,
    title TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_contact
        FOREIGN KEY (contact_id)
        REFERENCES contacts(id)
        ON DELETE CASCADE
);

-- Create updated_at trigger function if it doesn't exist
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_contacts_updated_at
    BEFORE UPDATE ON contacts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_apollo_employment_history_updated_at
    BEFORE UPDATE ON apollo_employment_history
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_contacts_organization_apollo_id
ON contacts(organization_apollo_id);

CREATE INDEX IF NOT EXISTS idx_apollo_employment_history_contact_id
ON apollo_employment_history(contact_id);

CREATE INDEX IF NOT EXISTS idx_contacts_email
ON contacts(email);

CREATE INDEX IF NOT EXISTS idx_contacts_name
ON contacts(name);

-- Create phone_numbers table
CREATE TABLE IF NOT EXISTS phone_numbers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_id UUID NOT NULL,
    number TEXT NOT NULL,
    source TEXT NOT NULL,
    score INTEGER,
    cognism_company_id UUID REFERENCES cognism_companies(id) ON DELETE CASCADE,
    cognism_contact_id UUID REFERENCES cognism_contacts(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_contact_phone
        FOREIGN KEY (contact_id)
        REFERENCES contacts(id)
        ON DELETE CASCADE
);

-- Create trigger for phone_numbers updated_at
CREATE TRIGGER update_phone_numbers_updated_at
    BEFORE UPDATE ON phone_numbers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create indexes for phone_numbers
CREATE INDEX IF NOT EXISTS idx_phone_numbers_contact_id
ON phone_numbers(contact_id);

CREATE INDEX IF NOT EXISTS idx_phone_numbers_number
ON phone_numbers(number); 