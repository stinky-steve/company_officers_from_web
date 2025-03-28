"""Script to add management fields to the mining_companies table.
This is a one-time setup script. Do not run this script if the fields already exist.
"""

import os
import psycopg2
from dotenv import load_dotenv

def add_management_fields():
    """Add management fields to the mining_companies table if they don't exist."""
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
    
    # Connect to database
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()
    
    try:
        # Check if fields exist
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'mining_companies' 
            AND column_name IN ('officers', 'board_members', 'data_source');
        """)
        existing_fields = [row[0] for row in cur.fetchall()]
        
        if existing_fields:
            print("Warning: Some management fields already exist:")
            for field in existing_fields:
                print(f"- {field}")
            print("\nThis script should only be run once to add the fields.")
            print("If you need to modify the fields, please create a separate migration script.")
            return
        
        # Add officers field
        cur.execute("""
            ALTER TABLE mining_companies 
            ADD COLUMN officers JSONB DEFAULT '[]'::jsonb;
        """)
        
        # Add board_members field
        cur.execute("""
            ALTER TABLE mining_companies 
            ADD COLUMN board_members JSONB DEFAULT '[]'::jsonb;
        """)
        
        # Add data_source field
        cur.execute("""
            ALTER TABLE mining_companies 
            ADD COLUMN data_source JSONB DEFAULT '{"officers": "local", "board_members": "local"}'::jsonb;
        """)
        
        # Create indexes
        cur.execute("""
            CREATE INDEX idx_mining_companies_officers ON mining_companies USING GIN (officers);
            CREATE INDEX idx_mining_companies_board_members ON mining_companies USING GIN (board_members);
        """)
        
        # Commit changes
        conn.commit()
        print("Successfully added management fields to mining_companies table")
        print("Note: This is a one-time setup. Do not run this script again.")
        
    except Exception as e:
        print(f"Error adding management fields: {str(e)}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    add_management_fields() 