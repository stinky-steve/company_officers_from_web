"""Script to analyze the structure of data files from MinIO bucket."""

import json
from pathlib import Path
from typing import Dict, List, Any
import random
from collections import defaultdict

from src.services.minio_service import MinioService

def analyze_json_structure(data: Any, path: str = "", structure: Dict = None) -> Dict:
    """Analyze the structure of a JSON object recursively.
    
    Args:
        data: The JSON data to analyze
        path: Current path in the JSON structure
        structure: Dictionary to store the structure information
        
    Returns:
        Dictionary containing structure information
    """
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
    """Main function to download and analyze data structure."""
    # Initialize MinIO service
    minio_service = MinioService()
    
    # Download sample files
    output_dir = Path("data/test_samples")
    sample_size = 5  # Number of files to download
    
    print(f"Downloading {sample_size} sample files...")
    downloaded_files = minio_service.download_sample(sample_size, output_dir)
    
    if not downloaded_files:
        print("No files were downloaded. Please check MinIO connection and bucket contents.")
        return
        
    print(f"\nDownloaded {len(downloaded_files)} files:")
    for file_path in downloaded_files:
        print(f"- {file_path}")
        
    # Analyze structure of each file
    all_structures = defaultdict(list)
    
    for file_path in downloaded_files:
        print(f"\nAnalyzing structure of {file_path}...")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                structure = analyze_json_structure(data)
                
                # Merge structures
                for path, types in structure.items():
                    all_structures[path].extend(types)
                    
        except Exception as e:
            print(f"Error analyzing {file_path}: {str(e)}")
            
    # Save structure information
    output_file = Path("docs/DATA_STRUCTURE.md")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Data Structure Analysis\n\n")
        f.write("This document describes the structure of JSON files stored in the MinIO bucket.\n\n")
        
        f.write("## Field Types\n\n")
        for path, types in sorted(all_structures.items()):
            # Count occurrences of each type
            type_counts = defaultdict(int)
            for t in types:
                type_counts[t] += 1
                
            # Format type information
            type_info = ", ".join(f"{t} ({count})" for t, count in type_counts.items())
            f.write(f"- `{path}`: {type_info}\n")
            
    print(f"\nStructure analysis saved to {output_file}")

if __name__ == "__main__":
    main() 