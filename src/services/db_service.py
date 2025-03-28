"""Service for managing database operations."""

import os
from typing import List, Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

from src.models.company import Company

class DatabaseService:
    """Service for managing database operations."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the database service.
        
        Args:
            config: Configuration dictionary containing database connection parameters
        """
        # Get database connection parameters from config
        self.host = config['db_host']
        self.port = config['db_port']
        self.dbname = config['db_name']
        self.user = config['db_user']
        self.password = config['db_password']
        
        # Validate required configuration
        if not all([self.host, self.port, self.dbname, self.user, self.password]):
            raise ValueError("Missing required database configuration parameters")
        
    def get_connection(self):
        """Get a database connection."""
        return psycopg2.connect(
            host=self.host,
            port=self.port,
            dbname=self.dbname,
            user=self.user,
            password=self.password
        )
        
    def get_all_companies(self) -> List[Dict[str, Any]]:
        """Get all companies from the database.
        
        Returns:
            List of company dictionaries
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, website, company_name, ticker, exchange,
                           headquarters_location, founded_date, description,
                           officers, board_members, data_source
                    FROM mining_companies
                    ORDER BY company_name;
                """)
                return cur.fetchall()
    
    def get_company_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a company by name.
        
        Args:
            name: Company name to search for
            
        Returns:
            Company dictionary if found, None otherwise
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, website, company_name, ticker, exchange,
                           headquarters_location, founded_date, description,
                           officers, board_members, data_source
                    FROM mining_companies
                    WHERE company_name = %s;
                """, (name,))
                return cur.fetchone()
    
    def get_company_by_website(self, website: str) -> Optional[Dict[str, Any]]:
        """Get a company by website URL.
        
        Args:
            website: Company website URL
            
        Returns:
            Company dictionary if found, None otherwise
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, website, company_name, ticker, exchange,
                           headquarters_location, founded_date, description,
                           officers, board_members, data_source
                    FROM mining_companies
                    WHERE website = %s;
                """, (website,))
                return cur.fetchone()
    
    def update_company_management(self, company_id: int, 
                                officers: List[Dict[str, str]], 
                                board_members: List[Dict[str, str]],
                                source: str) -> bool:
        """Update management information for a company.
        
        Args:
            company_id: ID of the company to update
            officers: List of officer dictionaries
            board_members: List of board member dictionaries
            source: Source of the data ('local' or 'llm')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Update data source
                    cur.execute("""
                        UPDATE mining_companies
                        SET data_source = jsonb_set(
                            data_source,
                            '{officers}',
                            %s::jsonb
                        )
                        WHERE id = %s;
                    """, (f'"{source}"', company_id))
                    
                    cur.execute("""
                        UPDATE mining_companies
                        SET data_source = jsonb_set(
                            data_source,
                            '{board_members}',
                            %s::jsonb
                        )
                        WHERE id = %s;
                    """, (f'"{source}"', company_id))
                    
                    # Update officers and board members
                    cur.execute("""
                        UPDATE mining_companies
                        SET officers = %s::jsonb,
                            board_members = %s::jsonb
                        WHERE id = %s;
                    """, (officers, board_members, company_id))
                    return True
        except Exception as e:
            print(f"Error updating company management: {str(e)}")
            return False
    
    def update_company_officers(self, company_id: int, officers: List[Dict[str, str]], source: str) -> bool:
        """Update officers for a company.
        
        Args:
            company_id: ID of the company to update
            officers: List of officer dictionaries
            source: Source of the data ('local' or 'llm')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Update data source
                    cur.execute("""
                        UPDATE mining_companies
                        SET data_source = jsonb_set(
                            data_source,
                            '{officers}',
                            %s::jsonb
                        )
                        WHERE id = %s;
                    """, (f'"{source}"', company_id))
                    
                    # Update officers
                    cur.execute("""
                        UPDATE mining_companies
                        SET officers = %s::jsonb
                        WHERE id = %s;
                    """, (officers, company_id))
                    return True
        except Exception as e:
            print(f"Error updating company officers: {str(e)}")
            return False
    
    def update_company_board(self, company_id: int, board_members: List[Dict[str, str]], source: str) -> bool:
        """Update board members for a company.
        
        Args:
            company_id: ID of the company to update
            board_members: List of board member dictionaries
            source: Source of the data ('local' or 'llm')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Update data source
                    cur.execute("""
                        UPDATE mining_companies
                        SET data_source = jsonb_set(
                            data_source,
                            '{board_members}',
                            %s::jsonb
                        )
                        WHERE id = %s;
                    """, (f'"{source}"', company_id))
                    
                    # Update board members
                    cur.execute("""
                        UPDATE mining_companies
                        SET board_members = %s::jsonb
                        WHERE id = %s;
                    """, (board_members, company_id))
                    return True
        except Exception as e:
            print(f"Error updating company board members: {str(e)}")
            return False
    
    def search_companies_by_officer(self, name: str) -> List[Dict[str, Any]]:
        """Search for companies by officer name.
        
        Args:
            name: Name of the officer to search for
            
        Returns:
            List of company dictionaries where the officer was found
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, website, company_name, ticker, exchange,
                           headquarters_location, founded_date, description,
                           officers, board_members, data_source
                    FROM mining_companies
                    WHERE officers @> '[{"name": %s}]'::jsonb
                    ORDER BY company_name;
                """, (name,))
                return cur.fetchall()
    
    def search_companies_by_role(self, role: str) -> List[Dict[str, Any]]:
        """Search for companies by officer/board member role.
        
        Args:
            role: Role/title to search for
            
        Returns:
            List of company dictionaries where the role was found
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, website, company_name, ticker, exchange,
                           headquarters_location, founded_date, description,
                           officers, board_members, data_source
                    FROM mining_companies
                    WHERE officers @> '[{"title": %s}]'::jsonb
                       OR board_members @> '[{"title": %s}]'::jsonb
                    ORDER BY company_name;
                """, (role, role))
                return cur.fetchall()
    
    def get_all_officers(self) -> List[Dict[str, Any]]:
        """Get all officers across all companies.
        
        Returns:
            List of dictionaries containing company and officer information
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT company_name,
                           jsonb_array_elements(officers)->>'name' as officer_name,
                           jsonb_array_elements(officers)->>'title' as officer_title,
                           data_source->>'officers' as data_source
                    FROM mining_companies
                    WHERE jsonb_array_length(officers) > 0
                    ORDER BY company_name, officer_name;
                """)
                return cur.fetchall()
    
    def get_all_board_members(self) -> List[Dict[str, Any]]:
        """Get all board members across all companies.
        
        Returns:
            List of dictionaries containing company and board member information
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT company_name,
                           jsonb_array_elements(board_members)->>'name' as member_name,
                           jsonb_array_elements(board_members)->>'title' as member_title,
                           data_source->>'board_members' as data_source
                    FROM mining_companies
                    WHERE jsonb_array_length(board_members) > 0
                    ORDER BY company_name, member_name;
                """)
                return cur.fetchall() 