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
        self.allowed_transitions = {  # Add allowed transitions
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
        # Update current speaker and message
        self.current_speaker = sender_name
        self.current_message = message
        
        print("\n=== WorkflowManager State in update_state===")
        print(self)  # This will call __str__
        print("===========================\n")
        try:
            # Log current state and message with proper state display
            logger.info(f"Processing message in state '{self.state}' from {sender_name}: {message[:100]}...")
            self.last_message = message
            
            if self.state == 'processing_requirements' and sender_name == 'BA_Agent':
                # Look for JSON in tool response or direct JSON
                json_match = re.search(r'\[\s*\{.*\}\s*\]', message, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    if self._is_valid_json_stories(json_str):
                        self.stories_json = json_str
                        logger.info(f"Valid stories JSON received from BA Agent in state '{self.state}'")
                        return
                elif "error" in message.lower():
                    self.error_message = message
                    logger.error(f"Error in BA_Agent response in state '{self.state}': {message}")
                    self.error()
                
            elif self.state == 'waiting_approval' and sender_name == 'User_Agent':
                if message.startswith("Create these Jira stories:"):
                    logger.info(f"Approval received in state '{self.state}', transitioning to creating_tickets")
                    self.create_tickets()
                elif "revise" in message.lower():
                    logger.info(f"Revision requested in state '{self.state}', transitioning back to processing_requirements")
                    self.retry()
                else:
                    logger.debug(f"Waiting for approval in state '{self.state}', no transition")
                
            elif self.state == 'creating_tickets' and sender_name == 'Jira_Agent':
                json_match = re.search(r'\[\s*".*"\s*\]', message, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    if self._is_valid_issue_keys(json_str):
                        logger.info(f"Valid issue keys received in state '{self.state}', completing workflow")
                        self.complete()
                        return
                elif "error" in message.lower():
                    self.error_message = "Invalid issue keys"
                    logger.error(f"Error in Jira_Agent response in state '{self.state}': {message}")
                    self.error()
                
        except Exception as e:
            logger.error(f"Error in update_state (current state: '{self.state}'): {str(e)}", exc_info=True)
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
            
        # Get allowed transitions for current agent
        allowed_next = self.allowed_transitions.get(current_agent, [])
        allowed_names = [agent.name for agent in allowed_next]
        
        # Special case for displaying_stories state
        if self.state == 'displaying_stories':
            return f"User_Agent (forced transition from {self.current_speaker})"
            
        return f"""
Next Speaker: {current_agent.name}
Allowed Transitions: {allowed_names}
State-based Agent: {self.state_to_agent.get(self.state, 'None').name}
"""

    def __str__(self):
        """Return a string representation of the WorkflowManager's state."""
        # Format current message for display
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
    print("\n=== WorkflowManager State in Select NExt speaker===")
    print(workflow_manager)  # This will call __str__
    print("===========================\n")
    
    # Terminal states: stop the workflow
    if workflow_manager.state in ['completed', 'error']:
        return None
    
    # Handoff: if we're displaying stories, User_Agent should speak
    if workflow_manager.state == 'displaying_stories':
        return user_agent
    
    # Normal state-to-agent mapping
    return workflow_manager.get_current_agent()


def start_agent_workflow(file_path: str) -> None:
    """Start the agent workflow to process requirements and create Jira stories."""
    logger.info(f"Starting agent workflow for file: {file_path}")
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
        
        # Create group chat manager with message handler
        def create_manager():
            manager = GroupChatManager(
                groupchat=groupchat,
                llm_config=LLM_CONFIG
            )
            
            def message_handler(recipient, messages, sender, config):
                """Handle messages and control workflow transitions."""
                logger.info(f"\n=== Message Handler Called ===")
                logger.info(f"Sender: {sender.name}")
                logger.info(f"Recipient: {recipient.name if recipient else 'None'}")
                logger.info(f"Message count: {len(messages)}")
                if messages:
                    logger.info(f"Latest message: {messages[-1].get('content', '')[:100]}...")
                
                workflow_manager = groupchat.workflow_manager
                current_message = messages[-1].get('content', '') if messages else ''
                current_speaker = sender.name
                
                # Update current speaker and message in workflow manager
                workflow_manager.current_speaker = current_speaker
                workflow_manager.current_message = current_message
                
                print("\n=== WorkflowManager State in Message Handler===")
                print(workflow_manager)
                print("===========================\n")
                
                # Special handling for BA Agent's story generation message
                if (current_speaker == 'BA_Agent' and 
                    "The Jira stories have been created" in current_message and 
                    "Here are the generated stories:" in current_message):
                    logger.info("BA Agent generated stories, transitioning to User Agent")
                    workflow_manager.show_stories()  # Transition to displaying_stories state
                    return user_agent, None
                
                # Update state based on message and sender
                workflow_manager.update_state(current_message, current_speaker)
                
                # Handle terminal states
                if workflow_manager.state in ['completed', 'error']:
                    return None, None
                
                # If state just transitioned to displaying_stories, trigger User_Agent
                if workflow_manager.state == 'displaying_stories':
                    if current_speaker == 'BA_Agent':
                        logger.info("Triggering User_Agent to display stories.")
                        return user_agent, None
                
                # Default: let the speaker selection function decide
                return None, None
            
            # Register message handler for each agent individually
            for agent in [ba_agent, user_agent, jira_agent]:
                agent.register_reply(
                    [agent],  # List of agents that can trigger this handler
                    message_handler
                )
                logger.info(f"Registered message handler for {agent.name}")
            
            return manager
        
        # Create manager with registered handlers
        manager = create_manager()
        
        # Start conversation with BA Agent
        ba_agent.initiate_chat(
            manager,
            message=f"""Call the process_requirements_wrapper function with file_path='{file_path}' to read the requirements and generate a JSON list of Jira stories. Return the JSON list directly (e.g., [{{"summary": "User login", "description": "Requirement: User login"}}]). If the file is empty or invalid, return []."""
        )
        
        # Wait for workflow to complete
        while workflow_manager.state not in ['completed', 'error']:
            time.sleep(1)  # Prevent busy waiting
        
        if workflow_manager.state == 'error':
            raise Exception(f"Workflow failed: {workflow_manager.error_message}")
        
        logger.info("Agent workflow completed successfully")
        return
        
    except Exception as e:
        logger.error(f"Error in agent workflow: {str(e)}", exc_info=True)
        raise

    
