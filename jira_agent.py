from autogen import ConversableAgent
from src.tools.jira_create_tool import create_jira_story
from src.config.settings import LLM_CONFIG
import json
import os
from pathlib import Path
import streamlit as st

def process_stories() -> str:
    """Create Jira stories from the stories folder."""
    try:
        print(f"\n=== Jira_Agent Processing Stories ===")
        
        # Get stories directory
        project_root = str(Path(__file__).parent.parent.parent)
        stories_dir = os.path.join(project_root, "stories")
        
        # Get stories file from session state
        stories_file = st.session_state.get("stories_file")
        if not stories_file:
            print("No stories file found")
            return "No stories file found"
        
        # Construct full path to stories file
        stories_path = os.path.join(stories_dir, stories_file)
        
        if not os.path.exists(stories_path):
            print(f"Stories file not found: {stories_path}")
            return "Stories file not found"
        
        # Read stories
        with open(stories_path, 'r') as f:
            stories = json.load(f)
        
        if not stories:
            print("No stories to create")
            return "No stories to create"
        
        print(f"Creating {len(stories)} stories in Jira")
        # Create stories
        issue_keys = []
        for story in stories:
            if "summary" not in story or "description" not in story:
                print(f"Invalid story format: {story}")
                continue
                
            issue_key = create_jira_story({
                "summary": story["summary"],
                "description": story["description"]
            })
            issue_keys.append(issue_key)
            print(f"Created story: {issue_key}")
        
        print("Jira story creation complete")
        return "Stories created in Jira"
        
    except json.JSONDecodeError:
        print("Invalid JSON format")
        return "Invalid JSON format"
    except Exception as e:
        print(f"Error in Jira_Agent: {str(e)}")
        return f"Error in Jira_Agent: {str(e)}"

jira_agent = ConversableAgent(
    name="Jira_Agent",
    system_message="""You are a Jira Agent.
Tasks:
1. Read stories from the stories folder
2. Create Jira stories with issue type 'Story' and project 'SDLC'
3. Return 'Stories created in Jira' on success""",
    llm_config=LLM_CONFIG,
    human_input_mode="NEVER",
    max_consecutive_auto_reply=3,
    code_execution_config=False
)

@jira_agent.register_for_execution()
@jira_agent.register_for_llm(description="Create Jira stories from the stories folder.")
def process_stories_wrapper() -> str:
    return process_stories()
