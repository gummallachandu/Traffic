"""Test cases for agents."""

import pytest
import json
import os
from pathlib import Path
from src.agents.ba_agent import process_requirements_wrapper
from src.agents.jira_agent import process_stories
from src.agents.coder_agent import process_story_to_code
from tests import TEST_DATA_DIR

@pytest.fixture
def sample_requirements():
    """Create sample requirements file for testing."""
    requirements = """1. User Creation
- Need simple user creation form with email, password, and name
- On submit, create user in csv file

2. User List
- List all users from the csv file
- Should have efficient APIs for the UI to consume"""
    
    file_path = os.path.join(TEST_DATA_DIR, "test_requirements.txt")
    with open(file_path, "w") as f:
        f.write(requirements)
    return file_path

@pytest.fixture
def sample_stories():
    """Create sample stories file for testing."""
    stories = [
        {
            "summary": "As a user, I want to create an account",
            "description": "User Story: Create account with email and password",
            "priority": "Medium",
            "story_points": 3,
            "type": "User Story"
        }
    ]
    
    file_path = os.path.join(TEST_DATA_DIR, "test_stories.txt")
    with open(file_path, "w") as f:
        json.dump(stories, f, indent=2)
    return file_path

def test_ba_agent_process_requirements(sample_requirements):
    """Test BA Agent's requirement processing."""
    # Process requirements
    result = process_requirements_wrapper(sample_requirements)
    
    # Check result
    assert "Generated and saved" in result
    
    # Check stories file was created
    stories_file = f"stories_{os.path.basename(sample_requirements)}"
    stories_path = os.path.join(Path(__file__).parent.parent, "stories", stories_file)
    assert os.path.exists(stories_path)
    
    # Check stories content
    with open(stories_path, "r") as f:
        stories = json.load(f)
        assert len(stories) > 0
        assert "summary" in stories[0]
        assert "description" in stories[0]
        assert "priority" in stories[0]
        assert "story_points" in stories[0]
        assert "type" in stories[0]

def test_jira_agent_process_stories(sample_stories, monkeypatch):
    """Test Jira Agent's story processing."""
    # Mock Jira API call
    def mock_create_story(*args, **kwargs):
        return "TEST-1"
    
    from src.tools.jira_create_tool import create_jira_story
    monkeypatch.setattr(create_jira_story, "create_jira_story", mock_create_story)
    
    # Process stories
    result = process_stories()
    
    # Check result
    assert "Stories created in Jira" in result

def test_coder_agent_process_stories(sample_stories):
    """Test Coder Agent's code generation."""
    # Process stories
    result = process_story_to_code()
    
    # Check result
    assert os.path.exists(result)
    
    # Check code content
    with open(result, "r") as f:
        code = f.read()
        assert "def create_user" in code
        assert "email" in code
        assert "password" in code
        assert "name" in code
        assert "docstring" in code.lower()

@pytest.mark.integration
def test_full_workflow(sample_requirements):
    """Test the complete workflow from requirements to code."""
    # 1. Process requirements
    ba_result = process_requirements_wrapper(sample_requirements)
    assert "Generated and saved" in ba_result
    
    # 2. Process stories
    jira_result = process_stories()
    assert "Stories created in Jira" in jira_result
    
    # 3. Generate code
    code_result = process_story_to_code()
    assert os.path.exists(code_result)
    
    # 4. Verify all files exist
    stories_file = f"stories_{os.path.basename(sample_requirements)}"
    stories_path = os.path.join(Path(__file__).parent.parent, "stories", stories_file)
    assert os.path.exists(stories_path)
    assert os.path.exists(code_result) 