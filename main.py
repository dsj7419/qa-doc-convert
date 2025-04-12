#!/usr/bin/env python3
"""
QA Verifier - Professional Edition
Main application entry point.
"""
import logging
import os
import sys
import tkinter as tk

from models.document import Document
from presenters.main_presenter import MainPresenter
from ui.main_window import MainWindow
from utils.logging_setup import setup_logging
from utils.theme import AppTheme
from utils.config_manager import ConfigManager

def main():
    """Main application entry point."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

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