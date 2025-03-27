"""Script to list objects in MinIO bucket."""

from src.services.minio_service import MinioService

def main():
    """List objects in MinIO bucket."""
    minio_service = MinioService()
    
    # List objects
    objects = minio_service.list_objects("company-files")
    
    print(f"Found {len(objects)} objects in bucket:")
    for obj in objects[:10]:  # Print first 10 objects
        print(f"- {obj}")
    
    if len(objects) > 10:
        print(f"... and {len(objects) - 10} more")

if __name__ == "__main__":
    main() 