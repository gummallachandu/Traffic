
from autogen import ConversableAgent
from src.config.settings import LLM_CONFIG
import logging
import json
import streamlit as st

# Configure logging
logger = logging.getLogger(__name__)

def display_stories(stories_json: str) -> str:
    """Display Jira stories on the Streamlit UI and handle approval flow."""
    logger.info("User_Agent displaying stories")
    try:
        stories = json.loads(stories_json)
        if not stories:
            logger.warning("Empty stories JSON received")
            return json.dumps({"error": "No stories to display"})
            
        st.session_state["stories_json"] = stories_json
        st.session_state["stories_ready"] = True
        
        if "user_agent_trigger" in st.session_state and st.session_state["user_agent_trigger"]:
            logger.info("Approval received, forwarding to Jira_Agent")
            st.session_state["approved_stories"] = stories_json
            st.session_state["user_agent_trigger"] = False
            message = f"Create these Jira stories: {stories_json}"
            logger.info(f"Sending message to Jira Agent: {message[:100]}...")
            return message
            
        logger.info("Stories displayed, waiting for approval")
        return "Stories displayed on UI, waiting for user approval"
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON format for stories")
        return json.dumps({"error": "Invalid JSON format"})
    except Exception as e:
        logger.error(f"Error in display_stories: {str(e)}")
        return json.dumps({"error": str(e)})

user_agent = ConversableAgent(
    name="User_Agent",
    system_message="""You are a User Agent (User_Agent). Your role is to:
    1. Receive a JSON list of Jira stories from BA_Agent
    2. Use the display_stories function to show them on the Streamlit UI
    3. Wait for user approval via the UI's "Approve" button
    4. After approval, send ONE message: "Create these Jira stories: {json_list}" to the group chat
    5. Do not respond to any messages after sending the approval message
    6. If the JSON list is empty or invalid, display an error on the UI and log it
    
    IMPORTANT:
    - Always use display_stories function to show stories
    - Wait for explicit user approval before forwarding to Jira_Agent
    - After sending "Create these Jira stories:", DO NOT respond to any further messages
    - Let the Jira_Agent handle the story creation
    - Log all actions and errors""",
    llm_config=LLM_CONFIG,
    human_input_mode="NEVER",
    max_consecutive_auto_reply=3,
    code_execution_config=False
)

@user_agent.register_for_execution()
@user_agent.register_for_llm(description="Display Jira stories on Streamlit UI and wait for approval.")
def handle_stories(stories_json: str) -> str:
    return display_stories(stories_json)
