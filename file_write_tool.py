import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

def write_file(file_path: str, content: str) -> bool:
    """Write content to a file.
    
    Args:
        file_path: Path to the file to write
        content: Content to write to the file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Write content to file
        with open(file_path, 'w') as f:
            f.write(content)
            
        logger.info(f"Successfully wrote to file: {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error writing to file {file_path}: {str(e)}")
        return False 