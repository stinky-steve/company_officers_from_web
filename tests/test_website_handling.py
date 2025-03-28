"""Test cases for website URL handling in the import script."""

import pytest
from unittest.mock import patch, mock_open
import psycopg2
from src.scripts.import_companies import import_companies

@pytest.fixture
def mock_csv_data():
    """Mock CSV data for testing website URL handling."""
    return (
        "Website,Company Name,Ticker,Exchange\n"
        "https://www.company1.com,Company One,ONE,TSX\n"
        "www.company2.com,Company Two,TWO,NYSE\n"
        ",Company Three,THREE,CSE\n"
        "http://company4.com,Company Four,FOUR,ASX\n"
        "company5.com,Company Five,FIVE,LSE\n"
    )

@pytest.fixture
def mock_db_connection(monkeypatch):
    """Mock database connection and cursor."""
    class MockCursor:
        def __init__(self):
            self.executed_queries = []
            self.connection = type('obj', (object,), {'encoding': 'UTF8'})()

        def execute(self, query, params=None):
            self.executed_queries.append((query, params))
            return []

        def fetchall(self):
            return [(1, 'Company One')]

        def close(self):
            pass

        def mogrify(self, template, params):
            return str(params).encode('utf-8')

    class MockConnection:
        def __init__(self):
            self.cursor_obj = MockCursor()
            self.committed = False
            self.encoding = 'UTF8'

        def cursor(self):
            return self.cursor_obj

        def commit(self):
            self.committed = True

        def close(self):
            pass

    mock_conn = MockConnection()

    def mock_connect(*args, **kwargs):
        return mock_conn

    monkeypatch.setattr(psycopg2, 'connect', mock_connect)
    return mock_conn

def test_website_url_handling(mock_csv_data, mock_db_connection, monkeypatch):
    """Test that website URLs are properly handled during import."""
    # Mock environment variables
    monkeypatch.setenv('PG_HOST', 'localhost')
    monkeypatch.setenv('PG_PORT', '5432')
    monkeypatch.setenv('PG_DB', 'test_db')
    monkeypatch.setenv('PG_USER', 'test_user')
    monkeypatch.setenv('PG_PASS', 'test_pass')

    with patch('builtins.open', mock_open(read_data=mock_csv_data)):
        try:
            import_companies()
        except SystemExit:
            pass

        # Get the executed queries
        executed_queries = mock_db_connection.cursor_obj.executed_queries

        # Check that the correct number of queries were executed
        assert len(executed_queries) > 0

        # Convert the executed queries to string for easier checking
        query_str = str(executed_queries)

        # Check that URLs are properly formatted
        assert 'https://www.company1.com' in query_str
        assert 'https://www.company2.com' in query_str
        assert 'http://placeholder/company-three' in query_str
        assert 'http://company4.com' in query_str
        assert 'https://company5.com' in query_str

def test_empty_website_handling(mock_db_connection, monkeypatch):
    """Test that empty website URLs are properly handled."""
    csv_data = (
        "Website,Company Name,Ticker,Exchange\n"
        ",Test Company,TEST,NYSE\n"
    )

    # Mock environment variables
    monkeypatch.setenv('PG_HOST', 'localhost')
    monkeypatch.setenv('PG_PORT', '5432')
    monkeypatch.setenv('PG_DB', 'test_db')
    monkeypatch.setenv('PG_USER', 'test_user')
    monkeypatch.setenv('PG_PASS', 'test_pass')

    with patch('builtins.open', mock_open(read_data=csv_data)):
        try:
            import_companies()
        except SystemExit:
            pass

        # Get the executed queries
        executed_queries = mock_db_connection.cursor_obj.executed_queries

        # Check that the correct number of queries were executed
        assert len(executed_queries) > 0

        # Convert the executed queries to string for easier checking
        query_str = str(executed_queries)

        # Check that empty website is replaced with placeholder
        assert 'http://placeholder/test-company' in query_str

def test_website_url_normalization(mock_db_connection, monkeypatch):
    """Test that website URLs are properly normalized."""
    csv_data = (
        "Website,Company Name,Ticker,Exchange\n"
        "www.test1.com,Test Company 1,TST1,NYSE\n"
        "test2.com,Test Company 2,TST2,NYSE\n"
        "https://test3.com/,Test Company 3,TST3,NYSE\n"
        "http://test4.com,Test Company 4,TST4,NYSE\n"
    )

    # Mock environment variables
    monkeypatch.setenv('PG_HOST', 'localhost')
    monkeypatch.setenv('PG_PORT', '5432')
    monkeypatch.setenv('PG_DB', 'test_db')
    monkeypatch.setenv('PG_USER', 'test_user')
    monkeypatch.setenv('PG_PASS', 'test_pass')

    with patch('builtins.open', mock_open(read_data=csv_data)):
        try:
            import_companies()
        except SystemExit:
            pass

        # Get the executed queries
        executed_queries = mock_db_connection.cursor_obj.executed_queries

        # Check that the correct number of queries were executed
        assert len(executed_queries) > 0

        # Convert the executed queries to string for easier checking
        query_str = str(executed_queries)

        # Check that URLs are properly normalized
        assert 'https://www.test1.com' in query_str
        assert 'https://test2.com' in query_str
        assert 'https://test3.com/' in query_str
        assert 'http://test4.com' in query_str 