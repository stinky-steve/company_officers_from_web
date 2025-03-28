"""Script to download and analyze sample files from MinIO bucket."""

import json
from pathlib import Path
from typing import Dict, Any
from collections import defaultdict
from urllib.parse import unquote

from src.services.minio_service import MinioService

def analyze_json_structure(data: Any, path: str = "", structure: Dict = None) -> Dict:
    """Analyze the structure of a JSON object recursively."""
    if structure is None:
        structure = defaultdict(list)
        
    if isinstance(data, dict):
        for key, value in data.items():
            new_path = f"{path}.{key}" if path else key
            structure[new_path].append(type(value).__name__)
            analyze_json_structure(value, new_path, structure)
    elif isinstance(data, list):
        if data:
            structure[path].append(f"list[{type(data[0]).__name__}]")
            analyze_json_structure(data[0], path, structure)
        else:
            structure[path].append("list[empty]")
            
    return structure

def main():
    """Download and analyze sample files from MinIO bucket."""
    try:
        # Initialize MinIO service
        print("\nInitializing MinIO service...")
        minio_service = MinioService()
        
        # Create output directory
        output_dir = Path("data/test_samples")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Download sample files
        sample_size = 5
        print(f"\nDownloading {sample_size} sample files...")
        downloaded_files = minio_service.download_sample(sample_size, output_dir)
        
        if not downloaded_files:
            print("No files were downloaded. Please check MinIO connection and bucket contents.")
            return
            
        print(f"\nDownloaded {len(downloaded_files)} files:")
        for file_path in downloaded_files:
            print(f"- {file_path}")
            
        # Analyze structure of each file
        all_structures = defaultdict(list)
        
        print("\nAnalyzing file structures...")
        for file_path in downloaded_files:
            print(f"\nAnalyzing {file_path}...")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    structure = analyze_json_structure(data)
                    
                    # Merge structures
                    for path, types in structure.items():
                        all_structures[path].extend(types)
                        
                # Print sample content
                print("\nSample content:")
                print(json.dumps(data, indent=2)[:500] + "...")  # Print first 500 chars
                    
            except Exception as e:
                print(f"Error analyzing {file_path}: {str(e)}")
                
        # Print structure summary
        print("\nStructure Summary:")
        print("-" * 50)
        for path, types in sorted(all_structures.items()):
            # Count occurrences of each type
            type_counts = defaultdict(int)
            for t in types:
                type_counts[t] += 1
                
            # Format type information
            type_info = ", ".join(f"{t} ({count})" for t, count in type_counts.items())
            print(f"- {path}: {type_info}")
            
    except Exception as e:
        print(f"\nError: {str(e)}")
        raise

if __name__ == "__main__":
    main() 