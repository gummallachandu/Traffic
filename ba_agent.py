
from autogen import ConversableAgent
from src.config.settings import LLM_CONFIG
from src.tools.file_read_tool import read_file
import logging
import json

logger = logging.getLogger(__name__)

def process_requirements_wrapper(file_path: str) -> str:
    logger.info(f"Processing requirements file: {file_path}")
    try:
        content = read_file(file_path)
        if not content:
            logger.warning(f"Empty or invalid file: {file_path}")
            return json.dumps([])
        
        stories = []
        for line in content.split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                stories.append({
                    "summary": line,
                    "description": f"Requirement: {line}"
                })
        
        return json.dumps(stories)
    except Exception as e:
        logger.error(f"Error processing requirements: {str(e)}")
        return json.dumps({"error": str(e)})

ba_agent = ConversableAgent(
    name="BA_Agent",
    system_message="""You are a Business Analyst Agent (BA_Agent). Your role is to:
    1. Read requirements from a file using process_requirements_wrapper
    2. Generate a JSON list of Jira stories
    3. Send the JSON list to User_Agent for approval
    4. Log all actions and errors
    
    Example output: [{"summary": "User login", "description": "Requirement: User login"}]""",
    llm_config=LLM_CONFIG,
    human_input_mode="NEVER",
    max_consecutive_auto_reply=3,
    code_execution_config=False
)

@ba_agent.register_for_execution()
@ba_agent.register_for_llm(name="process_requirements_wrapper", description="Process requirements file and generate Jira stories.")
def process_requirements_wrapper_func(file_path: str) -> str:
    return process_requirements_wrapper(file_path)
