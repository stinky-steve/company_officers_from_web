"""Script to analyze company URLs and their presence in MinIO bucket."""

import os
import json
from urllib.parse import unquote, urlparse
import pandas as pd
from collections import Counter
from pathlib import Path
from typing import List, Dict

from src.services.minio_service import MinioService
from src.services.db_service import DatabaseService
from src.config.settings import settings

def extract_domain(url):
    """Extract domain from URL."""
    try:
        if pd.isna(url):
            return None
        parsed = urlparse(url)
        return parsed.netloc.replace('www.', '')
    except:
        return None

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

def get_bucket_files(minio_service: MinioService) -> List[str]:
    """Get list of all files in MinIO bucket."""
    try:
        files = minio_service.list_objects()
        print(f"Found {len(files)} files in bucket")
        return files
    except Exception as e:
        print(f"Error getting bucket files: {str(e)}")
        return []

def analyze_companies(db: DatabaseService, bucket_files: List[str]):
    """Analyze companies from database and their presence in bucket."""
    # Get all companies
    companies = db.get_all_companies()
    print(f"\nRead {len(companies)} companies from database")
    
    # Create DataFrame from companies
    df = pd.DataFrame(companies)
    
    # Extract domains from company websites
    df['domain'] = df['website'].apply(extract_domain)
    
    # Count files per domain in bucket
    domain_counts = count_files_per_domain(bucket_files)
    
    # Add file counts to DataFrame
    df['files_in_bucket'] = df['domain'].apply(lambda x: domain_counts.get(x, 0) if x else 0)
    
    # Create output directory if it doesn't exist
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save enhanced CSV
    output_file = output_dir / "companies_with_file_counts.csv"
    df.to_csv(output_file, index=False)
    print(f"\nSaved enhanced CSV to {output_file}")
    
    # Print summary statistics
    print("\nSummary Statistics:")
    print("-" * 50)
    print(f"Total companies in database: {len(df)}")
    print(f"Companies with websites: {df['website'].notna().sum()}")
    print(f"Companies with files in bucket: {(df['files_in_bucket'] > 0).sum()}")
    print(f"\nTop 20 companies by number of files:")
    print(df.sort_values('files_in_bucket', ascending=False)[['company_name', 'website', 'files_in_bucket']].head(20))

def main():
    # Initialize services
    minio_service = MinioService()
    db = DatabaseService()
    
    # Get all files from bucket
    print("Getting files from MinIO bucket...")
    bucket_files = get_bucket_files(minio_service)
    
    # Analyze companies
    print("\nAnalyzing companies...")
    analyze_companies(db, bucket_files)

if __name__ == "__main__":
    main() 