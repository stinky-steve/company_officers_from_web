-- Create the mining_companies table
CREATE TABLE IF NOT EXISTS mining_companies (
    id SERIAL PRIMARY KEY,
    website VARCHAR(255) NOT NULL UNIQUE,
    company_name VARCHAR(255) NOT NULL,
    ticker VARCHAR(50),
    exchange VARCHAR(50),
    headquarters_location VARCHAR(255),
    founded_date DATE,
    description TEXT,
    officers JSONB DEFAULT '[]'::jsonb,
    board_members JSONB DEFAULT '[]'::jsonb,
    data_source JSONB DEFAULT '{"officers": "local", "board_members": "local"}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index on company name
CREATE INDEX IF NOT EXISTS idx_mining_companies_name ON mining_companies(company_name);

-- Create index on ticker
CREATE INDEX IF NOT EXISTS idx_mining_companies_ticker ON mining_companies(ticker);

-- Create index on exchange
CREATE INDEX IF NOT EXISTS idx_mining_companies_exchange ON mining_companies(exchange);

-- Create index on officers
CREATE INDEX IF NOT EXISTS idx_mining_companies_officers ON mining_companies USING GIN (officers);

-- Create index on board members
CREATE INDEX IF NOT EXISTS idx_mining_companies_board_members ON mining_companies USING GIN (board_members);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_mining_companies_updated_at
    BEFORE UPDATE ON mining_companies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column(); 