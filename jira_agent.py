from autogen import ConversableAgent
from src.config.settings import LLM_CONFIG
import logging
import json
from pathlib import Path
import os
from src.agents.executor_agent import create_jira_stories

logger = logging.getLogger(__name__)

# Define the llm_config with the tool schema for the Jira Agent
llm_config_with_tool = LLM_CONFIG.copy()
llm_config_with_tool["tools"] = [
    {
        "type": "function",
        "function": {
            "name": "create_jira_stories",
            "description": "Create Jira stories from a JSON file containing user stories.",
            "parameters": {
                "type": "object",
                "properties": {
                    "stories_file_path": {
                        "type": "string",
                        "description": "The absolute path to the JSON file containing the stories."
                    }
                },
                "required": ["stories_file_path"]
            }
        }
    }
]

jira_agent = ConversableAgent(
    name="Jira_Agent",
    system_message="""You are a Jira agent responsible for creating and managing Jira tickets.
    When given a file path to stories, call the create_jira_stories tool to create the tickets.
    Do not ask for confirmation. Call the tool directly with the provided file path.""",
    llm_config=llm_config_with_tool,
    human_input_mode="NEVER",
    max_consecutive_auto_reply=1,
    code_execution_config=False,
    function_map={"create_jira_stories": create_jira_stories}  # Register the function from executor agent
)


