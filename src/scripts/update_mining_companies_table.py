import os
import sys
import psycopg2
from dotenv import load_dotenv

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

def update_mining_companies_table():
    """Update mining_companies table with additional fields and JSONB columns."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get database connection parameters
        host = os.getenv('PG_HOST')
        port = os.getenv('PG_PORT')
        dbname = os.getenv('PG_DB')
        user = os.getenv('PG_USER')
        password = os.getenv('PG_PASS')
        
        print(f"Attempting to connect to PostgreSQL database...")
        
        # Establish connection
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password
        )
        
        print("Successfully connected to PostgreSQL database!")
        
        # Create a cursor
        cur = conn.cursor()
        
        # Drop existing table if it exists
        cur.execute("DROP TABLE IF EXISTS mining_companies CASCADE;")
        
        # Create updated mining_companies table
        cur.execute("""
            CREATE TABLE mining_companies (
                id SERIAL PRIMARY KEY,
                website TEXT,
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
        
        # Create indexes for better query performance
        cur.execute("""
            -- Basic indexes
            CREATE INDEX idx_mining_companies_name 
            ON mining_companies(company_name);
            
            CREATE INDEX idx_mining_companies_ticker 
            ON mining_companies(ticker);
            
            CREATE INDEX idx_mining_companies_website 
            ON mining_companies(website);
            
            -- GIN indexes for JSONB columns
            CREATE INDEX idx_mining_companies_officers 
            ON mining_companies USING GIN (officers jsonb_path_ops);
            
            CREATE INDEX idx_mining_companies_board_members 
            ON mining_companies USING GIN (board_members jsonb_path_ops);
            
            -- Expression indexes for common JSONB queries
            CREATE INDEX idx_mining_companies_officer_names 
            ON mining_companies USING btree ((officers->>'name'));
            
            CREATE INDEX idx_mining_companies_officer_titles 
            ON mining_companies USING btree ((officers->>'title'));
            
            CREATE INDEX idx_mining_companies_board_names 
            ON mining_companies USING btree ((board_members->>'name'));
            
            CREATE INDEX idx_mining_companies_board_titles 
            ON mining_companies USING btree ((board_members->>'title'));
        """)
        
        # Create trigger function for updating updated_at timestamp
        cur.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        """)
        
        # Create trigger for updated_at
        cur.execute("""
            DROP TRIGGER IF EXISTS update_mining_companies_updated_at ON mining_companies;
            CREATE TRIGGER update_mining_companies_updated_at
                BEFORE UPDATE ON mining_companies
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
        """)
        
        # Commit the transaction
        conn.commit()
        
        print("\nSuccessfully updated table structure!")
        print("\nTable structure:")
        print("-" * 50)
        
        # Display table structure
        cur.execute("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'mining_companies'
            ORDER BY ordinal_position;
        """)
        
        columns = cur.fetchall()
        for col in columns:
            col_name, data_type, max_length = col
            length_info = f" (max length: {max_length})" if max_length else ""
            print(f"  - {col_name}: {data_type}{length_info}")
        
        # Close cursor and connection
        cur.close()
        conn.close()
        
        print("\nDatabase table updated successfully!")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    update_mining_companies_table() 