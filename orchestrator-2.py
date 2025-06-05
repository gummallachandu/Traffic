from autogen import GroupChat, GroupChatManager
from src.agents.ba_agent import ba_agent
from src.agents.user_agent import user_agent
from src.agents.jira_agent import jira_agent
from src.config.settings import LLM_CONFIG
import logging
import time

# Configure logging
logger = logging.getLogger(__name__)

def select_next_speaker(last_speaker, groupchat):
    """Simple speaker selection based on last speaker."""
    if last_speaker == ba_agent:
        return user_agent
    elif last_speaker == user_agent:
        if "Create these Jira stories:" in groupchat.messages[-1].get('content', ''):
            return jira_agent
        else:
            return ba_agent
    elif last_speaker == jira_agent:
        return None  # End conversation after Jira agent
    else:
        return ba_agent  # Start with BA agent

def start_agent_workflow(file_path: str) -> None:
    """Start the agent workflow with simple message flow."""
    logger.info(f"Starting agent workflow for file: {file_path}")
    try:
        # Create group chat
        groupchat = GroupChat(
            agents=[ba_agent, user_agent, jira_agent],
            messages=[],
            max_round=100,
            speaker_selection_method=select_next_speaker,
            enable_clear_history=True
        )
        
        # Create group chat manager
        manager = GroupChatManager(
            groupchat=groupchat,
            llm_config=LLM_CONFIG
        )
        
        def message_handler(recipient, messages, sender, config):
            """Simple message handler that just logs messages."""
            if messages:
                current_message = messages[-1].get('content', '')
                logger.info(f"\n=== Message from {sender.name} ===")
                logger.info(f"Message: {current_message[:100]}...")
                logger.info("=====================\n")
            return None, None
        
        # Register message handler for each agent
        for agent in [ba_agent, user_agent, jira_agent]:
            agent.register_reply(
                [agent],
                message_handler
            )
            logger.info(f"Registered message handler for {agent.name}")
        
        # Start conversation with BA Agent
        ba_agent.initiate_chat(
            manager,
            message=f"""Call the process_requirements_wrapper function with file_path='{file_path}' to read the requirements and generate a JSON list of Jira stories. Return the JSON list directly (e.g., [{{"summary": "User login", "description": "Requirement: User login"}}]). If the file is empty or invalid, return []."""
        )
        
        # Wait for conversation to complete (when Jira agent finishes)
        while True:
            if not groupchat.messages:
                time.sleep(1)
                continue
                
            last_message = groupchat.messages[-1].get('content', '')
            if groupchat.messages[-1].get('name') == 'Jira_Agent':
                if '[' in last_message and ']' in last_message:  # Jira agent returned issue keys
                    break
            time.sleep(1)
        
        logger.info("Agent workflow completed successfully")
        return
        
    except Exception as e:
        logger.error(f"Error in agent workflow: {str(e)}", exc_info=True)
        raise 