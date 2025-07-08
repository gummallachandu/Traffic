import logging
from typing import Union
from .api_connector import read_file_from_api, write_file_to_api

logger = logging.getLogger(__name__)

def read_file(file_path: str) -> str:
    """
    Read content from a text file by calling an API.
    
    Args:
        file_path (str): Path to the file to read
        
    Returns:
        str: Content of the file
    """
    try:
        return read_file_from_api(file_path)
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        # Return a user-friendly error message or re-raise
        return f"Error reading file: {e}"

def write_file(file_path: str, content: Union[str, bytes]) -> bool:
    """
    Write content to a file by calling an API.
    
    Args:
        file_path (str): Path to the file to write
        content (Union[str, bytes]): Content to write to the file
        
    Returns:
        bool: True if successful, False if error
    """
    try:
        # Assuming the API expects a string. If it handles bytes, this might need adjustment.
        if isinstance(content, bytes):
            content = content.decode('utf-8', errors='ignore')
        
        return write_file_to_api(file_path, content)
    except Exception as e:
        logger.error(f"Error writing to file {file_path}: {str(e)}")
        return False 