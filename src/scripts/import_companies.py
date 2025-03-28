"""Script to import company data from CSV into the mining_companies table."""

import os
import sys
import csv
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_values

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

def normalize_website_url(url):
    """Normalize website URL by adding https:// if needed."""
    if not url:
        return None
    url = url.strip()
    if not url:
        return None
    if not url.startswith('http://') and not url.startswith('https://'):
        url = f"https://{url}"
    return url

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
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            # Read the first few lines for debugging
            print("\nFirst few lines of the CSV file:")
            for i, line in enumerate(f):
                if i < 5:
                    print(f"Line {i+1}: {line.strip()}")
            
            # Reset file pointer to beginning
            f.seek(0)
            
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, start=2):  # start=2 because row 1 is header
                # Debug output for first few rows
                if i <= 5:
                    print(f"\nProcessing Row {i}:")
                    print(f"  Raw Website: '{row.get('Website', '')}'")
                    print(f"  Company: '{row.get('Company Name', '')}'")
                
                # Skip rows where company name is empty
                if not row.get('Company Name'):
                    skipped.append(f"Row {i}: Empty company name")
                    continue
                
                # Use the actual website URL from the CSV, or a placeholder if empty
                website = normalize_website_url(row.get('Website', ''))
                if not website:
                    website = f"http://placeholder/{row['Company Name'].lower().replace(' ', '-')}"
                    skipped.append(f"Row {i}: Using placeholder website")
                
                if i <= 5:
                    print(f"  Processed Website: '{website}'")
                
                companies.append((
                    website,
                    row['Company Name'],
                    row.get('Ticker', ''),
                    row.get('Exchange', ''),
                    None,  # headquarters_location
                    None,  # founded_date
                    None,  # description
                    '[]',  # officers (empty JSONB array)
                    '[]',  # board_members (empty JSONB array)
                    '{"officers": null, "board_members": null}'  # data_source (JSONB)
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
                board_members,
                data_source
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
        
        # Display first few imported companies with their websites
        print("\nSample of imported companies:")
        cur.execute("""
            SELECT id, company_name, website 
            FROM mining_companies 
            WHERE id IN (SELECT id FROM mining_companies LIMIT 5)
        """)
        for i, (id, name, website) in enumerate(cur.fetchall()):
            print(f"  {i+1}. {name} (ID: {id})")
            print(f"     Website: {website}")
        
        # Close cursor and connection
        cur.close()
        conn.close()
        
        print("\nDatabase import completed successfully!")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    import_companies() 