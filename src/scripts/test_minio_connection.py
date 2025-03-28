"""Script to test MinIO connection and list available files."""

import os
from pathlib import Path
from dotenv import load_dotenv

from src.services.minio_service import MinioService

def test_minio_connection():
    """Test MinIO connection and list available files."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Print environment variables (without sensitive data)
        print("\nChecking environment variables:")
        print(f"MINIO_ENDPOINT: {os.getenv('MINIO_ENDPOINT', 'Not set')}")
        print(f"MINIO_BUCKET_NAME: {os.getenv('MINIO_BUCKET_NAME', 'Not set')}")
        print(f"MINIO_ACCESS_KEY: {'Set' if os.getenv('MINIO_ACCESS_KEY') else 'Not set'}")
        print(f"MINIO_SECRET_KEY: {'Set' if os.getenv('MINIO_SECRET_KEY') else 'Not set'}")
        
        # Initialize MinIO service
        print("\nInitializing MinIO service...")
        minio_service = MinioService()
        
        # Ensure bucket exists
        print("\nChecking bucket existence...")
        minio_service.ensure_bucket_exists()
        
        # Count objects
        print("\nCounting objects in bucket...")
        count = minio_service.count_objects()
        print(f"Total objects in bucket: {count}")
        
        # List first 5 objects
        print("\nListing first 5 objects:")
        objects = minio_service.list_objects()
        for obj in objects[:5]:
            print(f"- {obj}")
            
        print("\nMinIO connection test completed successfully!")
        
    except Exception as e:
        print(f"\nError testing MinIO connection: {str(e)}")
        raise

if __name__ == "__main__":
    test_minio_connection() 