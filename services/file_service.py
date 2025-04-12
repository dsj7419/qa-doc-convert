"""
File service for handling file operations.
"""
import logging
import os
import platform
import subprocess
from tkinter import filedialog
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class FileService:
    """Service for handling file operations."""
    
    @staticmethod
    def select_docx_file() -> Optional[str]:
        """
        Open file dialog to select a DOCX file.
        
        Returns:
            str: Selected file path or None if cancelled
        """
        path = filedialog.askopenfilename(
            title="Select DOCX File",
            filetypes=[("Word Documents", "*.docx")]
        )
        
        if path:
            logger.info(f"Selected file: {path}")
            return path
        
        logger.info("File selection cancelled.")
        return None
    
    @staticmethod
    def get_save_csv_path(original_file_path: str) -> Optional[str]:
        """
        Get save path for CSV export.
        
        Args:
            original_file_path: Original file path
            
        Returns:
            str: Save path or None if cancelled
        """
        if not original_file_path:
            return None
            
        # Generate default filename
        output_csv_path = os.path.splitext(original_file_path)[0] + "_verified.csv"
        
        save_path = filedialog.asksaveasfilename(
            title="Save Verified CSV",
            initialfile=os.path.basename(output_csv_path),
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        
        if save_path:
            logger.info(f"Selected save path: {save_path}")
            return save_path
            
        logger.info("CSV save cancelled by user.")
        return None
    
    @staticmethod
    def open_file_externally(file_path: str) -> Tuple[bool, str]:
        """
        Open a file using the system's default application.
        
        Args:
            file_path: Path to the file to open
            
        Returns:
            Tuple containing success flag and error message if any
        """
        try:
            if platform.system() == 'Windows':
                os.startfile(file_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(['open', file_path])
            else:  # Linux and others
                subprocess.call(['xdg-open', file_path])
                
            logger.info(f"Opened file externally: {file_path}")
            return True, ""
        except Exception as e:
            error_msg = f"Could not open file: {str(e)}"
            logger.error(error_msg)
            return False, error_msg