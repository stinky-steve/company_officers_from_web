"""Data models for company information."""

from dataclasses import dataclass
from typing import Optional, List, Dict
from pathlib import Path
from enum import Enum
from datetime import date


class Exchange(Enum):
    """Stock exchange where the company is listed."""
    TSXV = "TSXV"  # TSX Venture Exchange
    CSE = "CSE"    # Canadian Securities Exchange
    TSX = "TSX"    # Toronto Stock Exchange


@dataclass
class Company:
    """Class representing a mining company."""
    
    id: Optional[int]
    website: str
    company_name: str
    ticker: Optional[str]
    exchange: Optional[str]
    headquarters_location: Optional[str]
    founded_date: Optional[date]
    description: Optional[str]
    officers: List[Dict[str, str]]
    board_members: List[Dict[str, str]]
    data_source: Dict[str, str]
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Company':
        """Create a Company instance from a dictionary.
        
        Args:
            data: Dictionary containing company data
            
        Returns:
            Company instance
        """
        return cls(
            id=data.get('id'),
            website=data['website'],
            company_name=data['company_name'],
            ticker=data.get('ticker'),
            exchange=data.get('exchange'),
            headquarters_location=data.get('headquarters_location'),
            founded_date=data.get('founded_date'),
            description=data.get('description'),
            officers=data.get('officers', []),
            board_members=data.get('board_members', []),
            data_source=data.get('data_source', {'officers': 'local', 'board_members': 'local'})
        )
    
    def to_dict(self) -> Dict:
        """Convert the Company instance to a dictionary.
        
        Returns:
            Dictionary containing company data
        """
        return {
            'id': self.id,
            'website': self.website,
            'company_name': self.company_name,
            'ticker': self.ticker,
            'exchange': self.exchange,
            'headquarters_location': self.headquarters_location,
            'founded_date': self.founded_date,
            'description': self.description,
            'officers': self.officers,
            'board_members': self.board_members,
            'data_source': self.data_source
        }
    
    def update_management(self, officers: List[Dict[str, str]], 
                         board_members: List[Dict[str, str]], 
                         source: str = 'llm') -> None:
        """Update management information.
        
        Args:
            officers: List of officer dictionaries
            board_members: List of board member dictionaries
            source: Source of the data ('local' or 'llm')
        """
        self.officers = officers
        self.board_members = board_members
        self.data_source['officers'] = source
        self.data_source['board_members'] = source
    
    def update_officers(self, officers: List[Dict[str, str]], source: str = 'llm') -> None:
        """Update officers information.
        
        Args:
            officers: List of officer dictionaries
            source: Source of the data ('local' or 'llm')
        """
        self.officers = officers
        self.data_source['officers'] = source
    
    def update_board_members(self, board_members: List[Dict[str, str]], source: str = 'llm') -> None:
        """Update board members information.
        
        Args:
            board_members: List of board member dictionaries
            source: Source of the data ('local' or 'llm')
        """
        self.board_members = board_members
        self.data_source['board_members'] = source

    def __str__(self) -> str:
        """String representation of the company."""
        parts = [self.company_name]
        if self.ticker and self.exchange:
            parts.append(f"{self.ticker}:{self.exchange}")
        return " - ".join(parts)

    def __repr__(self) -> str:
        """Return string representation of the company."""
        return self.__str__()
