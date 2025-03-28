Local Extraction Code:
Located in src/services/web_service.py
Uses BeautifulSoup for HTML parsing
Has rate limiting functionality
Key functions:
get_page_content(url): Fetches webpage content
get_management_pages(base_url): Finds management-related pages
Uses rate limiting to avoid overwhelming websites
Integration of Local and LLM Extraction:
The pipeline follows a two-step approach:
First attempts local extraction using web_service.py
Falls back to LLM extraction if needed
This is evident from the test files:
tests/unit/llm_extractor/test_extractor.py
tests/unit/services/test_minio_service.py
tests/unit/pipeline/test_pipeline.py
Database Schema and Storage:
Two main tables:
mining_companies:
Stores basic company info
Has JSONB columns for officers and board_members
Includes data_source field for tracking extraction method
company_officers:
Stores detailed officer information
Links to mining_companies via company_id
Includes fields for name, title, bio, photo_url
The pipeline flow should be:
Read JSON files from MinIO bucket
For each file:
Try local extraction using web_service.py
If successful, store results in database
If insufficient or fails, use LLM extraction
Combine results and store in database
Update both mining_companies and company_officers tables
Would you like me to:
Look deeper into any specific part of this flow?
Examine the test files to understand the expected behavior?
Review the database operations code to see how the data is stored?