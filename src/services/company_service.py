"""Service for managing company operations."""

from typing import List, Optional, Dict, Any
from src.models.company import Company
from src.services.db_service import DatabaseService
from src.services.llm_service import LLMService
import json
import logging

logger = logging.getLogger(__name__)

class CompanyService:
    """Service for managing company operations."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the company service.
        
        Args:
            config: Configuration dictionary containing service settings
        """
        self.db_service = DatabaseService(config)
        self.llm_service = LLMService(config)
    
    def get_all_companies(self) -> List[Company]:
        """Get all companies from the database."""
        try:
            with self.db_service.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, website, company_name, ticker, exchange,
                               headquarters_location, founded_date, description,
                               officers, board_members, data_source
                        FROM mining_companies
                        ORDER BY company_name
                    """)
                    rows = cur.fetchall()
                    return [Company(*row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting companies: {str(e)}")
            return []
    
    def get_company_by_name(self, name: str) -> Optional[Company]:
        """Get a company by name.
        
        Args:
            name: Company name to search for
            
        Returns:
            Company instance if found, None otherwise
        """
        company_data = self.db_service.get_company_by_name(name)
        return Company.from_dict(company_data) if company_data else None
    
    def get_company_by_website(self, website: str) -> Optional[Company]:
        """Get a company by website URL.
        
        Args:
            website: Company website URL
            
        Returns:
            Company instance if found, None otherwise
        """
        company_data = self.db_service.get_company_by_website(website)
        return Company.from_dict(company_data) if company_data else None
    
    def update_company_management(self, company_id: int, 
                                officers: List[Dict[str, str]], 
                                board_members: List[Dict[str, str]],
                                source: str = 'llm') -> bool:
        """Update management information for a company.
        
        Args:
            company_id: ID of the company to update
            officers: List of officer dictionaries
            board_members: List of board member dictionaries
            source: Source of the data ('local' or 'llm')
            
        Returns:
            True if successful, False otherwise
        """
        return self.db_service.update_company_management(
            company_id=company_id,
            officers=officers,
            board_members=board_members,
            source=source
        )
    
    def update_company_officers(self, company_id: int, 
                              officers: List[Dict[str, str]], 
                              source: str = 'llm') -> bool:
        """Update officers for a company.
        
        Args:
            company_id: ID of the company to update
            officers: List of officer dictionaries
            source: Source of the data ('local' or 'llm')
            
        Returns:
            True if successful, False otherwise
        """
        return self.db_service.update_company_officers(
            company_id=company_id,
            officers=officers,
            source=source
        )
    
    def update_company_board(self, company_id: int, 
                           board_members: List[Dict[str, str]], 
                           source: str = 'llm') -> bool:
        """Update board members for a company.
        
        Args:
            company_id: ID of the company to update
            board_members: List of board member dictionaries
            source: Source of the data ('local' or 'llm')
            
        Returns:
            True if successful, False otherwise
        """
        return self.db_service.update_company_board(
            company_id=company_id,
            board_members=board_members,
            source=source
        )
    
    def search_companies_by_officer(self, name: str) -> List[Company]:
        """Search for companies by officer name.
        
        Args:
            name: Name of the officer to search for
            
        Returns:
            List of Company instances where the officer was found
        """
        companies_data = self.db_service.search_companies_by_officer(name)
        return [Company.from_dict(data) for data in companies_data]
    
    def search_companies_by_role(self, role: str) -> List[Company]:
        """Search for companies by officer/board member role.
        
        Args:
            role: Role/title to search for
            
        Returns:
            List of Company instances where the role was found
        """
        companies_data = self.db_service.search_companies_by_role(role)
        return [Company.from_dict(data) for data in companies_data]
    
    def get_all_officers(self) -> List[Dict[str, Any]]:
        """Get all officers across all companies.
        
        Returns:
            List of dictionaries containing company and officer information
        """
        return self.db_service.get_all_officers()
    
    def get_all_board_members(self) -> List[Dict[str, Any]]:
        """Get all board members across all companies.
        
        Returns:
            List of dictionaries containing company and board member information
        """
        return self.db_service.get_all_board_members()
    
    def update_data_source(self, company_id: int, data_source: dict) -> bool:
        """Update the data source for a company's management information."""
        try:
            with self.db_service.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE mining_companies 
                        SET data_source = %s::jsonb 
                        WHERE id = %s
                    """, (json.dumps(data_source), company_id))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error updating data source for company {company_id}: {str(e)}")
            return False 