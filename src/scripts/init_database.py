"""Script to initialize the database with the schema."""

import os
import psycopg2
from dotenv import load_dotenv

def read_schema():
    """Read the schema file."""
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'db', 'schema.sql')
    with open(schema_path, 'r') as f:
        return f.read()

def init_database():
    """Initialize the database with the schema."""
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
        # Read schema
        schema = read_schema()
        
        # Execute schema
        with conn.cursor() as cur:
            cur.execute(schema)
        
        # Commit changes
        conn.commit()
        print("Database initialized successfully")
        
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == '__main__':
    init_database() 