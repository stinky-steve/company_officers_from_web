"""Service for managing LLM operations."""

import os
from typing import List, Dict, Optional, Any
import openai
from dotenv import load_dotenv

class LLMService:
    """Service for managing LLM operations."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the LLM service.
        
        Args:
            config: Configuration dictionary containing API keys and settings
        """
        self.api_key = config['openai_api_key']
        if not self.api_key:
            raise ValueError("OpenAI API key not found in configuration")
        openai.api_key = self.api_key
        self.config = config
        
    def extract_management_info(self, company_name: str, content: str) -> Dict[str, List[Dict[str, str]]]:
        """Extract management information using LLM.
        
        Args:
            company_name: Name of the company
            content: Text content to analyze
            
        Returns:
            Dictionary containing officers and board members
        """
        prompt = f"""Analyze the following text about {company_name} and extract information about:
1. Chief Executive Officer (CEO)
2. Chairman of the Board

Format the response as a JSON object with two arrays:
- officers: Array of objects with 'name' and 'title' fields
- board_members: Array of objects with 'name' and 'title' fields

Only include the CEO and Chairman if they are explicitly mentioned.
If a position is not found, return an empty array.

Text to analyze:
{content}

Response format:
{{
    "officers": [
        {{"name": "John Doe", "title": "Chief Executive Officer"}}
    ],
    "board_members": [
        {{"name": "Jane Smith", "title": "Chairman of the Board"}}
    ]
}}"""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts management information from company text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse the response
            result = response.choices[0].message.content
            return eval(result)  # Convert string to dict
            
        except Exception as e:
            print(f"Error in LLM extraction: {str(e)}")
            return {"officers": [], "board_members": []}
    
    def has_key_positions(self, officers: List[Dict[str, str]], board_members: List[Dict[str, str]]) -> bool:
        """Check if key positions (CEO and Chairman) are present.
        
        Args:
            officers: List of officer dictionaries
            board_members: List of board member dictionaries
            
        Returns:
            True if both CEO and Chairman are found, False otherwise
        """
        has_ceo = any(o['title'].lower() in ['chief executive officer', 'ceo'] for o in officers)
        has_chairman = any(m['title'].lower() in ['chairman', 'chairman of the board'] for m in board_members)
        return has_ceo and has_chairman 
    
    def update_company_management(self, company_id: int, 
                                officers: List[Dict[str, str]], 
                                board_members: List[Dict[str, str]]) -> bool:
        """Update management information for a company using LLM data.
        
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
            source='llm'
        )
    
    def update_company_officers(self, company_id: int, 
                              officers: List[Dict[str, str]]) -> bool:
        """Update officers for a company using LLM data.
        
        Args:
            company_id: ID of the company to update
            officers: List of officer dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        return self.company_service.update_company_officers(
            company_id=company_id,
            officers=officers,
            source='llm'
        )
    
    def update_company_board(self, company_id: int, 
                           board_members: List[Dict[str, str]]) -> bool:
        """Update board members for a company using LLM data.
        
        Args:
            company_id: ID of the company to update
            board_members: List of board member dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        return self.company_service.update_company_board(
            company_id=company_id,
            board_members=board_members,
            source='llm'
        ) 