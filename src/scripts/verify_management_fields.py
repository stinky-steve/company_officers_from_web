"""Script to verify the structure of management fields in the mining_companies table."""

import os
import psycopg2
from dotenv import load_dotenv

def verify_management_fields():
    """Verify the structure of management fields in the mining_companies table."""
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
        # Check column types
        cur.execute("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns
            WHERE table_name = 'mining_companies'
            AND column_name IN ('officers', 'board_members', 'data_source');
        """)
        
        print("\nManagement field types:")
        for row in cur.fetchall():
            print(f"\nField: {row[0]}")
            print(f"Type: {row[1]}")
            print(f"Default: {row[2]}")
        
        # Check indexes
        cur.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'mining_companies'
            AND indexname LIKE 'idx_mining_companies_%';
        """)
        
        print("\nManagement field indexes:")
        for row in cur.fetchall():
            print(f"\nIndex: {row[0]}")
            print(f"Definition: {row[1]}")
        
        # Get sample data
        print("\nSample data from first company:")
        cur.execute("""
            SELECT company_name, officers, board_members, data_source
            FROM mining_companies
            LIMIT 1;
        """)
        
        row = cur.fetchone()
        if row:
            print(f"\nCompany: {row[0]}")
            print(f"Officers: {row[1]}")
            print(f"Board Members: {row[2]}")
            print(f"Data Source: {row[3]}")
            
    except Exception as e:
        print(f"Error verifying management fields: {str(e)}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    verify_management_fields() 