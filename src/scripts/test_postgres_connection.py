import os
import sys
import psycopg2
from dotenv import load_dotenv

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

def test_postgres_connection():
    """Test PostgreSQL connection and retrieve table information."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get database connection parameters
        host = os.getenv('PG_HOST')
        port = os.getenv('PG_PORT')
        dbname = os.getenv('PG_DB')
        user = os.getenv('PG_USER')
        password = os.getenv('PG_PASS')
        
        print(f"Attempting to connect to PostgreSQL database:")
        print(f"Host: {host}")
        print(f"Port: {port}")
        print(f"Database: {dbname}")
        print(f"User: {user}")
        
        # Establish connection
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password
        )
        
        print("\nSuccessfully connected to PostgreSQL database!")
        
        # Create a cursor
        cur = conn.cursor()
        
        # Get list of tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = cur.fetchall()
        
        print("\nTables in the database:")
        print("-" * 50)
        
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            
            # Get column information for each table
            cur.execute(f"""
                SELECT column_name, data_type, character_maximum_length
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position;
            """)
            
            columns = cur.fetchall()
            print("Columns:")
            for col in columns:
                col_name, data_type, max_length = col
                length_info = f" (max length: {max_length})" if max_length else ""
                print(f"  - {col_name}: {data_type}{length_info}")
        
        # Close cursor and connection
        cur.close()
        conn.close()
        
        print("\nDatabase connection test completed successfully!")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    test_postgres_connection() 