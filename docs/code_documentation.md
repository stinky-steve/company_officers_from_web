# Code Documentation

## Project Overview
This project is designed to extract and store information about mining companies, including their officers and directors, from various web sources.

## Database Schema
The project uses a PostgreSQL database with the following main tables:

### mining_companies
- Primary table storing company information
- Fields:
  - id (SERIAL PRIMARY KEY)
  - website (TEXT)
  - company_name (TEXT UNIQUE)
  - ticker (TEXT)
  - exchange (TEXT)
  - headquarters_location (TEXT)
  - founded_date (DATE)
  - description (TEXT)
  - officers (JSONB)
  - board_members (JSONB)
  - data_source (JSONB)
  - created_at (TIMESTAMP)
  - updated_at (TIMESTAMP)

### company_officers
- Stores detailed information about company officers
- Fields:
  - id (SERIAL PRIMARY KEY)
  - company_id (INTEGER REFERENCES mining_companies)
  - name (TEXT)
  - title (TEXT)
  - bio (TEXT)
  - photo_url (TEXT)
  - created_at (TIMESTAMP)
  - updated_at (TIMESTAMP)

## Code Components

### 1. Database Setup (`src/database/setup.py`)
**Purpose**: Creates and initializes the database schema
**Input**: None
**Output**: Creates database tables if they don't exist
**Key Functions**:
- `create_tables()`: Creates all necessary database tables
- `init_db()`: Initializes the database connection and creates tables

### 2. Company Import (`src/scripts/import_companies.py`)
**Purpose**: Imports company data from CSV into the database
**Input**: CSV file containing company information
**Output**: Populates mining_companies table with basic company data
**Key Functions**:
- `normalize_website_url(url)`: Formats website URLs consistently
- `import_companies()`: Main function that reads CSV and imports data

### 3. Website Scraping (`src/scripts/scrape_company_website.py`)
**Purpose**: Scrapes company websites for officer and director information
**Input**: Company website URL
**Output**: JSON containing officer and director information
**Key Functions**:
- `scrape_company_website(url)`: Main scraping function
- `extract_officers(soup)`: Extracts officer information from HTML
- `extract_directors(soup)`: Extracts director information from HTML

### 4. Officer Information Extraction (`src/scripts/extract_officer_info.py`)
**Purpose**: Extracts detailed information about company officers
**Input**: Company website URL and officer name
**Output**: Detailed officer information including bio and photo URL
**Key Functions**:
- `extract_officer_info(url, officer_name)`: Extracts officer details
- `find_officer_photo(soup, officer_name)`: Finds officer's photo URL

### 5. Database Operations (`src/database/operations.py`)
**Purpose**: Handles database operations for company and officer data
**Input**: Various data structures containing company/officer information
**Output**: Database updates and queries
**Key Functions**:
- `insert_company(company_data)`: Inserts new company
- `update_company(company_id, company_data)`: Updates existing company
- `insert_officer(officer_data)`: Inserts new officer
- `get_company_by_name(name)`: Retrieves company by name

### 6. Main Processing Script (`src/scripts/process_companies.py`)
**Purpose**: Orchestrates the entire process of importing and scraping company data
**Input**: List of company names or CSV file
**Output**: Complete database with company and officer information
**Key Functions**:
- `process_companies(company_names)`: Main processing function
- `process_single_company(company_name)`: Processes individual company

## Data Flow
1. CSV file containing company information is imported via `import_companies.py`
2. Basic company information is stored in the database
3. `process_companies.py` reads company information and initiates scraping
4. `scrape_company_website.py` extracts officer and director information
5. `extract_officer_info.py` gets detailed information about each officer
6. All information is stored in the database using functions from `operations.py`

## Error Handling
- All scripts include comprehensive error handling
- Failed operations are logged with detailed error messages
- Database operations use transactions to ensure data consistency
- Website scraping includes retry mechanisms for failed requests

## Dependencies
- PostgreSQL database
- Python packages:
  - psycopg2: Database operations
  - beautifulsoup4: HTML parsing
  - requests: HTTP requests
  - python-dotenv: Environment variable management

## Usage
1. Set up environment variables in `.env` file
2. Run database setup: `python src/database/setup.py`
3. Import companies: `python src/scripts/import_companies.py`
4. Process companies: `python src/scripts/process_companies.py` 