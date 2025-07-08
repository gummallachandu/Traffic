import logging
import requests
from atlassian import Jira
import os
from dotenv import load_dotenv
from typing import Dict
import json

logger = logging.getLogger(__name__)

# Load .env file for environment variables
load_dotenv()

# Get API base URL from environment variable
API_BASE_URL = os.getenv("TOOL_APP_URL")
if not API_BASE_URL:
    raise ValueError("TOOL_APP_URL environment variable is required")

def read_file_from_api(file_path: str) -> str:
    """
    Calls the API to read content from a file.
    
    Args:
        file_path (str): Path to the file to read.
        
    Returns:
        str: Content of the file.
        
    Raises:
        Exception: For API errors.
    """
    content = None
    try:
        url = f"{API_BASE_URL}/read-file"
        logger.info(f"Calling API (POST) to read file: {url} for path: {file_path}")
        # The API expects a POST request with the file path in the body
        response = requests.post(url, json={"file_path": file_path})
        response.raise_for_status()
        
        # The API returns a JSON object, we need to parse it and get the 'content' field
        response_data = response.json()
        logger.debug(f"Full API Response JSON: {response_data}")
        
        content = response_data.get("content")
        if content is None:
            raise Exception("API response did not contain a 'content' field.")

        logger.info(f"Successfully read file using API: {file_path}")
        return content
    except requests.exceptions.HTTPError as http_err:
        error_details = f"HTTP error occurred: {http_err}"
        if http_err.response:
            error_details += f" - Response Body: {http_err.response.text}"
        logger.error(f"API error reading file {file_path}: {error_details}")
        raise Exception(f"API error reading file {file_path}: {error_details}") from http_err
    except requests.exceptions.RequestException as req_err:
        logger.error(f"API request error reading file {file_path}: {req_err}")
        raise Exception(f"API request error reading file {file_path}: {req_err}") from req_err
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Error parsing API response for {file_path}: {str(e)}")
        raise Exception(f"Error parsing API response for {file_path}: {str(e)}") from e

def write_file_to_api(file_path: str, content: str) -> bool:
    """
    Calls the API to write content to a file.
    
    Args:
        file_path (str): Path to the file to write.
        content (str): Content to write to the file.
        
    Returns:
        bool: True if successful.
        
    Raises:
        Exception: For API errors.
    """
    try:
        url = f"{API_BASE_URL}/write-file/"
        logger.info(f"Calling API to write to file: {url} for path: {file_path}")
        response = requests.post(url, json={"file_path": file_path, "content": content})
        response.raise_for_status()
        
        logger.info(f"Successfully wrote to file using API: {file_path}")
        return True
    except requests.exceptions.HTTPError as http_err:
        error_details = f"HTTP error occurred: {http_err}"
        if http_err.response:
            error_details += f" - Response Body: {http_err.response.text}"
        logger.error(f"API error writing to file {file_path}: {error_details}")
        raise Exception(f"API error writing to file {file_path}: {error_details}") from http_err
    except requests.exceptions.RequestException as req_err:
        logger.error(f"API error writing to file {file_path}: {req_err}")
        raise Exception(f"API error writing to file {file_path}: {req_err}") from req_err

def create_jira_story_in_api(input_dict: Dict) -> str:
    """Create a Jira story with specified summary and description via API."""
    logger.info(f"API Connector: Received input for Jira: {input_dict}")
    try:
        jira_url = os.getenv("JIRA_INSTANCE_URL")
        jira_username = os.getenv("JIRA_USERNAME")
        jira_api_token = os.getenv("JIRA_API_TOKEN")

        if not all([jira_url, jira_username, jira_api_token]):
            missing = [v for v, k in {"JIRA_INSTANCE_URL": jira_url, "JIRA_USERNAME": jira_username, "JIRA_API_TOKEN": jira_api_token}.items() if not k]
            error_msg = f"Missing Jira environment variables: {', '.join(missing)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        jira = Jira(
            url=jira_url,
            username=jira_username,
            password=jira_api_token,
            cloud=True
        )
        logger.info(f"Jira client initialized with URL {jira_url}")

        project_key = os.getenv("JIRA_PROJECT_KEY", "SDLC")
        fields = {
            "project": {"key": project_key},
            "summary": input_dict.get("summary", "New User Story"),
            "description": input_dict.get("description", ""),
            "issuetype": {"name": "Story"}
        }

        logger.info(f"Creating Jira story with fields: {fields}")
        issue = jira.create_issue(fields=fields)
        issue_key = issue.get("key", "Unknown issue key")
        logger.info(f"Created Jira story: {issue_key}")
        return issue_key
    except Exception as e:
        logger.error(f"Error creating Jira story in API connector: {str(e)}")
        raise Exception(f"Error creating Jira story in API connector: {str(e)}") 