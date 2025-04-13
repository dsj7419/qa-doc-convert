"""
Log panel component.
"""
import logging
import tkinter as tk
from tkinter import scrolledtext, ttk

from utils.theme import AppTheme

logger = logging.getLogger(__name__)

class LogPanel(ttk.Frame):
    """Panel for displaying log messages."""
    
    def __init__(self, parent):
        """
        Initialize the log panel.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent, style='TFrame')
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI elements."""
        # Log header
        header_frame = ttk.Frame(self, style='Header.TFrame')
        header_frame.pack(fill=tk.X)
        
        header_label = ttk.Label(
            header_frame,
            text="Application Log",
            style='Header.TLabel',
            font=AppTheme.FONTS['title'],
            foreground=AppTheme.COLORS['header_fg'],
            padding=(10, 5)
        )
        header_label.pack(anchor="w", fill=tk.X)
        
        # Container frame for log with border
        log_container = ttk.Frame(self, style='TFrame')
        log_container.pack(fill=tk.X, padx=5, pady=5)
        
        # Log text widget - reduced height
        self.log_text = scrolledtext.ScrolledText(
            log_container,
            height=5,
            font=AppTheme.FONTS['log'],
            bg=AppTheme.COLORS['input_bg'],
            fg=AppTheme.COLORS['text'],
            relief=tk.SUNKEN,
            bd=1,
            wrap=tk.WORD,
            state=tk.DISABLED,
            padx=8,
            pady=8,
            highlightthickness=1,
            highlightbackground=AppTheme.COLORS['list_border'],
            highlightcolor=AppTheme.COLORS['accent']
        )
        self.log_text.pack(fill=tk.X)
        
        # Button container
        button_container = ttk.Frame(self, style='TFrame')
        button_container.pack(fill=tk.X, padx=5, pady=(5, 0))
        
        # Clear button
        clear_btn = ttk.Button(
            button_container,
            text="Clear Log",
            command=self._clear_log,
            style='TButton',
            width=10
        )
        clear_btn.pack(side=tk.RIGHT, pady=(5, 0))
        
        # Configure log message tags
        self._configure_tags()
    
    def _configure_tags(self):
        """Configure text tags for different log levels."""
        self.log_text.tag_configure("INFO", foreground=AppTheme.COLORS['text'])
        self.log_text.tag_configure("WARNING", foreground=AppTheme.COLORS['warning'])
        self.log_text.tag_configure("ERROR", foreground=AppTheme.COLORS['danger'])
    
    def log_message(self, message, level="INFO"):
        """
        Add a message to the log.
        
        Args:
            message: Message to log
            level: Log level (INFO, WARNING, ERROR)
        """
        # Log to application logger
        if level == "ERROR":
            logger.error(message)
        elif level == "WARNING":
            logger.warning(message)
        else:
            logger.info(message)
        
        # Update UI log
        self.log_text.config(state=tk.NORMAL)
        
        # Insert message with timestamp and tag
        self.log_text.insert(tk.END, f"{level}: {message}\n", level)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # Keep UI responsive
        self.update_idletasks()
    
    def _clear_log(self):
        """Clear the log text widget."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)