
from autogen import GroupChat, GroupChatManager
from src.agents.ba_agent import ba_agent
from src.agents.user_agent import user_agent
from src.agents.jira_agent import jira_agent
from src.config.settings import LLM_CONFIG
from transitions import Machine
import logging
import time
import json
import re
import streamlit as st

# Configure logging
logger = logging.getLogger(__name__)

# Define states as strings
STATES = [
    'initial',
    'processing_requirements',
    'displaying_stories',
    'waiting_approval',
    'creating_tickets',
    'completed',
    'error'
]

class WorkflowManager:
    """Manages workflow state using transitions library."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.stories_json = None
        self.error_message = None
        self.last_message = None
        self.current_speaker = None
        self.current_message = None
        self.allowed_transitions = {
            ba_agent: [user_agent],
            user_agent: [jira_agent, ba_agent],
            jira_agent: []
        }
        
        # Initialize state machine
        self.machine = Machine(
            model=self,
            states=STATES,
            initial='initial',
            transitions=[
                {'trigger': 'start_processing', 'source': 'initial', 'dest': 'processing_requirements'},
                {'trigger': 'show_stories', 'source': 'processing_requirements', 'dest': 'displaying_stories'},
                {'trigger': 'wait_approval', 'source': 'displaying_stories', 'dest': 'waiting_approval'},
                {'trigger': 'create_tickets', 'source': 'waiting_approval', 'dest': 'creating_tickets'},
                {'trigger': 'complete', 'source': 'creating_tickets', 'dest': 'completed'},
                {'trigger': 'error', 'source': '*', 'dest': 'error'},
                {'trigger': 'retry', 'source': ['error', 'waiting_approval'], 'dest': 'processing_requirements'}
            ],
            after_state_change='_on_state_change'
        )
        
        # Map states to agents
        self.state_to_agent = {
            'processing_requirements': ba_agent,
            'displaying_stories': user_agent,
            'waiting_approval': user_agent,
            'creating_tickets': jira_agent
        }
    
    def _on_state_change(self):
        """Callback after state change."""
        logger.info(f"State changed to: {self.state}")
    
    def get_current_agent(self):
        """Get the agent for the current state."""
        agent = self.state_to_agent.get(self.state)
        logger.info(f"Current state: {self.state}, Selected agent: {agent.name if agent else 'None'}")
        return agent
    
    def update_state(self, message: str, sender_name: str) -> None:
        """Update state based on message content and sender."""
        self.current_speaker = sender_name
        self.current_message = message
        
        print("\n=== WorkflowManager State in update_state ===")
        print(self)
        print("===========================\n")
        try:
            logger.info(f"Processing message in state '{self.state}' from {sender_name}: {message[:100]}...")
            self.last_message = message
            
            if self.state == 'processing_requirements' and sender_name == 'BA_Agent':
                json_match = re.search(r'\[\s*\{.*\}\s*\]', message, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    if self._is_valid_json_stories(json_str):
                        self.stories_json = json_str
                        logger.info(f"Valid stories JSON received, transitioning to displaying_stories")
                        st.session_state["stories_json"] = json_str  # Sync with Streamlit
                        self.show_stories()
                        return
                elif "error" in message.lower():
                    self.error_message = message
                    logger.error(f"Error in BA_Agent response: {message}")
                    self.error()
                
            elif self.state == 'displaying_stories' and sender_name == 'User_Agent':
                if "Stories displayed on UI" in message:
                    logger.info("Stories displayed, transitioning to waiting_approval")
                    self.wait_approval()
                
            elif self.state == 'waiting_approval' and sender_name == 'User_Agent':
                if message.startswith("Create these Jira stories:"):
                    logger.info("Approval received, transitioning to creating_tickets")
                    self.create_tickets()
                elif "revise" in message.lower():
                    logger.info("Revision requested, transitioning back to processing_requirements")
                    self.retry()
                else:
                    logger.debug("Waiting for approval, no transition")
                
            elif self.state == 'creating_tickets' and sender_name == 'Jira_Agent':
                json_match = re.search(r'\[\s*".*"\s*\]', message, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    if self._is_valid_issue_keys(json_str):
                        logger.info("Valid issue keys received, completing workflow")
                        self.complete()
                        return
                elif "error" in message.lower():
                    self.error_message = "Invalid issue keys"
                    logger.error(f"Error in Jira_Agent response: {message}")
                    self.error()
                
        except Exception as e:
            logger.error(f"Error in update_state: {str(e)}", exc_info=True)
            self.error_message = str(e)
            self.error()
    
    def _is_valid_json_stories(self, message: str) -> bool:
        try:
            stories = json.loads(message)
            return isinstance(stories, list)
        except json.JSONDecodeError:
            return False
    
    def _is_valid_issue_keys(self, message: str) -> bool:
        try:
            keys = json.loads(message)
            return isinstance(keys, list)
        except json.JSONDecodeError:
            return False
    
    def get_next_speaker_info(self):
        """Get detailed information about the next speaker and allowed transitions."""
        current_agent = self.get_current_agent()
        if not current_agent:
            return "No next speaker (terminal state)"
        
        allowed_next = self.allowed_transitions.get(current_agent, [])
        allowed_names = [agent.name for agent in allowed_next]
        
        return f"""
Next Speaker: {current_agent.name}
Allowed Transitions: {allowed_names}
State-based Agent: {self.state_to_agent.get(self.state, 'None').name}
"""
    
    def __str__(self):
        """Return a string representation of the WorkflowManager's state."""
        current_msg = self.current_message
        if current_msg and len(current_msg) > 100:
            current_msg = current_msg[:100] + "..."
        
        return f"""
WorkflowManager State:
----------------------
Current State: {self.state}
Current Speaker: {self.current_speaker}
Current Message: {current_msg}
{self.get_next_speaker_info()}
File Path: {self.file_path}
Stories JSON: {self.stories_json[:100] + '...' if self.stories_json and len(self.stories_json) > 100 else self.stories_json}
Error Message: {self.error_message}
Last Message: {self.last_message[:100] + '...' if self.last_message and len(self.last_message) > 100 else self.last_message}
Available States: {STATES}
State to Agent Mapping: {list(self.state_to_agent.keys())}
"""

def select_next_speaker(last_speaker, groupchat):
    """Select the next speaker based on workflow state."""
    workflow_manager = groupchat.workflow_manager
    print("\n=== WorkflowManager State in select_next_speaker ===")
    print(workflow_manager)
    print("===========================\n")
    
    if workflow_manager.state in ['completed', 'error']:
        logger.info(f"Workflow reached terminal state: {workflow_manager.state}")
        return None
    
    if workflow_manager.state in ['displaying_stories', 'waiting_approval']:
        logger.info("Forcing User_Agent for displaying_stories/waiting_approval state")
        return user_agent
    
    next_agent = workflow_manager.get_current_agent()
    if next_agent:
        logger.info(f"Selected next speaker: {next_agent.name} (state: {workflow_manager.state})")
    return next_agent

def start_agent_workflow(file_path: str) -> None:
    """Start the agent workflow to process requirements and create Jira stories."""
    logger.info(f"Starting agent workflow for file: {file_path}")
    max_attempts = 3
    attempt = 1
    
    while attempt <= max_attempts:
        try:
            # Initialize workflow manager
            workflow_manager = WorkflowManager(file_path)
            workflow_manager.start_processing()
            
            # Create group chat
            groupchat = GroupChat(
                agents=[ba_agent, user_agent, jira_agent],
                messages=[],
                max_round=100,
                speaker_selection_method=select_next_speaker,
                allowed_or_disallowed_speaker_transitions=workflow_manager.allowed_transitions,
                speaker_transitions_type='allowed',
                enable_clear_history=True
            )
            
            groupchat.workflow_manager = workflow_manager
            
            # Create group chat manager
            manager = GroupChatManager(
                groupchat=groupchat,
                llm_config=LLM_CONFIG
            )
            
            # Store manager in session state
            st.session_state["chat_manager"] = manager
            
            def message_handler(recipient, messages, sender, config):
                logger.info(f"\n=== Message Handler Called ===")
                logger.info(f"Sender: {sender.name}")
                logger.info(f"Recipient: {recipient.name if recipient else 'None'}")
                logger.debug(f"Full messages: {messages}")
                
                workflow_manager = groupchat.workflow_manager
                current_speaker = sender.name
                
                if not messages or messages[-1] is None:
                    logger.warning(f"Empty or None message received from {current_speaker}")
                    return None, None
                
                last_message = messages[-1]
                current_message = ""
                
                if isinstance(last_message, dict):
                    if 'content' in last_message and last_message['content']:
                        current_message = last_message['content']
                        logger.info(f"Message: {current_message[:100]}...")
                    
                    if 'tool_calls' in last_message and last_message['tool_calls']:
                        tool_call = last_message['tool_calls'][0]
                        logger.info(f"Tool call detected: {tool_call.get('function', {}).get('name', 'Unknown')}")
                        if 'tool_response' in last_message and last_message['tool_response']:
                            current_message = last_message['tool_response']
                            logger.info(f"Tool response: {current_message[:100]}...")
                        else:
                            logger.debug("Waiting for tool response")
                            return None, None
                
                if "Error: Function" in current_message:
                    logger.error(f"Tool call failed: {current_message}")
                    workflow_manager.error_message = current_message
                    workflow_manager.error()
                    return None, None
                
                if not current_message:
                    logger.debug(f"No valid content in message from {current_speaker}, continuing")
                    return None, None
                
                print("\n=== WorkflowManager State in message_handler ===")
                print(workflow_manager)
                print("===========================\n")
                
                workflow_manager.update_state(current_message, current_speaker)
                
                if workflow_manager.state in ['completed', 'error']:
                    logger.info(f"Workflow terminated in state: {workflow_manager.state}")
                    return None, None
                
                next_agent = workflow_manager.get_current_agent()
                if not next_agent:
                    logger.error(f"No agent mapped for state {workflow_manager.state}")
                    return None, None
                
                allowed_next = workflow_manager.allowed_transitions.get(sender, [])
                if next_agent not in allowed_next and workflow_manager.state != 'creating_tickets':
                    logger.warning(f"Invalid transition from {current_speaker} to {next_agent.name}")
                    return None, None
                
                logger.info(f"Transitioning from {current_speaker} to {next_agent.name}")
                return next_agent, current_message
            
            manager.register_reply(
                [ba_agent, user_agent, jira_agent],
                reply_func=message_handler
            )
            
            # Start conversation
            ba_agent.initiate_chat(
                manager,
                message=f"""Call the process_requirements_wrapper function with file_path='{file_path}' to read the requirements and generate a JSON list of Jira stories. Return the JSON list directly (e.g., [{{"summary": "User login", "description": "Requirement: User login"}}]). If the file is empty or invalid, return []."""
            )
            
            logger.info("Agent workflow completed successfully")
            return
            
        except Exception as e:
            if "rate limit" in str(e).lower() or "quota" in str(e).lower():
                logger.warning(f"Rate limit exceeded, attempt {attempt}/{max_attempts}. Retrying in 60 seconds.")
                time.sleep(60)
                attempt += 1
            else:
                logger.error(f"Error in agent workflow: {str(e)}", exc_info=True)
                raise
    
    logger.error("Max retry attempts reached for rate limit error")
    raise Exception("API quota limit exceeded after multiple retries")
