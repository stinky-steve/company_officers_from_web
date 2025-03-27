"""Tests for the company service."""

import pytest
from pathlib import Path
import csv
import tempfile
from typing import List

from src.services.company_service import CompanyService
from src.models.company import Company


@pytest.fixture
def sample_companies_file() -> Path:
    """Create a temporary CSV file with sample company data."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        writer = csv.writer(f)
        writer.writerow(['URL', 'Name', 'Exchange', 'Ticker'])
        writer.writerow(['https://example1.com', 'Company One', 'NYSE', 'ONE'])
        writer.writerow(['https://example2.com', 'Company Two', 'TSX', 'TWO'])
        writer.writerow(['https://example3.com', 'Company Three', 'NYSE', 'THREE'])
        return Path(f.name)


@pytest.fixture
def company_service(sample_companies_file) -> CompanyService:
    """Create a CompanyService instance with sample data."""
    return CompanyService(companies_file=sample_companies_file)


def test_load_companies(company_service):
    """Test loading companies from CSV file."""
    companies = company_service.load_companies()
    assert len(companies) == 3
    
    # Check first company
    assert companies[0].url == 'https://example1.com'
    assert companies[0].name == 'Company One'
    assert companies[0].exchange == 'NYSE'
    assert companies[0].ticker == 'ONE'


def test_get_company_by_url(company_service):
    """Test getting company by URL."""
    company = company_service.get_company_by_url('https://example1.com')
    assert company is not None
    assert company.name == 'Company One'
    
    # Test non-existent URL
    company = company_service.get_company_by_url('https://nonexistent.com')
    assert company is None


def test_get_company_by_name(company_service):
    """Test getting company by name."""
    company = company_service.get_company_by_name('Company Two')
    assert company is not None
    assert company.url == 'https://example2.com'
    
    # Test case-insensitive
    company = company_service.get_company_by_name('company two')
    assert company is not None
    
    # Test non-existent name
    company = company_service.get_company_by_name('Nonexistent Company')
    assert company is None


def test_get_company_by_ticker(company_service):
    """Test getting company by ticker."""
    company = company_service.get_company_by_ticker('THREE')
    assert company is not None
    assert company.name == 'Company Three'
    
    # Test case-insensitive
    company = company_service.get_company_by_ticker('three')
    assert company is not None
    
    # Test non-existent ticker
    company = company_service.get_company_by_ticker('NONE')
    assert company is None


def test_get_companies_by_exchange(company_service):
    """Test getting companies by exchange."""
    nyse_companies = company_service.get_companies_by_exchange('NYSE')
    assert len(nyse_companies) == 2
    assert all(c.exchange == 'NYSE' for c in nyse_companies)
    
    # Test non-existent exchange
    nonexistent_companies = company_service.get_companies_by_exchange('NONEXISTENT')
    assert len(nonexistent_companies) == 0


def test_get_companies_dict(company_service):
    """Test getting companies dictionary."""
    companies_dict = company_service.get_companies_dict()
    assert len(companies_dict) == 3
    assert 'https://example1.com' in companies_dict
    assert companies_dict['https://example1.com'].name == 'Company One'


def test_invalid_file():
    """Test handling of invalid file."""
    service = CompanyService(companies_file=Path('nonexistent.csv'))
    with pytest.raises(FileNotFoundError):
        service.load_companies() 