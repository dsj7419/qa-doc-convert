"""
This module handles PyInstaller-specific temporary directory configuration 
for Hugging Face Transformers and other ML libraries.
"""
import os
import sys
import logging
import tempfile
import shutil
import atexit
from pathlib import Path

logger = logging.getLogger(__name__)

def is_running_as_bundle():
    """
    Determine if the application is running as a PyInstaller bundle.
    
    Returns:
        bool: True if running as a PyInstaller bundle
    """
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

def setup_transformer_temp_dirs():
    """
    Configure proper temporary directories for transformers when running as PyInstaller bundle.
    
    Returns:
        str or None: Path to persistent temp directory that should be cleaned up on exit,
                    or None if not running as a bundle
    """
    # Skip if not running as PyInstaller bundle
    if not is_running_as_bundle():
        logger.info("Not running as PyInstaller bundle, no special temp handling needed")
        return None
        
    logger.info("Running as PyInstaller bundle, setting up transformer-compatible temp directories")
    
    try:
        # Create a new temporary directory that will persist through the application run
        persistent_temp_dir = tempfile.mkdtemp(prefix="qa_verifier_")
        logger.info(f"Created persistent temp directory: {persistent_temp_dir}")
        
        # Create subdirectories for different cache types
        cache_dirs = {
            "TRANSFORMERS_CACHE": os.path.join(persistent_temp_dir, "transformers_cache"),
            "HF_HOME": os.path.join(persistent_temp_dir, "hf_home"),
            "TORCH_HOME": os.path.join(persistent_temp_dir, "torch_home"),
            "XDG_CACHE_HOME": os.path.join(persistent_temp_dir, "xdg_cache"),
        }
        
        # Create all cache directories
        for name, path in cache_dirs.items():
            os.makedirs(path, exist_ok=True)
            os.environ[name] = path
            logger.info(f"Set {name}={path}")
        
        # Disable warnings and use less aggressive file locking
        os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
        os.environ["HF_HUB_DISABLE_EXPERIMENTAL_WARNING"] = "1"
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        
        # Test write permissions in all cache directories
        for name, path in cache_dirs.items():
            try:
                test_file = os.path.join(path, "test_write.tmp")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                logger.info(f"Successfully verified {name} directory is writable")
            except Exception as e:
                logger.error(f"Error verifying {name} directory: {e}")
        
        # Register cleanup function to run on exit
        atexit.register(cleanup_transformer_temp_dirs, persistent_temp_dir)
        
        return persistent_temp_dir
    
    except Exception as e:
        logger.error(f"Error setting up transformer temp directories: {e}")
        return None

def cleanup_transformer_temp_dirs(temp_dir):
    """
    Clean up the temporary directories created for transformers.
    Should be called when application exits.
    
    Args:
        temp_dir: Path to the temporary directory to clean up
    """
    if temp_dir and os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir)
            logger.info(f"Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            logger.error(f"Error cleaning up temporary directory: {e}")