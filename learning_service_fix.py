"""
This module ensures all required directories exist and are writable
before the learning service attempts to use them.
"""
import os
import logging
import platform
import shutil
import time
from pathlib import Path

logger = logging.getLogger("learning_service_fix")

def get_user_data_dir():
    """
    Get platform-specific user data directory.
    
    Returns:
        str: Path to user data directory
    """
    app_name = "QA_Verifier"
    
    if platform.system() == "Windows":
        # Windows: Use %APPDATA% (typically C:\Users\<username>\AppData\Roaming)
        user_data_dir = os.path.join(os.environ.get("APPDATA", ""), app_name)
    elif platform.system() == "Darwin":  # macOS
        # macOS: Use ~/Library/Application Support
        user_data_dir = os.path.join(os.path.expanduser("~/Library/Application Support"), app_name)
    else:  # Linux and others
        # Linux: Use ~/.local/share
        user_data_dir = os.path.join(os.path.expanduser("~/.local/share"), app_name)
    
    return user_data_dir

def verify_directory(directory_path):
    """
    Create a directory if it doesn't exist and verify write permissions.
    
    Args:
        directory_path: Path to the directory
        
    Returns:
        bool: True if directory exists and is writable, False otherwise
    """
    try:
        # Create directory and any parent directories
        os.makedirs(directory_path, exist_ok=True)
        
        # Test write permissions
        test_file = os.path.join(directory_path, "test_write.tmp")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("test")
        os.remove(test_file)
        
        logger.info(f"Successfully verified directory: {directory_path}")
        return True
    except Exception as e:
        logger.error(f"Error creating/verifying directory {directory_path}: {e}")
        return False

def apply_fix():
    """
    Apply the fix to ensure all directories exist before training.
    
    This function should be called at application startup.
    
    Returns:
        bool: True if all directories were successfully verified
    """
    # Get user data directory
    user_data_dir = get_user_data_dir()
    
    # Create required directories
    directories = [
        user_data_dir,
        os.path.join(user_data_dir, "fine_tuned_model"),
        os.path.join(user_data_dir, "training_checkpoints"),
        os.path.join(user_data_dir, "training_logs"),
    ]
    
    # Verify all directories
    success = all(verify_directory(directory) for directory in directories)
    
    # Fix the existing checkpoint directory structure if needed
    checkpoint_dir = os.path.join(user_data_dir, "training_checkpoints")
    if os.path.exists(checkpoint_dir):
        try:
            # Make sure the directory is empty to prevent resuming from corrupt checkpoints
            for item in os.listdir(checkpoint_dir):
                item_path = os.path.join(checkpoint_dir, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            logger.info(f"Cleaned checkpoint directory: {checkpoint_dir}")
        except Exception as e:
            logger.error(f"Error cleaning checkpoint directory: {e}")
            success = False
    
    # Test writing a large file to detect disk space issues
    try:
        test_large_file = os.path.join(user_data_dir, "test_large_file.tmp")
        with open(test_large_file, 'wb') as f:
            # Write 1 MB of data to test for disk space issues
            f.write(b'0' * 1024 * 1024)
        os.remove(test_large_file)
        logger.info("Successfully verified disk space")
    except Exception as e:
        logger.error(f"Error testing disk space: {e}")
        success = False
    
    return success