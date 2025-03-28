"""Main script for processing company data."""

import logging
import os
import shutil
from pathlib import Path
from typing import Dict, Any, List
from urllib.parse import urlparse, unquote
from collections import Counter
import json

from src.config.settings import settings
from src.services.minio_service import MinioService
from src.services.db_service import DatabaseService

def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
        return parsed.netloc.replace('www.', '')
    except:
        return ""

def count_files_per_domain(bucket_files: List[str]) -> Dict[str, int]:
    """Count number of files per domain in bucket."""
    counts = Counter()
    
    for file in bucket_files:
        try:
            # Decode URL-encoded filename
            decoded = unquote(file)
            # Parse URL from filename
            parsed = urlparse(decoded)
            # Extract domain without www
            domain = parsed.netloc.replace('www.', '')
            if domain:
                counts[domain] += 1
        except:
            continue
            
    return counts

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=settings.log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def initialize_services() -> Dict[str, Any]:
    """Initialize required services."""
    db_config = {
        'db_host': settings.database.db_host,
        'db_port': settings.database.db_port,
        'db_name': settings.database.db_name,
        'db_user': settings.database.db_user,
        'db_password': settings.database.db_password.get_secret_value()
    }
    return {
        'minio_service': MinioService(),
        'db_service': DatabaseService(db_config)
    }

def download_company_files(minio_service: MinioService, domain: str, working_dir: Path) -> List[str]:
    """Download files for a company's domain to working directory."""
    downloaded_files = []
    
    # Get all files for the domain
    files = [f for f in minio_service.list_objects() if domain in f]
    logging.info(f"Found {len(files)} files for domain {domain}")
    
    # Create working directory if it doesn't exist
    working_dir.mkdir(parents=True, exist_ok=True)
    
    # Download each file
    for file in files:
        try:
            # Decode the URL-encoded filename
            decoded = unquote(file)
            # Extract just the filename from the full URL path
            filename = decoded.split('/')[-1]
            
            # Replace invalid characters in filename
            safe_filename = filename.replace('?', '_').replace('=', '_').replace('&', '_')
            target_path = working_dir / safe_filename
            
            logging.info(f"Processing file: {decoded}")
            logging.info(f"Downloading to: {target_path}")
            
            # Download file using fget_object
            minio_service.client.fget_object(
                bucket_name=minio_service.bucket_name,
                object_name=file,
                file_path=str(target_path)
            )
            
            if target_path.exists():
                logging.info(f"Successfully downloaded: {safe_filename}")
                downloaded_files.append(safe_filename)
            else:
                logging.error(f"File was not created: {target_path}")
                
        except Exception as e:
            logging.error(f"Error downloading {file}: {e}")
            
    return downloaded_files

def process_company_files(company_id: int, working_dir: Path, db_service: DatabaseService) -> None:
    """Process downloaded files for a company."""
    # TODO: Implement file processing logic here
    # This will be the integration point with the existing analysis code
    
    # For now, just log the files we found
    files = list(working_dir.glob("*.json"))
    logging.info(f"Found {len(files)} JSON files to process")
    
    for file in files:
        try:
            # TODO: Implement officer extraction logic here
            # For now, just log the file
            logging.info(f"Processing file: {file.name}")
            
        except Exception as e:
            logging.error(f"Error processing file {file.name}: {e}")
            continue

def cleanup_working_dir(working_dir: Path) -> None:
    """Clean up working directory after processing."""
    try:
        shutil.rmtree(working_dir)
    except Exception as e:
        logging.error(f"Error cleaning up working directory: {e}")

def process_company(company: Dict[str, Any], minio_service: MinioService, domain_counts: Dict[str, int]) -> None:
    """Process a single company's files."""
    company_name = company.get('company_name', 'Unknown')
    company_id = company.get('id')
    website = company.get('website')
    
    if not website:
        logging.info(f"Skipping company {company_name} - no website")
        return
        
    domain = extract_domain(website)
    if not domain:
        logging.info(f"Skipping company {company_name} - invalid website format")
        return
    
    logging.info(f"Company: {company_name}")
    logging.info(f"Domain: {domain}")
    logging.info(f"Files in bucket: {domain_counts.get(domain, 0)}")
    
    if domain_counts.get(domain, 0) == 0:
        logging.info("--------------------------------------------------")
        return
        
    # Create working directory
    working_dir = Path("working") / f"company_{company_id}"
    working_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Download files
        logging.info("Downloading files...")
        downloaded_files = download_company_files(minio_service, domain, working_dir)
        logging.info(f"Downloaded {len(downloaded_files)} files")
        
        # Process files
        logging.info("Processing files...")
        json_files = list(working_dir.glob("*.json"))
        logging.info(f"Found {len(json_files)} JSON files to process")
        
        for file in json_files:
            logging.info(f"Processing file: {file.name}")
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # TODO: Process the data to extract management information
                    pass
            except Exception as e:
                logging.error(f"Error processing file {file}: {e}")
                
    finally:
        # Clean up working directory
        logging.info("Cleaning up...")
        try:
            # Close any open file handles
            import gc
            gc.collect()
            
            # Remove all files in the directory
            for file in working_dir.glob("*"):
                try:
                    file.unlink()
                except Exception as e:
                    logging.error(f"Error deleting file {file}: {e}")
                    
            # Remove the directory itself
            working_dir.rmdir()
        except Exception as e:
            logging.error(f"Error cleaning up working directory: {e}")
            
    logging.info("--------------------------------------------------")

def main():
    """Main execution function."""
    # Set up logging
    setup_logging()
    
    # Initialize services
    services = initialize_services()
    
    # Get all files from bucket first
    logging.info("Getting files from MinIO bucket...")
    all_files = services['minio_service'].list_objects()
    logging.info(f"Found {len(all_files)} files in bucket")
    
    # Log some sample files to understand the structure
    logging.info("Sample files in bucket:")
    for file in all_files[:10]:
        logging.info(f"  {file}")
    
    # Count files per domain
    domain_counts = count_files_per_domain(all_files)
    logging.info(f"Found files for {len(domain_counts)} unique domains")
    
    # Get all companies from database
    companies = services['db_service'].get_all_companies()
    logging.info(f"Found {len(companies)} companies in database")
    
    # Limit to first 5 companies for testing
    companies = companies[:5]
    logging.info(f"Processing first {len(companies)} companies")
    
    # Process each company
    for company in companies:
        process_company(company, services['minio_service'], domain_counts)
        
    logging.info("Processing complete")

if __name__ == "__main__":
    main()
