#!/usr/bin/env python3
"""
QA Verifier - Professional Edition
Main application entry point.
"""
import logging
import os
import sys
import tkinter as tk

from ui.main_window import MainWindow
from utils.logging_setup import setup_logging
from utils.theme import AppTheme

def main():
    """Main application entry point."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
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
        
        # Initialize the application
        app = MainWindow(root)
        
        # Start the application
        root.mainloop()
        logger.info("Application closed normally")
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()