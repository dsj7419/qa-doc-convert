#!/usr/bin/env python3
"""
QA Verifier - Professional Edition
Main application entry point.
"""
import io
import logging
import os
import sys
import tkinter as tk
import atexit

from models.document import Document
from presenters.main_presenter import MainPresenter
from ui.main_window import MainWindow
from utils.logging_setup import setup_logging
from utils.theme import AppTheme
from utils.config_manager import ConfigManager
from learning_service_fix import apply_fix

# Set environment for Hugging Face and Unicode issues
os.environ.update({
    "PYTHONIOENCODING": "utf-8",
    "TRANSFORMERS_VERBOSITY": "error",
    "HF_HUB_DISABLE_SYMLINKS_WARNING": "1",
    "HF_HUB_DISABLE_EXPERIMENTAL_WARNING": "1",
    "TOKENIZERS_PARALLELISM": "false",
    "HF_HUB_DOWNLOAD_TIMEOUT": "300"
})

# Patch stdout/stderr for UTF-8 if available
if sys.stdout and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Try to apply the transformers patch early
try:
    from transformers_patch import apply_transformers_patch
    apply_transformers_patch()
except ImportError:
    pass

# Import the new PyInstaller fix
try:
    from pyinstaller_transformer_fix import setup_transformer_temp_dirs, cleanup_transformer_temp_dirs
except ImportError:
    # Create stub functions if the module isn't available
    def setup_transformer_temp_dirs():
        return None
    def cleanup_transformer_temp_dirs(temp_dir):
        pass

def main():
    """Main application entry point."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    # Setup PyInstaller-specific temporary directories
    temp_dir = setup_transformer_temp_dirs()
    if temp_dir:
        logger.info(f"Set up PyInstaller transformer temp dir: {temp_dir}")
        # Register cleanup on exit
        atexit.register(cleanup_transformer_temp_dirs, temp_dir)

    # Apply the directory fix for learning service
    try:
        apply_fix()
        logger.info("Applied learning service directory fix")
    except Exception as e:
        logger.warning(f"Could not apply learning service fix: {e}")

    # Configure environment variables for Hugging Face libraries
    # These help reduce file locking and permissions issues
    os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"  # Disable parallelism to avoid deadlocks
    
    # Set a custom HTTP timeout for downloading models to avoid hanging
    os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = "300"  # 5 minutes timeout
    
    # Log current environment for debugging
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"APPDATA location: {os.environ.get('APPDATA', 'Not set')}")
    logger.info(f"HF_HOME: {os.environ.get('HF_HOME', 'Not set')}")
    logger.info(f"TRANSFORMERS_CACHE: {os.environ.get('TRANSFORMERS_CACHE', 'Not set')}")
    
    # Now proceed with normal application startup
    config_manager = ConfigManager()
    config = config_manager.get_config()
    
    try:
        # Create and start the application
        logger.info("Starting QA Verifier Professional Edition")
        
        # Create root window
        root = tk.Tk()
        
        # Set application icon (if available)
        try:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "icon.ico")
            if os.path.exists(icon_path):
                root.iconbitmap(icon_path)
        except Exception as icon_err:
            logger.warning(f"Could not load application icon: {icon_err}")
        
        # Use a nice window title with version
        root.title("QA Verifier - Professional Edition v1.0")
        
        # Set minimum window size for usability
        root.minsize(900, 650)
        
        # Center window on screen
        window_width = 1100
        window_height = 750
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        center_x = int((screen_width - window_width) / 2)
        center_y = int((screen_height - window_height) / 2)
        root.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        
        # Initialize components with dependency injection
        # Create models
        document = Document(config_manager)
        
        # Create views
        view = MainWindow(root)
        
        # Create presenters
        presenter = MainPresenter(view, document, root, config_manager)
        
        # Connect presenter to view
        view.set_presenter(presenter)
        
        # Initialize the presenter
        presenter.initialize()
        
        # Start the application
        root.mainloop()
        logger.info("Application closed normally")
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()