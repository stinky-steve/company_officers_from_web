"""Script to create the mining_companies table in the LGI database.
This is a one-time setup script. Do not run this script if the table already exists.
"""

import os
import psycopg2
from dotenv import load_dotenv

def create_mining_companies_table():
    """Create the mining_companies table in the LGI database if it doesn't exist."""
    # Load environment variables
    load_dotenv()
    
    # Get database connection parameters
    db_params = {
        'dbname': os.getenv('PG_DB'),
        'user': os.getenv('PG_USER'),
        'password': os.getenv('PG_PASS'),
        'host': os.getenv('PG_HOST'),
        'port': os.getenv('PG_PORT')
    }
    
    # Print connection parameters (without password)
    print("Attempting to connect with parameters:")
    print(f"Host: {db_params['host']}")
    print(f"Port: {db_params['port']}")
    print(f"Database: {db_params['dbname']}")
    print(f"User: {db_params['user']}")
    
    # Connect to database
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()
    
    try:
        # Check if table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'mining_companies'
            );
        """)
        table_exists = cur.fetchone()[0]
        
        if table_exists:
            print("Warning: mining_companies table already exists!")
            print("This script should only be run once to create the table.")
            print("If you need to modify the table structure, please create a separate migration script.")
            return
        
        # Create mining_companies table
        cur.execute("""
            CREATE TABLE mining_companies (
                id SERIAL PRIMARY KEY,
                website VARCHAR(255) NOT NULL UNIQUE,
                company_name VARCHAR(255) NOT NULL UNIQUE,
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
        """)
        
        # Create indexes
        cur.execute("""
            CREATE INDEX idx_mining_companies_name ON mining_companies(company_name);
            CREATE INDEX idx_mining_companies_ticker ON mining_companies(ticker);
            CREATE INDEX idx_mining_companies_exchange ON mining_companies(exchange);
            CREATE INDEX idx_mining_companies_officers ON mining_companies USING GIN (officers);
            CREATE INDEX idx_mining_companies_board_members ON mining_companies USING GIN (board_members);
        """)
        
        # Create function to update updated_at timestamp
        cur.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        """)
        
        # Create trigger to automatically update updated_at
        cur.execute("""
            CREATE TRIGGER update_mining_companies_updated_at
                BEFORE UPDATE ON mining_companies
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
        """)
        
        # Commit changes
        conn.commit()
        print("Successfully created mining_companies table in LGI database")
        print("Note: This is a one-time setup. Do not run this script again.")
        
    except Exception as e:
        print(f"Error creating mining_companies table: {str(e)}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    create_mining_companies_table() 