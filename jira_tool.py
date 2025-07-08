import logging
from typing import Dict
from .api_connector import create_jira_story_in_api

# Configure logging
logger = logging.getLogger(__name__)

def create_jira_story(input_dict: Dict) -> str:
    """
    Create a Jira story by calling the API connector.
    
    Args:
        input_dict (Dict): Dictionary containing story details like summary and description.
        
    Returns:
        str: The issue key of the created Jira story.
    """
    logger.info(f"Tool: Received request to create Jira story with data: {input_dict}")
    try:
        issue_key = create_jira_story_in_api(input_dict)
        logger.info(f"Tool: Successfully created Jira story: {issue_key}")
        return issue_key
    except Exception as e:
        logger.error(f"Tool: Error creating Jira story: {str(e)}")
        # Re-raise the exception to be handled by the agent
        raise