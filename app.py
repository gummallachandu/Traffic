import streamlit as st
import os
import sys
from pathlib import Path
import logging
import json
from datetime import datetime

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from autogen import GroupChat
from src.orchestrator import start_agent_workflow, custom_speaker_selection
from src.agents.user_agent import user_agent
from src.agents.ba_agent import ba_agent
from src.agents.jira_agent import jira_agent

logger = logging.getLogger(__name__)

def init_session_state():
    """Initialize all session state variables."""
    if "workflow_status" not in st.session_state:
        st.session_state["workflow_status"] = "initial"
    if "chat_manager" not in st.session_state:
        st.session_state["chat_manager"] = None
    if "uploaded_file_path" not in st.session_state:
        st.session_state["uploaded_file_path"] = None
    if "stories_approved" not in st.session_state:
        st.session_state["stories_approved"] = False
    if "stories_file" not in st.session_state:
        st.session_state["stories_file"] = None
    if "code_approved" not in st.session_state:
        st.session_state["code_approved"] = False
    if "code_file" not in st.session_state:
        st.session_state["code_file"] = None

def main():
    st.title("SDLC Automation")
    
    # Initialize session state
    init_session_state()
    
    # Debug info
    st.sidebar.write("Debug Info:")
    st.sidebar.write(f"Workflow Status: {st.session_state['workflow_status']}")
    st.sidebar.write(f"Stories File: {st.session_state.get('stories_file', 'None')}")
    st.sidebar.write(f"Stories Approved: {st.session_state['stories_approved']}")
    st.sidebar.write(f"Program File: {st.session_state.get('code_file', 'None')}")
    st.sidebar.write(f"Code Approved: {st.session_state['code_approved']}")
    st.sidebar.write(f"Chat Manager: {'Active' if st.session_state.get('chat_manager') else 'None'}")
    
    # File upload
    uploaded_file = st.file_uploader("Upload Requirements File", type=["txt"])
    
    if uploaded_file is not None:
        # Create input directory if it doesn't exist
        input_dir = os.path.join(project_root, "input")
        os.makedirs(input_dir, exist_ok=True)
        
        # Generate timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"upload_{timestamp}.txt"
        file_path = os.path.join(input_dir, new_filename)
        
        # Save uploaded file with new name
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Store file path in session state
        st.session_state["uploaded_file_path"] = file_path
        st.success(f"File uploaded and saved as: {new_filename}")
        
        # Log the actual file path
        logger.info(f"Saved uploaded file to: {file_path}")
    
    # Process Requirements Button
    if st.button("Process Requirements") and st.session_state["uploaded_file_path"]:
        if st.session_state["workflow_status"] == "initial":
            st.info("Processing requirements...")
            try:
                # Log the file being processed
                logger.info(f"Processing file: {st.session_state['uploaded_file_path']}")
                start_agent_workflow(st.session_state["uploaded_file_path"])
                st.rerun()  # Rerun to update UI
            except Exception as e:
                st.error(f"Error starting workflow: {str(e)}")
    
    # Display stories if generated
    if st.session_state["workflow_status"] == "stories_generated":
        stories_file = st.session_state.get("stories_file")
        if stories_file:
            stories_path = os.path.join(project_root, "stories", stories_file)
            if os.path.exists(stories_path):
                st.subheader("Generated Stories")
                with open(stories_path, 'r') as f:
                    stories = json.load(f)
                    st.json(stories)
                
                # Show the actual stories file path
                st.sidebar.write(f"Current Stories File: {stories_file}")
                
                # Approve Stories Button
                if not st.session_state["stories_approved"]:
                    if st.button("Approve Stories", key="approve_stories"):
                        # Set approval state
                        st.session_state["stories_approved"] = True
                        st.session_state["workflow_status"] = "stories_approved"
                        st.success("Stories approved! Creating Jira tickets...")
                        
                        # Get chat manager and continue conversation
                        chat_manager = st.session_state.get("chat_manager")
                        if chat_manager:
                            try:
                                user_agent.initiate_chat(
                                    chat_manager,
                                    message="Stories approved. Please proceed with creating Jira tickets."
                                )
                                st.rerun()  # Rerun to update UI
                            except Exception as e:
                                st.error(f"Error updating chat: {str(e)}")
                        else:
                            st.error("Chat manager not active. Please restart the workflow.")
    
    # Display generated code
    if st.session_state["workflow_status"] == "code_generated":
        program_file = st.session_state.get("code_file")
        if program_file and os.path.exists(program_file):
            st.subheader("Generated Program")
            with open(program_file, 'r') as f:
                code = f.read()
                st.code(code, language="python")
            
            # Approve Code Button
            if not st.session_state["code_approved"]:
                if st.button("Approve Code", key="approve_code"):
                    # Set approval state
                    st.session_state["code_approved"] = True
                    st.session_state["workflow_status"] = "code_approved"
                    st.success("Code approved! Workflow completed.")
                    
                    # Get chat manager and end conversation
                    chat_manager = st.session_state.get("chat_manager")
                    if chat_manager:
                        try:
                            user_agent.initiate_chat(
                                chat_manager,
                                message="Code approved. Workflow completed."
                            )
                            st.rerun()  # Rerun to update UI
                        except Exception as e:
                            st.error(f"Error updating chat: {str(e)}")
                    else:
                        st.error("Chat manager not active. Please restart the workflow.")

if __name__ == "__main__":
    main()
