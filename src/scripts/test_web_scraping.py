"""Script to test web scraping functionality using sample files."""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

from src.config.settings import settings
from src.services.minio_service import MinioService
from src.services.db_service import DatabaseService

def extract_officers(text: str) -> List[Dict[str, str]]:
    """Extract officer information from text using regex patterns.
    
    Args:
        text: Text to extract officers from
        
    Returns:
        List of dictionaries containing officer name and title
    """
    # Clean up text
    text = re.sub(r'\t', ' ', text)  # Replace tabs with spaces
    text = re.sub(r'\n+', ' ', text)  # Replace newlines with spaces
    text = re.sub(r'\s+', ' ', text)  # Normalize spaces
    text = text.strip()
    
    # Common officer titles
    titles = [
        r'CEO',
        r'CFO',
        r'COO',
        r'President',
        r'Vice President',
        r'VP',
        r'Director',
        r'Chairman',
        r'Chair',
        r'Chief',
        r'Executive',
        r'Manager',
        r'Head',
        r'Lead',
        r'Superintendent',
        r'Supervisor',
        r'Coordinator',
        r'Advisor',
        r'Consultant',
        r'Specialist'
    ]
    
    officers = []
    for title in titles:
        # Look for title followed by name
        pattern = f"{title}\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
        matches = re.finditer(pattern, text)
        
        for match in matches:
            name = match.group(1)
            # Get context around the match
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end]
            
            officers.append({
                'name': name,
                'title': title,
                'context': context
            })
    
    return officers

def process_file(file_path: Path) -> Optional[Dict[str, List[Dict[str, str]]]]:
    """Process a JSON file to extract officer information.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Dictionary mapping domain to list of officers, or None if processing fails
    """
    try:
        print(f"Reading file: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Extract domain from URL
        url = data.get('url', '')
        print(f"Processing URL: {url}")
        domain = urlparse(url).netloc
        
        # Extract officers from body text
        body_text = data.get('body_text', '')
        print(f"Body text length: {len(body_text)} characters")
        officers = extract_officers(body_text)
        
        return {domain: officers}
        
    except Exception as e:
        print(f"Error processing file {file_path}: {str(e)}")
        return None

def main():
    """Main function to test web scraping functionality."""
    print("Initializing services...")
    # Initialize services
    minio_service = MinioService()
    db_service = DatabaseService(settings.database.dict())
    
    # Create output directory
    output_dir = Path("data/test_samples")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_dir}")
    
    # Download sample files
    print("Downloading sample files from MinIO...")
    try:
        downloaded_files = minio_service.download_sample(2, output_dir)
        print(f"Downloaded {len(downloaded_files)} files")
    except Exception as e:
        print(f"Error downloading files: {str(e)}")
        return
    
    # Process files
    print("\nProcessing files...")
    for file_path in output_dir.glob("*.json"):
        print(f"\nProcessing {file_path.name}...")
        result = process_file(file_path)
        
        if result:
            for domain, officers in result.items():
                print(f"\nDomain: {domain}")
                if officers:
                    print(f"Found {len(officers)} officers:")
                    for officer in officers:
                        print(f"- {officer['name']} ({officer['title']})")
                        print(f"  Context: {officer['context']}")
                    
                    # Store officers in database
                    try:
                        company = db_service.get_company_by_website(domain)
                        if company:
                            db_service.update_company_officers(
                                company['id'],
                                officers,
                                'web_scraping'
                            )
                            print(f"Successfully stored officers for {domain}")
                        else:
                            print(f"Company not found in database for {domain}")
                    except Exception as e:
                        print(f"Error storing officers for {domain}: {str(e)}")
                else:
                    print("No officers found")

if __name__ == "__main__":
    main() 