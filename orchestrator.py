from autogen import GroupChat, GroupChatManager
from src.agents.ba_agent import ba_agent
from src.agents.jira_agent import jira_agent
from src.agents.user_agent import user_agent
from src.agents.coder_agent import coder_agent
from src.config.settings import LLM_CONFIG
import streamlit as st
import os
import json
from pathlib import Path
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Global variable for file path
abs_file_path = None

def create_ba_agent():
    """Create and return the BA agent."""
    return ba_agent

def create_user_agent():
    """Create and return the User agent."""
    return user_agent

def create_jira_agent():
    """Create and return the Jira agent."""
    return jira_agent

def create_coder_agent():
    """Create and return the Coder agent."""
    return coder_agent

def custom_speaker_selection(last_speaker, groupchat: GroupChat):
    """Custom speaker selection method to manage agent flow."""
    if not last_speaker:
        return ba_agent  # Start with BA Agent
    
    # Get message content from the last message
    last_message = groupchat.messages[-1] if groupchat.messages else None
    content = last_message.get('content', '') if last_message else ''
    
    logger.info(f"Last speaker: {last_speaker.name}")
    logger.info(f"Message content: {content[:200]}...")
    
    # Get current workflow status
    workflow_status = st.session_state.get("workflow_status", "initial")
    stories_approved = st.session_state.get("stories_approved", False)
    code_approved = st.session_state.get("code_approved", False)
    stories_file = st.session_state.get("stories_file")
    code_file = st.session_state.get("code_file")
    
    # Get both project root and workspace root paths
    project_root = Path(__file__).parent.parent.parent
    workspace_root = "/Users/mystic/Documents/projects/autogen-sdlc"
    
    logger.info(f"Current workflow status: {workflow_status}")
    logger.info(f"Stories approved: {stories_approved}")
    logger.info(f"Code approved: {code_approved}")
    logger.info(f"Stories file: {stories_file}")
    logger.info(f"Code file: {code_file}")
    logger.info(f"Project root: {project_root}")
    logger.info(f"Workspace root: {workspace_root}")
    
    # BA Agent flow
    if last_speaker is ba_agent:
        if "Generated and saved" in content:
            st.session_state["workflow_status"] = "stories_generated"
            return user_agent
        return ba_agent
    
    # User Agent flow
    elif last_speaker is user_agent:
        if stories_approved and workflow_status == "stories_approved":
            return jira_agent
        elif code_approved and workflow_status == "code_approved":
            return None  # End conversation
        return user_agent
    
    # Jira Agent flow
    elif last_speaker is jira_agent:
        if "Stories created in Jira" in content:
            st.session_state["workflow_status"] = "code_generation"
            
            return coder_agent
        return jira_agent
    
    # Coder Agent flow
    elif last_speaker is coder_agent:
        # Check if code file exists in session state
        if code_file and os.path.exists(code_file):
            st.session_state["workflow_status"] = "code_generated"
            return user_agent
        # If no code file yet, let Coder Agent continue
        return coder_agent
    
    # Default: Start with BA Agent
    return ba_agent

def message_handler(recipient, messages, sender, config):
    """Handle messages to control agent transitions."""
    if not messages:
        return None, None
    
    current_message = messages[-1].get('content', '')
    logger.info(f"\n=== Message from {sender.name} ===")
    logger.info(f"Message: {current_message[:200]}...")
    
    # BA_Agent: Handle success message
    if sender.name == 'BA_Agent':
        if "Generated and saved" in current_message or "successfully processed" in current_message:
            # Set stories file in session state
            input_filename = os.path.basename(abs_file_path)
            stories_file = f"stories_{input_filename}"
            st.session_state["stories_file"] = stories_file
            st.session_state["workflow_status"] = "stories_generated"
            logger.info(f"Set stories file in session state: {stories_file}")
            # Pass the exact message to User agent
            return user_agent, current_message
        
        # Continue with BA_Agent for other messages
        logger.info("Continuing with BA Agent")
        return ba_agent, current_message
    
    # User_Agent: After approval, transition to Jira agent
    elif sender.name == 'User_Agent':
        if st.session_state["workflow_status"] == "validating_stories":
            # Keep User Agent active for validation
            logger.info("User Agent validating stories")
            return user_agent, "Please validate the stories and provide feedback."
        elif "Stories approved" in current_message:
            logger.info("User Agent approved stories, transitioning to Jira Agent")
            st.session_state["workflow_status"] = "stories_approved"
            return jira_agent, "Create Jira tickets from the stories in the stories folder."
        elif "Waiting for approval" in current_message:
            logger.info("User Agent waiting for approval")
            return user_agent, current_message
        else:
            logger.info("User Agent processing message")
            return user_agent, current_message
    
    # Jira_Agent: After creating tickets, end workflow
    elif sender.name == 'Jira_Agent':
        if "Stories created in Jira" in current_message:
            logger.info("Jira Agent completed, workflow finished")
            st.session_state["workflow_status"] = "completed"
            return None, None
        else:
            logger.info("Jira Agent processing message")
            return jira_agent, current_message
    
    # Default: Continue with current recipient
    return recipient, current_message

def update_group_chat(message: str):
    """Update the group chat with a new message.
    
    Args:
        message: The message to send to the group chat
    """
    try:
        if "chat_manager" in st.session_state and st.session_state["chat_manager"]:
            manager = st.session_state["chat_manager"]
            # Send message to the group chat
            manager.run(message)
            logger.info(f"Group chat updated with message: {message[:200]}...")
        else:
            logger.error("No chat manager found in session state")
    except Exception as e:
        logger.error(f"Error updating group chat: {str(e)}")

def start_agent_workflow(file_path: str) -> None:
    """Start the agent workflow.
    
    Args:
        file_path: Path to the requirements file
    """
    try:
        logger.info("\n=== Starting Workflow ===")
        logger.info(f"Processing file: {file_path}")
        
        # Create group chat with all agents
        groupchat = GroupChat(
            agents=[ba_agent, user_agent, jira_agent, coder_agent],
            messages=[],
            max_round=10,
            speaker_selection_method=custom_speaker_selection
        )
        
        # Create chat manager
        manager = GroupChatManager(
            groupchat=groupchat,
            llm_config=LLM_CONFIG
        )
        
        # Store chat manager in session state
        st.session_state["chat_manager"] = manager
        
        logger.info("\n=== Starting BA Agent ===")
        # Start the conversation with BA Agent
        ba_agent.initiate_chat(
            manager,
            message=f"Read the requirements file at '{file_path}' and generate Jira stories. Save them to the stories folder and return a success message."
        )
        
    except Exception as e:
        logger.error(f"Error in workflow: {str(e)}")
        raise