"""
Status bar component.
"""
import tkinter as tk
from tkinter import ttk

from utils.theme import AppTheme

class StatusBar(ttk.Frame):
    """Status bar displaying application status."""
    
    def __init__(self, parent):
        """
        Initialize the status bar.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent, style='TFrame')
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI elements."""
        # Create container with border
        status_container = ttk.Frame(self, style='Section.TFrame')
        status_container.pack(fill=tk.X, padx=5, expand=True)
        
        # Status icon
        status_icon = ttk.Label(
            status_container,
            text="ℹ",  # Unicode info symbol
            font=("Segoe UI", 10, "bold"),
            foreground=AppTheme.COLORS['accent'],
            background=AppTheme.COLORS['section_header_bg']
        )
        status_icon.pack(side=tk.LEFT, padx=(5, 10))
        
        # Status text variable
        self.status_var = tk.StringVar(value="Load a DOCX file to begin.")
        
        # Status label with improved styling
        self.status_label = ttk.Label(
            status_container,
            textvariable=self.status_var,
            font=AppTheme.FONTS['normal'],
            foreground=AppTheme.COLORS['text'],
            background=AppTheme.COLORS['section_header_bg'],
            anchor=tk.W,
            padding=(0, 5)
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def update_status(self, message):
        """
        Update the status message.
        
        Args:
            message: Status message to display
        """
        self.status_var.set(message)
        self.update_idletasks()  # Force update5