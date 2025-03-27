from typing import List, Optional
import os
from minio import Minio
from pathlib import Path
from urllib.parse import urlparse

from src.config.settings import settings

class MinioService:
    def __init__(self):
        # Parse endpoint URL
        endpoint = str(settings.minio.endpoint)
        if not endpoint.startswith(('http://', 'https://')):
            endpoint = f'http://{endpoint}'
        parsed_url = urlparse(endpoint)
        
        self.client = Minio(
            endpoint=parsed_url.netloc,
            access_key=settings.minio.access_key,
            secret_key=settings.minio.secret_key.get_secret_value(),
            secure=parsed_url.scheme == "https"
        )
        self.bucket_name = settings.minio.bucket_name

    def ensure_bucket_exists(self) -> None:
        """Ensure the configured bucket exists, create if it doesn't."""
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)

    def count_objects(self) -> int:
        """Count total number of objects in the bucket."""
        objects = self.client.list_objects(self.bucket_name)
        return sum(1 for _ in objects)

    def list_objects(self, prefix: str = "") -> List[str]:
        """List all objects in the bucket with optional prefix."""
        objects = self.client.list_objects(self.bucket_name, prefix=prefix)
        return [obj.object_name for obj in objects]

    def download_sample(self, sample_size: int, output_dir: Path, prefix: str = "") -> List[str]:
        """Download a sample of objects from the bucket.
        
        Args:
            sample_size: Number of objects to download
            output_dir: Local directory to save files
            prefix: Optional prefix to filter objects
            
        Returns:
            List of downloaded file paths
        """
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get list of objects
        objects = list(self.client.list_objects(self.bucket_name, prefix=prefix))
        
        # Take sample (or all if sample_size > total objects)
        sample = objects[:min(sample_size, len(objects))]
        
        downloaded_files = []
        for obj in sample:
            output_path = output_dir / obj.object_name
            # Create parent directories if needed
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download the object
            self.client.fget_object(
                self.bucket_name,
                obj.object_name,
                str(output_path)
            )
            downloaded_files.append(str(output_path))
            
        return downloaded_files 