"""Test cases for orchestrator."""

import pytest
import os
from pathlib import Path
from src.orchestrator import custom_speaker_selection, start_agent_workflow
from src.agents.ba_agent import ba_agent
from src.agents.user_agent import user_agent
from src.agents.jira_agent import jira_agent
from src.agents.coder_agent import coder_agent
from autogen import GroupChat
from tests import TEST_DATA_DIR

@pytest.fixture
def mock_groupchat():
    """Create a mock group chat for testing."""
    return GroupChat(
        agents=[ba_agent, user_agent, jira_agent, coder_agent],
        messages=[],
        max_round=10
    )

@pytest.fixture
def sample_requirements():
    """Create sample requirements file for testing."""
    requirements = """1. User Creation
- Need simple user creation form with email, password, and name
- On submit, create user in csv file"""
    
    file_path = os.path.join(TEST_DATA_DIR, "test_orchestrator_requirements.txt")
    with open(file_path, "w") as f:
        f.write(requirements)
    return file_path

def test_speaker_selection_initial(mock_groupchat):
    """Test speaker selection with no last speaker."""
    next_speaker = custom_speaker_selection(None, mock_groupchat)
    assert next_speaker is ba_agent

def test_speaker_selection_ba_agent(mock_groupchat):
    """Test speaker selection after BA Agent."""
    # Mock message content
    mock_groupchat.messages = [{
        "content": "Generated and saved 5 stories to stories/test.txt",
        "name": "BA_Agent"
    }]
    
    next_speaker = custom_speaker_selection(ba_agent, mock_groupchat)
    assert next_speaker is user_agent

def test_speaker_selection_user_agent(mock_groupchat, monkeypatch):
    """Test speaker selection after User Agent."""
    # Mock session state
    import streamlit as st
    monkeypatch.setattr(st.session_state, "get", lambda x, y=None: {
        "workflow_status": "stories_approved",
        "stories_approved": True,
        "code_approved": False
    }.get(x, y))
    
    next_speaker = custom_speaker_selection(user_agent, mock_groupchat)
    assert next_speaker is jira_agent

def test_speaker_selection_jira_agent(mock_groupchat):
    """Test speaker selection after Jira Agent."""
    # Mock message content
    mock_groupchat.messages = [{
        "content": "Stories created in Jira",
        "name": "Jira_Agent"
    }]
    
    next_speaker = custom_speaker_selection(jira_agent, mock_groupchat)
    assert next_speaker is coder_agent

def test_speaker_selection_coder_agent(mock_groupchat, monkeypatch):
    """Test speaker selection after Coder Agent."""
    # Mock session state and file existence
    import streamlit as st
    monkeypatch.setattr(st.session_state, "get", lambda x, y=None: {
        "code_file": "/path/to/code.py"
    }.get(x, y))
    monkeypatch.setattr(os.path, "exists", lambda x: True)
    
    next_speaker = custom_speaker_selection(coder_agent, mock_groupchat)
    assert next_speaker is user_agent

@pytest.mark.integration
def test_workflow_start(sample_requirements, monkeypatch):
    """Test starting the workflow."""
    # Mock necessary functions
    def mock_initiate_chat(*args, **kwargs):
        return None
    
    monkeypatch.setattr(ba_agent, "initiate_chat", mock_initiate_chat)
    
    # Start workflow
    try:
        start_agent_workflow(sample_requirements)
        assert True  # If we get here, no exception was raised
    except Exception as e:
        pytest.fail(f"Workflow start failed: {str(e)}")

def test_workflow_error_handling(monkeypatch):
    """Test workflow error handling."""
    # Mock file path that doesn't exist
    non_existent_file = "/path/to/nonexistent.txt"
    
    # Start workflow with non-existent file
    with pytest.raises(Exception):
        start_agent_workflow(non_existent_file) 