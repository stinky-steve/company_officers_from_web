import os
import sys
import psycopg2
from dotenv import load_dotenv

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

def create_mining_tables():
    """Create mining_companies and mining_people tables in the database."""
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
        
        # Create mining_companies table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS mining_companies (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                ticker_symbol VARCHAR(50),
                website_url TEXT,
                headquarters_location VARCHAR(255),
                founded_date DATE,
                description TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create mining_people table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS mining_people (
                id SERIAL PRIMARY KEY,
                company_id INTEGER REFERENCES mining_companies(id),
                name VARCHAR(255) NOT NULL,
                role VARCHAR(255),
                email VARCHAR(255),
                phone VARCHAR(50),
                source_url TEXT,
                source_title TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create indexes for better query performance
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_mining_companies_name 
            ON mining_companies(name);
            
            CREATE INDEX IF NOT EXISTS idx_mining_companies_ticker 
            ON mining_companies(ticker_symbol);
            
            CREATE INDEX IF NOT EXISTS idx_mining_people_company_id 
            ON mining_people(company_id);
            
            CREATE INDEX IF NOT EXISTS idx_mining_people_name 
            ON mining_people(name);
            
            CREATE INDEX IF NOT EXISTS idx_mining_people_role 
            ON mining_people(role);
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
        
        # Create triggers for both tables
        cur.execute("""
            DROP TRIGGER IF EXISTS update_mining_companies_updated_at ON mining_companies;
            CREATE TRIGGER update_mining_companies_updated_at
                BEFORE UPDATE ON mining_companies
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
                
            DROP TRIGGER IF EXISTS update_mining_people_updated_at ON mining_people;
            CREATE TRIGGER update_mining_people_updated_at
                BEFORE UPDATE ON mining_people
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
        """)
        
        # Commit the transaction
        conn.commit()
        
        print("\nSuccessfully created tables and indexes!")
        print("\nTable structures:")
        print("-" * 50)
        
        # Display table structures
        for table in ['mining_companies', 'mining_people']:
            print(f"\n{table}:")
            cur.execute(f"""
                SELECT column_name, data_type, character_maximum_length
                FROM information_schema.columns
                WHERE table_name = '{table}'
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
        
        print("\nDatabase tables created successfully!")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    create_mining_tables() 