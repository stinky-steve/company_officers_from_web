"""Shared fixtures for all test modules."""

import pytest
from pathlib import Path
from typing import Dict, List

@pytest.fixture
def test_data_dir(tmp_path) -> Path:
    """Create a temporary directory for test data."""
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    return data_dir

@pytest.fixture
def sample_company_json() -> Dict:
    """Create a sample company JSON structure."""
    return {
        "company_name": "Test Mining Corp",
        "leadership": {
            "executives": [
                {"name": "John Doe", "title": "Chief Executive Officer"},
                {"name": "Jane Smith", "title": "Chief Financial Officer"}
            ],
            "board_members": [
                {"name": "Alice Johnson", "title": "Board Chair"},
                {"name": "Bob Wilson", "title": "Independent Director"}
            ]
        }
    }

@pytest.fixture
def sample_management_list() -> List[Dict]:
    """Create a sample list of management entries."""
    return [
        {
            "source": "Test Mining Corp",
            "name": "John Doe",
            "role": "Chief Executive Officer"
        },
        {
            "source": "Test Mining Corp",
            "name": "Jane Smith",
            "role": "Chief Financial Officer"
        },
        {
            "source": "Test Mining Corp",
            "name": "Alice Johnson",
            "role": "Board Chair"
        }
    ]

@pytest.fixture
def mock_openai_response():
    """Create a mock OpenAI API response."""
    return {
        "choices": [{
            "message": {
                "content": '[{"name": "John Doe", "role": "Chief Executive Officer"}, {"name": "Jane Smith", "role": "Chief Financial Officer"}]'
            }
        }]
    } 