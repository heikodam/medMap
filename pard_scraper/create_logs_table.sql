-- Create scrape_logs table to track scraper runs
CREATE TABLE scrape_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scrape_type TEXT NOT NULL,
    total_items INTEGER NOT NULL,
    status TEXT NOT NULL,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for better performance when querying by scrape_type
CREATE INDEX idx_scrape_logs_scrape_type ON scrape_logs(scrape_type);

-- Create index for better performance when querying by status
CREATE INDEX idx_scrape_logs_status ON scrape_logs(status); 