"""Script to test the DataReader functionality with MinIO data."""

import logging
import os
import pandas as pd
from typing import List, Dict
from tqdm import tqdm

from src.services.minio_service import MinioService
from src.data_reader import DataReader
from src.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MINIO_BUCKET = "min-co-web-page-data"

def save_sample_content(content: str, index: int):
    """Save sample content for manual inspection."""
    output_dir = "data/test_samples"
    os.makedirs(output_dir, exist_ok=True)
    
    # Save summary file
    summary_file = os.path.join(output_dir, f"sample_{index}_summary.txt")
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write(content)

def get_company_files(minio_service: MinioService, company_domain: str) -> List[str]:
    """Get all files for a specific company domain."""
    all_files = minio_service.list_objects()
    return [f for f in all_files if company_domain in f]

def process_company_files(data_reader: DataReader, company_domain: str, company_name: str):
    """Process all files for a specific company."""
    logger.info(f"\nProcessing files for {company_name} ({company_domain})")
    
    # Get all files for the company
    files = get_company_files(data_reader.minio_service, company_domain)
    logger.info(f"Found {len(files)} files to process")
    
    # Process files
    processed_files = 0
    total_people = 0
    company_people = []
    
    for i, file in enumerate(tqdm(files, desc="Processing files"), 1):
        try:
            content = data_reader.read_json_file(file)
            if not content:
                continue
                
            # Process content to extract management information
            processed_content = data_reader.process_content(content)
            if not processed_content:
                continue
                
            # Save sample content
            save_sample_content(str(processed_content), i)
            
            # Extract people
            if processed_content.people:
                total_people += len(processed_content.people)
                processed_files += 1
                company_people.extend(processed_content.people)
                
                # Log findings
                logger.info(f"\nFile {i}:")
                logger.info(f"URL: {processed_content.url}")
                logger.info(f"Title: {processed_content.title}")
                logger.info(f"People found: {len(processed_content.people)}")
                
                for person in processed_content.people:
                    logger.info(f"- {person.name} ({person.role})")
                    if person.contact_info:
                        logger.info(f"  Contact: {person.contact_info}")
                
        except Exception as e:
            logger.error(f"Error processing file {file}: {str(e)}")
            continue
    
    return processed_files, total_people, company_people

def main():
    """Test the data reader with a sample company."""
    try:
        logger.info("Creating DataReader instance...")
        minio_service = MinioService()
        data_reader = DataReader(minio_service, MINIO_BUCKET)
        
        # Process files for a specific company
        company_domain = "ayagoldsilver.com"
        company_name = "Aya Gold & Silver Inc."
        
        # Process all files for the selected company
        processed_files, total_people, company_people = process_company_files(
            data_reader, company_domain, company_name
        )
        
        # Print summary
        print("\nProcessing Summary")
        print("=" * 50)
        print(f"Company: {company_name}")
        print(f"Domain: {company_domain}")
        print(f"Files processed: {processed_files}")
        print(f"Total people found: {total_people}")
        
        if company_people:
            print("\nUnique People Found")
            print("-" * 50)
            unique_people = {p.name: p for p in company_people}.values()
            for person in unique_people:
                print(f"\nName: {person.name}")
                print(f"Role: {person.role}")
                if person.contact_info:
                    print("Contact Info:")
                    for key, value in person.contact_info.items():
                        print(f"  {key}: {value}")
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    main() 