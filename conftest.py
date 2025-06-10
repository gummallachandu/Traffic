"""Pytest configuration."""

import pytest
import os
import shutil
from pathlib import Path

@pytest.fixture(autouse=True)
def setup_teardown():
    """Setup and teardown for each test."""
    # Setup
    test_data_dir = os.path.join(Path(__file__).parent, "test_data")
    os.makedirs(test_data_dir, exist_ok=True)
    
    # Run test
    yield
    
    # Teardown
    if os.path.exists(test_data_dir):
        shutil.rmtree(test_data_dir)

@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Mock environment variables."""
    monkeypatch.setenv("JIRA_API_TOKEN", "test_token")
    monkeypatch.setenv("JIRA_EMAIL", "test@example.com")
    monkeypatch.setenv("JIRA_SERVER", "https://test.atlassian.net")
    monkeypatch.setenv("OPENAI_API_KEY", "test_key") 