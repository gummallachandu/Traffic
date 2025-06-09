from autogen import ConversableAgent
from src.config.settings import LLM_CONFIG
import streamlit as st
import json
import os
from pathlib import Path
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def display_stories_from_folder():
    """Display stories from the stories folder."""
    try:
        # Get stories directory
        project_root = str(Path(__file__).parent.parent.parent)
        stories_dir = os.path.join(project_root, "stories")
        
        # Get stories file from session state
        stories_file = st.session_state.get("stories_file")
        logger.info(f"Looking for stories file: {stories_file}")
        
        if not stories_file:
            # Try to find the most recent stories file
            story_files = [f for f in os.listdir(stories_dir) if f.startswith("stories_")]
            if story_files:
                stories_file = sorted(story_files)[-1]  # Get the most recent file
                logger.info(f"Found most recent stories file: {stories_file}")
                # Update session state with the found file
                st.session_state["stories_file"] = stories_file
            else:
                logger.warning("No stories file found. Please generate stories first.")
                return "No stories found"
        
        # Construct full path to stories file
        stories_path = os.path.join(stories_dir, stories_file)
        logger.info(f"Reading stories from: {stories_path}")
        
        if not os.path.exists(stories_path):
            logger.warning(f"Stories file not found: {stories_path}")
            return "Stories file not found"
        
        # Read and display stories
        try:
            with open(stories_path, 'r') as f:
                stories = json.load(f)
                st.json(stories)
                # Don't return approval message - wait for UI button
                return "Stories displayed in UI. Waiting for user approval via button click."
        except Exception as e:
            logger.error(f"Error reading stories: {str(e)}")
            return f"Error reading stories: {str(e)}"
        
    except Exception as e:
        logger.error(f"Error displaying stories: {str(e)}")
        return f"Error displaying stories: {str(e)}"

# Create the user agent
user_agent = ConversableAgent(
    name="User_Agent",
    llm_config=LLM_CONFIG,
    system_message="""You are a User Interface agent responsible for displaying stories and handling user approval.
Your tasks are:
1. Read stories from the stories folder
2. Display stories in a user-friendly format
3. Wait for user approval through the Streamlit UI button click
4. Only return 'Stories approved' when the UI button has been clicked

IMPORTANT: 
- When you receive a message containing 'Generated and saved', immediately call display_stories_from_folder
- Do not automatically approve stories - wait for UI button click
- Only return 'Stories approved' when st.session_state['stories_approved'] is True
- For all other messages, process them automatically without human input""",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=3,
    code_execution_config=False
)

# Register the function with the agent
@user_agent.register_for_execution()
@user_agent.register_for_llm(name="display_stories_from_folder", description="Display stories from the stories folder and wait for UI approval.")
def handle_stories() -> str:
    result = display_stories_from_folder()
    # Only return approval if UI button was clicked
    if st.session_state.get("stories_approved", False):
        return "Stories approved"
    return result
