"""Script to upload sample files to MinIO bucket."""

import os
from pathlib import Path
from src.services.minio_service import MinioService

def create_sample_files():
    """Create some sample files to upload."""
    # Create sample directory
    sample_dir = Path("data/samples")
    sample_dir.mkdir(parents=True, exist_ok=True)
    
    # Create some sample files
    samples = [
        ("example1.com_about.html", "https://example1.com/about"),
        ("example2.com_team.html", "https://example2.com/team"),
        ("example3.com_contact.html", "https://example3.com/contact"),
    ]
    
    for filename, url in samples:
        file_path = sample_dir / filename
        with open(file_path, "w") as f:
            f.write(f"Sample content for {url}")
    
    return sample_dir

def main():
    """Upload sample files to MinIO bucket."""
    minio_service = MinioService()
    
    # Create sample files
    print("Creating sample files...")
    sample_dir = create_sample_files()
    
    # Upload files
    print("\nUploading files to MinIO...")
    for file_path in sample_dir.glob("*.html"):
        try:
            # Upload file with metadata
            minio_service.client.fput_object(
                "company-files",
                file_path.name,
                str(file_path),
                content_type="text/html",
                metadata={"url": file_path.stem.split("_")[0]}
            )
            print(f"Uploaded {file_path.name}")
        except Exception as e:
            print(f"Error uploading {file_path.name}: {e}")
    
    print("\nDone!")

if __name__ == "__main__":
    main() 