"""Test cases for the company import script."""

import os
import pytest
from unittest.mock import patch, mock_open, MagicMock, PropertyMock
import psycopg2
from src.scripts.import_companies import import_companies

@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables for database connection."""
    env_vars = {
        'PG_HOST': 'localhost',
        'PG_PORT': '5432',
        'PG_DB': 'test_db',
        'PG_USER': 'test_user',
        'PG_PASS': 'test_pass'
    }
    with patch.dict(os.environ, env_vars):
        yield env_vars

@pytest.fixture
def mock_csv_data():
    """Mock CSV data for testing."""
    return (
        "Website,Company Name,Ticker,Exchange\n"
        "https://www.company1.com,Company One,ONE,TSX\n"
        "http://company2.com,Company Two,TWO,NYSE\n"
        ",Company Three,THREE,CSE\n"
        "company4.com,Company Four,FOUR,ASX\n"
        "https://www.company5.com/,Company Five,FIVE,LSE\n"
    )

@pytest.fixture
def mock_db_connection():
    """Mock database connection and cursor."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    
    # Mock the cursor's mogrify method to return bytes
    def mock_mogrify(query, params):
        # Convert the params to a string and encode it as bytes
        return f"MOCK_SQL_{str(params)}".encode('utf-8')
    
    mock_cur.mogrify = mock_mogrify
    
    # Mock the connection's encoding property
    mock_conn.encoding = 'UTF8'
    
    # Set up cursor's connection property
    mock_cur_conn = MagicMock()
    mock_cur_conn.encoding = 'UTF8'
    mock_cur.connection = mock_cur_conn
    
    # Mock execute_values to simulate successful execution
    def mock_execute(query):
        return None
    
    mock_cur.execute = MagicMock(side_effect=mock_execute)
    
    # Set up connection's cursor method
    mock_conn.cursor.return_value = mock_cur
    
    return mock_conn, mock_cur

def test_csv_parsing(mock_csv_data, mock_db_connection):
    """Test CSV parsing functionality."""
    mock_conn, mock_cur = mock_db_connection
    
    with patch('builtins.open', mock_open(read_data=mock_csv_data)):
        with patch('psycopg2.connect', return_value=mock_conn):
            mock_cur.fetchall.return_value = [(1, 'Company One'), (2, 'Company Two')]
            
            try:
                import_companies()
            except SystemExit:
                pass  # Expected behavior
            
            # Verify that execute was called
            assert mock_cur.execute.called
            # Verify that commit was called
            assert mock_conn.commit.called

def test_empty_company_name_handling(mock_db_connection):
    """Test handling of empty company names."""
    mock_conn, mock_cur = mock_db_connection
    test_data = (
        "Website,Company Name,Ticker,Exchange\n"
        "https://test.com,,TEST,NYSE\n"
    )
    
    with patch('builtins.open', mock_open(read_data=test_data)):
        with patch('psycopg2.connect', return_value=mock_conn):
            try:
                import_companies()
            except SystemExit:
                pass  # Expected behavior
            
            # Verify that execute was not called (no valid companies)
            assert not mock_cur.execute.called

def test_website_url_formatting(mock_db_connection):
    """Test website URL formatting."""
    mock_conn, mock_cur = mock_db_connection
    test_data = (
        "Website,Company Name,Ticker,Exchange\n"
        "www.test.com,Test Company,TEST,NYSE\n"
        "https://test2.com/,Test Company 2,TST2,NYSE\n"
        "http://test3.com,Test Company 3,TST3,NYSE\n"
    )
    
    with patch('builtins.open', mock_open(read_data=test_data)):
        with patch('psycopg2.connect', return_value=mock_conn):
            mock_cur.fetchall.return_value = [(1, 'Test Company')]
            
            try:
                import_companies()
            except SystemExit:
                pass  # Expected behavior
            
            # Verify that execute was called with properly formatted URLs
            assert mock_cur.execute.called
            # Get the first call arguments
            call_args = str(mock_cur.execute.call_args[0][0])
            # Check that the URLs are properly formatted
            assert 'https://www.test.com' in call_args or 'MOCK_SQL_(\'https://www.test.com\'' in call_args

def test_duplicate_company_handling(mock_db_connection):
    """Test handling of duplicate company names."""
    mock_conn, mock_cur = mock_db_connection
    test_data = (
        "Website,Company Name,Ticker,Exchange\n"
        "https://test1.com,Same Company,TST1,NYSE\n"
        "https://test2.com,Same Company,TST2,NYSE\n"
    )
    
    with patch('builtins.open', mock_open(read_data=test_data)):
        with patch('psycopg2.connect', return_value=mock_conn):
            mock_cur.fetchall.return_value = [(1, 'Same Company')]
            
            try:
                import_companies()
            except SystemExit:
                pass  # Expected behavior
            
            # Verify that execute was called
            assert mock_cur.execute.called
            # Verify that the ON CONFLICT clause is present in the query
            call_args = str(mock_cur.execute.call_args[0][0])
            assert 'ON CONFLICT' in call_args

def test_database_connection():
    """Test database connection error handling."""
    with patch('psycopg2.connect') as mock_connect:
        mock_connect.side_effect = psycopg2.Error("Connection failed")
        
        try:
            import_companies()
        except SystemExit:
            pass  # Expected behavior
        
        # Verify that connect was called
        assert mock_connect.called 