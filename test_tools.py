"""Test cases for tools."""

import pytest
import os
import json
from pathlib import Path
from unittest.mock import MagicMock
from src.tools.jira_create_tool import create_jira_story
from tests import TEST_DATA_DIR

@pytest.fixture
def mock_jira(monkeypatch):
    """Create a mock Jira client."""
    mock = MagicMock()
    mock.create_issue.return_value = {"key": "TEST-1"}
    mock.search_issues.return_value = [{
        "key": "TEST-1",
        "fields": {
            "summary": "Test Story",
            "description": "Test Description",
            "priority": {"name": "Medium"},
            "customfield_10016": 3,  # Story points
            "issuetype": {"name": "User Story"}
        }
    }]
    
    # Mock JIRA class
    class MockJIRA:
        def __init__(self, *args, **kwargs):
            pass
        
        def create_issue(self, *args, **kwargs):
            return mock.create_issue(*args, **kwargs)
        
        def search_issues(self, *args, **kwargs):
            return mock.search_issues(*args, **kwargs)
    
    monkeypatch.setattr("jira.JIRA", MockJIRA)
    return mock

@pytest.fixture
def sample_story():
    """Create a sample story for testing."""
    return {
        "summary": "As a user, I want to create an account",
        "description": "User Story: Create account with email and password",
        "priority": "Medium",
        "story_points": 3,
        "type": "User Story"
    }

def test_create_jira_story(sample_story, mock_jira):
    """Test creating a Jira story."""
    # Create story
    result = create_jira_story(sample_story)
    
    # Check result
    assert result == "TEST-1"
    mock_jira.create_issue.assert_called_once()

def test_get_jira_stories(mock_jira):
    """Test getting Jira stories."""
    # Get stories
    result = get_jira_stories()
    
    # Check result
    assert len(result) == 1
    assert result[0]["key"] == "TEST-1"
    assert result[0]["summary"] == "Test Story"
    assert result[0]["description"] == "Test Description"
    assert result[0]["priority"] == "Medium"
    assert result[0]["story_points"] == 3
    assert result[0]["type"] == "User Story"
    mock_jira.search_issues.assert_called_once()

def test_create_jira_story_error(mock_jira):
    """Test error handling in create_jira_story."""
    # Mock Jira API call to raise exception
    mock_jira.create_issue.side_effect = Exception("Jira API error")
    
    # Try to create story
    with pytest.raises(Exception):
        create_jira_story({})

def test_get_jira_stories_error(mock_jira):
    """Test error handling in get_jira_stories."""
    # Mock Jira API call to raise exception
    mock_jira.search_issues.side_effect = Exception("Jira API error")
    
    # Try to get stories
    with pytest.raises(Exception):
        get_jira_stories()

@pytest.mark.integration
def test_jira_tools_integration(sample_story, mock_jira):
    """Test integration between create and get Jira tools."""
    # Create story
    key = create_jira_story(sample_story)
    assert key == "TEST-1"
    
    # Get stories
    stories = get_jira_stories()
    assert len(stories) == 1
    assert stories[0]["key"] == key
    
    # Verify mock calls
    mock_jira.create_issue.assert_called_once()
    mock_jira.search_issues.assert_called_once() 