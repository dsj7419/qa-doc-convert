"""
Log panel component with fixed button text color.
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
        # Log header with better contrast
        header_container = ttk.Frame(self, style='TFrame')
        header_container.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Make the container visually distinct - use tk.Frame for direct color control
        header_bg = tk.Frame(
            header_container,
            bg=AppTheme.COLORS['action_button_bg'],
            padx=5,
            pady=3
        )
        header_bg.pack(fill=tk.X, expand=True)
        
        # Log icon
        log_icon = tk.Label(
            header_bg,
            text="📋",  # Clipboard emoji
            font=("Segoe UI", 12),
            fg="#ffffff",  # White for contrast
            bg=AppTheme.COLORS['action_button_bg']
        )
        log_icon.pack(side=tk.LEFT, padx=(0, 8))
        
        header_label = tk.Label(
            header_bg,
            text="Log:",
            font=AppTheme.FONTS['bold'],
            fg="#ffffff",  # White for contrast
            bg=AppTheme.COLORS['action_button_bg']
        )
        header_label.pack(side=tk.LEFT)
        
        # Container frame for log with border
        log_container = ttk.Frame(self, style='TFrame')
        log_container.pack(fill=tk.X, padx=5, pady=0)
        
        # Log text widget - reduced height
        self.log_text = scrolledtext.ScrolledText(
            log_container,
            height=4,  # Reduced from 6
            font=AppTheme.FONTS['log'],
            bg="white",
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
        
        # DIRECT APPROACH: Use plain tk.Button
        clear_btn = tk.Button(
            button_container,
            text="Clear Log",
            command=self._clear_log,
            bg=AppTheme.COLORS['action_button_bg'],
            fg="#ffffff",  # FORCE WHITE TEXT
            activebackground=AppTheme.COLORS['action_button_hover'],
            activeforeground="#ffffff",  # WHITE TEXT ON HOVER
            font=AppTheme.FONTS['normal'],
            relief="raised",
            borderwidth=1,
            width=10,
            cursor="hand2"
        )
        clear_btn.pack(side=tk.RIGHT, pady=(5, 0))
    
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
            
        # Define color based on level
        if level == "ERROR":
            tag = "error"
            color = AppTheme.COLORS['danger']
        elif level == "WARNING":
            tag = "warning"
            color = AppTheme.COLORS['warning']
        else:
            tag = "info"
            color = AppTheme.COLORS['dark']
        
        # Update UI log
        self.log_text.config(state=tk.NORMAL)
        
        # Add tags if they don't exist
        if tag not in self.log_text.tag_names():
            self.log_text.tag_configure(tag, foreground=color)
        
        # Insert message with timestamp and tag
        self.log_text.insert(tk.END, f"{level}: {message}\n", tag)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # Keep UI responsive
        self.update_idletasks()
    
    def _clear_log(self):
        """Clear the log text widget."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)