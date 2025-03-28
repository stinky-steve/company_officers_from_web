"""Service for handling local file operations."""

import os
import json
from typing import Optional, List, Dict, Any
from pathlib import Path

class FileService:
    """Service for managing local file operations."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the file service.
        
        Args:
            config: Configuration dictionary containing file paths and settings
        """
        self.minio_endpoint = config['minio_endpoint']
        self.minio_access_key = config['minio_access_key']
        self.minio_secret_key = config['minio_secret_key']
        self.minio_bucket_name = config['minio_bucket_name']
        
        # Validate required configuration
        if not all([self.minio_endpoint, self.minio_access_key, 
                   self.minio_secret_key, self.minio_bucket_name]):
            raise ValueError("Missing required MinIO configuration parameters")
        
        self.data_dir = Path(config['data_dir'])
        self.raw_dir = self.data_dir / 'raw'
        self.company_files_dir = self.raw_dir / 'company_files'
        
        # Create directories if they don't exist
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.company_files_dir.mkdir(parents=True, exist_ok=True)
    
    def _normalize_filename(self, name: str) -> str:
        """Normalize a name for use in filenames.
        
        Args:
            name: Name to normalize
            
        Returns:
            Normalized name
        """
        return name.lower().replace(' ', '_').replace('/', '_')
    
    def get_company_file_path(self, company_name: str) -> Path:
        """Get the path to a company's data file.
        
        Args:
            company_name: Name of the company
            
        Returns:
            Path to company data file
        """
        filename = f"{self._normalize_filename(company_name)}.json"
        return self.company_files_dir / filename
    
    def read_company_data(self, company_name: str) -> Optional[Dict]:
        """Read data for a company from local file.
        
        Args:
            company_name: Name of the company
            
        Returns:
            Company data if found, None otherwise
        """
        file_path = self.get_company_file_path(company_name)
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading {file_path}: {str(e)}")
            return None
    
    def get_local_officers(self, company_name: str) -> Optional[List[Dict[str, str]]]:
        """Get officers from local file.
        
        Args:
            company_name: Name of the company
            
        Returns:
            List of officer dictionaries if found, None otherwise
        """
        data = self.read_company_data(company_name)
        if not data:
            return None
        
        officers = data.get('officers')
        if not officers or not isinstance(officers, list):
            return None
        
        # Validate officer data
        valid_officers = []
        for officer in officers:
            if isinstance(officer, dict) and 'name' in officer and 'title' in officer:
                valid_officers.append({
                    'name': str(officer['name']),
                    'title': str(officer['title'])
                })
        
        return valid_officers if valid_officers else None
    
    def get_local_board(self, company_name: str) -> Optional[List[Dict[str, str]]]:
        """Get board members from local file.
        
        Args:
            company_name: Name of the company
            
        Returns:
            List of board member dictionaries if found, None otherwise
        """
        data = self.read_company_data(company_name)
        if not data:
            return None
        
        board = data.get('board_members')
        if not board or not isinstance(board, list):
            return None
        
        # Validate board member data
        valid_members = []
        for member in board:
            if isinstance(member, dict) and 'name' in member and 'title' in member:
                valid_members.append({
                    'name': str(member['name']),
                    'title': str(member['title'])
                })
        
        return valid_members if valid_members else None
    
    def save_company_data(self, company_name: str, data: Dict) -> bool:
        """Save data for a company to local file.
        
        Args:
            company_name: Name of the company
            data: Data to save
            
        Returns:
            True if successful, False otherwise
        """
        file_path = self.get_company_file_path(company_name)
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving {file_path}: {str(e)}")
            return False 