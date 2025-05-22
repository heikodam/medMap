-- Create scrape_log table to track scraper runs
CREATE TABLE scrape_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scrape_type TEXT NOT NULL,
    total_items INTEGER NOT NULL,
    status TEXT NOT NULL,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Add indexes for faster querying
CREATE INDEX idx_scrape_log_scrape_type ON scrape_log(scrape_type);
CREATE INDEX idx_scrape_log_created_at ON scrape_log(created_at);
CREATE INDEX idx_scrape_log_status ON scrape_log(status); 