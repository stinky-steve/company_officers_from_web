"""Main script for processing company data."""

import logging
import os
import shutil
from pathlib import Path
from typing import Dict, Any, List, Tuple
from urllib.parse import urlparse, unquote
from collections import Counter
import json
from tqdm import tqdm

from src.config.settings import settings
from src.services.minio_service import MinioService
from src.services.db_service import DatabaseService
from src.services.llm_service import LLMService
from src.data_reader import DataReader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/main.log", mode="w", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        # Remove any protocol prefix
        if '://' in url:
            url = url.split('://')[1]
        # Remove any path
        if '/' in url:
            url = url.split('/')[0]
        # Remove any port number
        if ':' in url:
            url = url.split(':')[0]
        return url.lower()
    except Exception as e:
        logger.error(f"Error extracting domain from {url}: {e}")
        return ''

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
    logger.info(f"Found {len(files)} files for domain {domain}")
    
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
            
            logger.info(f"Processing file: {decoded}")
            logger.info(f"Downloading to: {target_path}")
            
            # Download file using fget_object
            minio_service.client.fget_object(
                bucket_name=minio_service.bucket_name,
                object_name=file,
                file_path=str(target_path)
            )
            
            if target_path.exists():
                logger.info(f"Successfully downloaded: {safe_filename}")
                downloaded_files.append(safe_filename)
            else:
                logger.error(f"File was not created: {target_path}")
                
        except Exception as e:
            logger.error(f"Error downloading {file}: {e}")
            
    return downloaded_files

def process_company_files(
    data_reader: DataReader,
    minio_service: MinioService,
    company_domain: str,
    company_name: str
) -> Tuple[int, int, List]:
    """Process all files for a specific company.

    Returns:
        processed_files: Number of files that yielded people.
        total_people: Total number of people extracted.
        company_people: List of all Person objects extracted.
    """
    logger.info(f"Processing files for {company_name} ({company_domain})")
    files = get_company_files(minio_service, company_domain)
    logger.info(f"Found {len(files)} files to process")

    processed_files = 0
    total_people = 0
    company_people = []

    # Create working directory
    working_dir = Path("working") / f"company_{company_name.lower().replace(' ', '_')}"
    working_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Download files
        logger.info("Downloading files...")
        for file in files:
            try:
                # Decode URL-encoded file path
                decoded = file.replace('%3A', ':').replace('%2F', '/')
                if '://' in decoded:
                    url = decoded.split('://')[1]
                else:
                    url = decoded

                # Create safe filename
                safe_filename = url.replace('/', '_').replace('\\', '_')
                target_path = working_dir / safe_filename

                logger.info(f"Processing file: {decoded}")
                logger.info(f"Downloading to: {target_path}")

                # Download file using MinioService
                minio_service.client.fget_object(
                    minio_service.bucket_name,
                    file,
                    str(target_path)
                )

                if target_path.exists():
                    logger.info(f"Successfully downloaded: {safe_filename}")
                else:
                    logger.error(f"File was not created: {target_path}")

            except Exception as e:
                logger.error(f"Error downloading {file}: {e}")
                continue

        # Process files
        logger.info("Processing files...")
        for json_file in working_dir.glob("*.json"):
            try:
                content = data_reader.read_json_file(str(json_file))
                if not content:
                    continue

                processed_content = data_reader.process_content(content)
                if not processed_content:
                    continue

                exec_count = len(processed_content.executives)
                board_count = len(processed_content.board_members)
                people_count = exec_count + board_count

                if people_count > 0:
                    total_people += people_count
                    processed_files += 1
                    company_people.extend(processed_content.executives)
                    company_people.extend(processed_content.board_members)

                    logger.info(f"\nFile: {json_file.name}")
                    logger.info(f"URL: {processed_content.url}")
                    logger.info(f"Title: {processed_content.title}")
                    logger.info(f"Executives found: {exec_count}")
                    logger.info(f"Board members found: {board_count}")

            except Exception as e:
                logger.error(f"Error processing {json_file}: {str(e)}")
                continue

    finally:
        # Clean up working directory
        logger.info("Cleaning up...")
        try:
            for file in working_dir.glob("*"):
                try:
                    file.unlink()
                except Exception as e:
                    logger.error(f"Error removing {file}: {e}")
            working_dir.rmdir()
        except Exception as e:
            logger.error(f"Error cleaning up {working_dir}: {e}")

    logger.info(f"Processed {processed_files} files")
    logger.info(f"Found {total_people} people")
    return processed_files, total_people, company_people

def extract_officers(text: str) -> List[Dict[str, str]]:
    """Extract officer information from text content."""
    officers = []
    try:
        # Use LLM service to extract management information
        llm_service = LLMService()
        management_info = llm_service.extract_management_info("", text)
        
        # Process the extracted information
        for category, people in management_info.items():
            for person in people:
                officer = {
                    'name': person.get('name', ''),
                    'title': person.get('title', ''),
                    'bio': person.get('bio', '')
                }
                officers.append(officer)
                
    except Exception as e:
        logging.error(f"Error extracting officers: {e}")
        
    return officers

def cleanup_working_dir(working_dir: Path) -> None:
    """Clean up the working directory and its contents."""
    try:
        # Close any open file handles
        import gc
        gc.collect()
        
        # Remove all files first
        for file_path in working_dir.glob('*'):
            try:
                if file_path.is_file():
                    file_path.unlink()
                elif file_path.is_dir():
                    shutil.rmtree(file_path)
            except Exception as e:
                logging.warning(f"Error removing {file_path}: {e}")
                # Try to force close any open handles
                try:
                    import psutil
                    for proc in psutil.process_iter(['pid', 'open_files']):
                        try:
                            for file in proc.open_files():
                                if str(file_path) in file.path:
                                    proc.kill()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                except ImportError:
                    pass
        
        # Then remove the directory itself
        try:
            working_dir.rmdir()
            logging.info(f"Successfully cleaned up {working_dir}")
        except Exception as e:
            logging.warning(f"Could not remove directory {working_dir}: {e}")
            
    except Exception as e:
        logging.error(f"Error cleaning up working directory: {e}")
        # Don't raise the exception - we want to continue processing other companies

def process_company(company: Dict[str, Any], minio_service: MinioService, domain_counts: Dict[str, int], services: Dict[str, Any]) -> None:
    """Process a single company."""
    company_name = company.get('company_name', 'Unknown')
    company_id = company.get('id')
    logger.info(f"Company: {company_name}")
    
    if not company_id:
        logger.error(f"No company ID found for {company_name}")
        return
        
    # Get domain from website
    website = company.get('website', '')
    if not website:
        logger.info(f"No website found for {company_name}")
        return
        
    domain = extract_domain(website)
    logger.info(f"Domain: {domain}")
    
    # Count files for this domain
    domain_count = domain_counts.get(domain, 0)
    logger.info(f"Files in bucket: {domain_count}")
    
    if domain_count == 0:
        return
        
    # Create working directory
    working_dir = Path('working') / f'company_{company_id}'
    working_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Download files
        logger.info("Downloading files...")
        downloaded_files = download_company_files(minio_service, domain, working_dir)
        logger.info(f"Downloaded {len(downloaded_files)} files")
        
        # Process files
        logger.info("Processing files...")
        processed_files, total_people, company_people = process_company_files(
            data_reader=DataReader(minio_service.client, settings.minio.bucket_name),
            minio_service=services['minio_service'],
            company_domain=domain,
            company_name=company_name
        )
        
        logger.info(f"Processed {len(processed_files)} files")
        logger.info(f"Found {total_people} people")
        
    finally:
        # Clean up working directory
        logger.info("Cleaning up...")
        cleanup_working_dir(working_dir)
        
    logger.info("--------------------------------------------------")

def is_excluded_url(url: str) -> bool:
    """Return True if the URL contains any excluded keyword."""
    excluded_keywords = ["press-release", "news", "blog", "announcement", "news-room", "press-releases", "projects"]
    return any(kw in url.lower() for kw in excluded_keywords)

def get_company_files(minio_service: MinioService, company_domain: str) -> List[str]:
    """Get all files for a specific company domain, excluding URLs with unwanted keywords."""
    all_files = minio_service.list_objects()
    return [f for f in all_files if company_domain in f and not is_excluded_url(f)]

def main():
    """Main function to process company files and extract management information."""
    # Initialize services
    services = initialize_services()
    
    # Get settings
    settings = Settings()
    
    # Get files from MinIO bucket
    logger.info("Getting files from MinIO bucket...")
    files = services['minio_service'].list_objects(settings.minio.bucket_name)
    file_list = [f.object_name for f in files]
    logger.info(f"Found {len(file_list)} files in bucket")
    
    # Log sample files
    logger.info("Sample files in bucket:")
    for f in file_list[:10]:
        logger.info(f"  {f}")
    
    # Get unique domains from files
    domains = {unquote(f.split('/')[0]) for f in file_list}
    logger.info(f"Found files for {len(domains)} unique domains")
    
    # Get companies from database
    companies = services['db_service'].get_all_companies()
    logger.info(f"Found {len(companies)} companies in database")
    
    # Log sample company keys
    if companies:
        logger.info("Sample company keys:")
        for key in companies[0].keys():
            logger.info(f"  {key}")
    
    # Process first 5 companies
    logger.info("Processing first 5 companies")
    for company in companies[:5]:
        logger.info("-" * 50)
        logger.info(f"Company: {company['company_name']}")
        
        # Extract domain from website
        domain = extract_domain(company['website'])
        logger.info(f"Domain: {domain}")
        
        # Get files for this company's domain
        company_files = [f for f in file_list if domain in f]
        logger.info(f"Files in bucket: {len(company_files)}")
        
        if not company_files:
            continue
            
        # Process files
        processed_files, total_people, company_people = process_company_files(
            company_name=company['company_name'],
            domain=domain,
            minio_service=services['minio_service'],
            settings=settings
        )
        
        logger.info(f"Processed {processed_files} files")
        logger.info(f"Found {total_people} people")
        logger.info(f"Found {company_people} people for this company")
        logger.info("-" * 50)
    
    logger.info("Processing complete")

if __name__ == "__main__":
    main()
