"""Service for managing local data operations."""

from typing import List, Dict, Any
from src.services.db_service import DatabaseService

class LocalService:
    """Service for managing local data operations."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the local service.
        
        Args:
            config: Configuration dictionary containing service settings
        """
        self.db_service = DatabaseService(config)
        
    def update_company_officers(self, company_id: int, officers: List[Dict[str, str]]) -> bool:
        """Update company officers from local data.
        
        Args:
            company_id: ID of the company to update
            officers: List of officer dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        return self.db_service.update_company_management(
            company_id=company_id,
            officers=officers,
            board_members=[],
            source='local'
        )
        
    def update_company_board(self, company_id: int, board_members: List[Dict[str, str]]) -> bool:
        """Update company board members from local data.
        
        Args:
            company_id: ID of the company to update
            board_members: List of board member dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        return self.db_service.update_company_management(
            company_id=company_id,
            officers=[],
            board_members=board_members,
            source='local'
        ) 