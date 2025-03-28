"""Script to reset the database by dropping and recreating tables."""

import os
import psycopg2
from dotenv import load_dotenv

def read_schema():
    """Read the schema file."""
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'db', 'schema.sql')
    with open(schema_path, 'r') as f:
        return f.read()

def reset_database():
    """Drop and recreate the database tables."""
    load_dotenv()
    
    # Get database connection parameters
    host = os.getenv('PG_HOST')
    port = os.getenv('PG_PORT')
    dbname = os.getenv('PG_DB')
    user = os.getenv('PG_USER')
    password = os.getenv('PG_PASS')
    
    # Connect to database
    conn = psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password
    )
    
    try:
        # Drop existing tables and functions
        with conn.cursor() as cur:
            # Drop trigger first
            cur.execute("""
                DROP TRIGGER IF EXISTS update_mining_companies_updated_at ON mining_companies;
            """)
            
            # Drop function with CASCADE
            cur.execute("""
                DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;
            """)
            
            # Drop table
            cur.execute("""
                DROP TABLE IF EXISTS mining_companies CASCADE;
            """)
            
            # Read and execute schema
            schema = read_schema()
            cur.execute(schema)
        
        # Commit changes
        conn.commit()
        print("Database reset successfully")
        
    except Exception as e:
        print(f"Error resetting database: {str(e)}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == '__main__':
    reset_database() 