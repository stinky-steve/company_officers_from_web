"""Script to check if mining_companies table has been populated with data."""

import os
import psycopg2
from dotenv import load_dotenv

def check_mining_companies():
    """Check the contents of the mining_companies table."""
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
        # Get total count
        cur.execute("SELECT COUNT(*) FROM mining_companies;")
        total_count = cur.fetchone()[0]
        print(f"\nTotal number of companies in the table: {total_count}")
        
        if total_count == 0:
            print("\nThe table is empty. It needs to be populated with data from mining_companies_websites_19_Mar_2025.csv")
            return
        
        # Get sample of companies
        print("\nSample of companies in the table:")
        cur.execute("""
            SELECT id, company_name, website, ticker, exchange 
            FROM mining_companies 
            LIMIT 5;
        """)
        
        rows = cur.fetchall()
        for row in rows:
            print(f"\nID: {row[0]}")
            print(f"Company: {row[1]}")
            print(f"Website: {row[2]}")
            print(f"Ticker: {row[3]}")
            print(f"Exchange: {row[4]}")
            
    except Exception as e:
        print(f"Error checking mining_companies table: {str(e)}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    check_mining_companies() 