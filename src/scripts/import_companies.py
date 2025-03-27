import os
import sys
import csv
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_values

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

def import_companies():
    """Import company data from CSV into the mining_companies table."""
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
        
        # Path to CSV file
        csv_file = os.path.join(project_root, 'data', 'raw', 'mining_companies_websites_19_Mar_2025.csv')
        
        # Read CSV file and prepare data for insertion
        companies = []
        skipped = []
        
        print("\nReading CSV file...")
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, start=2):  # start=2 because row 1 is header
                # Skip rows where company name is empty
                if not row.get('Company Name'):
                    skipped.append(f"Row {i}: Empty company name")
                    continue
                    
                companies.append((
                    row.get('Website', ''),  # Use empty string if website is None
                    row['Company Name'],
                    row.get('Ticker', ''),
                    row.get('Exchange', ''),
                    None,  # headquarters_location
                    None,  # founded_date
                    None,  # description
                    '[]',  # officers (empty JSONB array)
                    '[]'   # board_members (empty JSONB array)
                ))
        
        print(f"\nPrepared {len(companies)} companies for import...")
        if skipped:
            print(f"Skipped {len(skipped)} rows:")
            for msg in skipped[:5]:  # Show first 5 skipped entries
                print(f"  - {msg}")
            if len(skipped) > 5:
                print(f"  ... and {len(skipped) - 5} more")
        
        # Insert data using execute_values for better performance
        insert_query = """
            INSERT INTO mining_companies (
                website,
                company_name,
                ticker,
                exchange,
                headquarters_location,
                founded_date,
                description,
                officers,
                board_members
            )
            VALUES %s
            ON CONFLICT (company_name) 
            DO UPDATE SET
                website = EXCLUDED.website,
                ticker = EXCLUDED.ticker,
                exchange = EXCLUDED.exchange
            RETURNING id, company_name;
        """
        
        print("\nInserting data into database...")
        results = execute_values(
            cur, 
            insert_query, 
            companies,
            template=None,
            page_size=100,
            fetch=True
        )
        
        # Commit the transaction
        conn.commit()
        
        print("\nImport Results:")
        print("-" * 50)
        print(f"Total companies processed: {len(companies)}")
        print(f"Successfully imported: {len(results)}")
        
        # Display first few imported companies
        print("\nSample of imported companies:")
        for i, (id, name) in enumerate(results[:5]):
            print(f"  {i+1}. {name} (ID: {id})")
        
        # Close cursor and connection
        cur.close()
        conn.close()
        
        print("\nDatabase import completed successfully!")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    import_companies() 