"""Service for managing local file operations."""

from typing import List, Dict, Optional
from src.services.company_service import CompanyService

class LocalService:
    """Service for managing local file operations."""
    
    def __init__(self):
        """Initialize the local service."""
        self.company_service = CompanyService()
    
    def update_company_management(self, company_id: int, 
                                officers: List[Dict[str, str]], 
                                board_members: List[Dict[str, str]]) -> bool:
        """Update management information for a company using local data.
        
        Args:
            company_id: ID of the company to update
            officers: List of officer dictionaries
            board_members: List of board member dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        return self.company_service.update_company_management(
            company_id=company_id,
            officers=officers,
            board_members=board_members,
            source='local'
        )
    
    def update_company_officers(self, company_id: int, 
                              officers: List[Dict[str, str]]) -> bool:
        """Update officers for a company using local data.
        
        Args:
            company_id: ID of the company to update
            officers: List of officer dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        return self.company_service.update_company_officers(
            company_id=company_id,
            officers=officers,
            source='local'
        )
    
    def update_company_board(self, company_id: int, 
                           board_members: List[Dict[str, str]]) -> bool:
        """Update board members for a company using local data.
        
        Args:
            company_id: ID of the company to update
            board_members: List of board member dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        return self.company_service.update_company_board(
            company_id=company_id,
            board_members=board_members,
            source='local'
        ) 