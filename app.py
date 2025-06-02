import os
import sys
from pathlib import Path
import json
from datetime import datetime
import logging
import time

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

import streamlit as st
from src.orchestrator import start_agent_workflow

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/sdlc.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure input directory
input_dir = os.path.join(project_root, "input")
os.makedirs(input_dir, exist_ok=True)

# Initialize session state
if "processing" not in st.session_state:
    st.session_state["processing"] = False
if "stories_json" not in st.session_state:
    st.session_state["stories_json"] = None
if "user_agent_trigger" not in st.session_state:
    st.session_state["user_agent_trigger"] = False
if "workflow_started" not in st.session_state:
    st.session_state["workflow_started"] = False
if "current_file" not in st.session_state:
    st.session_state["current_file"] = None
if "stories_ready" not in st.session_state:
    st.session_state["stories_ready"] = False
if "approved_stories" not in st.session_state:
    st.session_state["approved_stories"] = None

def start_workflow(file_path: str, is_approval: bool = False):
    """Start the agent workflow and handle state."""
    try:
        # Clear previous state
        st.session_state["processing"] = True
        if not is_approval:
            st.session_state["stories_json"] = None
            st.session_state["user_agent_trigger"] = False
            st.session_state["workflow_started"] = True
            st.session_state["current_file"] = file_path
            st.session_state["stories_ready"] = False
            st.session_state["approved_stories"] = None
        
        # Start agent workflow
        start_agent_workflow(file_path)
        
        # Reset processing state
        st.session_state["processing"] = False
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        logger.error(f"Error: {str(e)}", exc_info=True)
        st.session_state["processing"] = False
        if not is_approval:
            st.session_state["workflow_started"] = False
            st.session_state["current_file"] = None
            st.session_state["stories_ready"] = False
            st.session_state["approved_stories"] = None

st.title("AutoGen SDLC POC")
st.header("Upload Requirements (.txt only)")

# File uploader
uploaded_file = st.file_uploader("Choose a .txt file", type=["txt"])

# Upload and process button
if st.button("Upload and Process") and not st.session_state["processing"]:
    if uploaded_file:
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"upload_{timestamp}.txt"
            file_path = os.path.join(input_dir, filename)

            # Save file
            with open(file_path, "wb") as f:
                f.write(uploaded_file.read())

            st.success(f"File uploaded to {file_path}")
            logger.info(f"Uploaded file: {file_path}")

            # Start workflow
            start_workflow(file_path)
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
            logger.error(f"Error: {str(e)}", exc_info=True)
    else:
        st.error("Please upload a .txt file.")
        logger.warning("Upload attempted without file.")

# Display processing status
if st.session_state["processing"]:
    st.info("Processing requirements... Please wait.")
    with st.spinner("Processing..."):
        time.sleep(0.1)  # Allow UI to update

# Check if stories are ready
if st.session_state["stories_json"] and st.session_state["current_file"] and not st.session_state["stories_ready"]:
    st.session_state["stories_ready"] = True
    st.rerun()

# Display stories if available and from current run
if st.session_state["stories_json"] and st.session_state["current_file"]:
    try:
        stories = json.loads(st.session_state["stories_json"])
        if not stories:
            st.error("No stories to display.")
            logger.warning("Empty stories JSON received")
        else:
            st.header("Review and Approve Jira Stories")
            st.info("Please review the stories below. Click 'Approve' to create them in Jira.")
            
            # Create a container for stories
            stories_container = st.container()
            with stories_container:
                for i, story in enumerate(stories, 1):
                    with st.expander(f"Story {i}: {story['summary']}", expanded=True):
                        st.write(f"**Summary**: {story['summary']}")
                        st.write(f"**Description**: {story['description']}")
                        if "priority" in story:
                            st.write(f"**Priority**: {story['priority']}")

            # Approval button in a separate container
            approval_container = st.container()
            with approval_container:
                # Only disable the button if we're actively processing
                if st.button("Approve and Create Stories", key="approve_button", disabled=st.session_state["processing"] and not st.session_state["stories_ready"]):
                    st.session_state["user_agent_trigger"] = True
                    st.session_state["approved_stories"] = st.session_state["stories_json"]
                    st.success("Stories approved! Creating stories in Jira...")
                    logger.info("Stories approved by user")
                    # Restart workflow with current file to process approval
                    start_workflow(st.session_state["current_file"], is_approval=True)
                    st.rerun()
                    
    except json.JSONDecodeError:
        st.error("Invalid stories JSON format.")
        logger.error("Invalid JSON format for stories")
    except Exception as e:
        st.error(f"Error displaying stories: {str(e)}")
        logger.error(f"Error displaying stories: {str(e)}", exc_info=True)

# Simple auto-refresh if workflow is active and not ready
if st.session_state["workflow_started"] and not st.session_state["stories_ready"]:
    time.sleep(1)  # Wait a bit before refreshing
    st.rerun()
