"""
Theme configuration and styling for the application.
Elegant professional color scheme with enhanced readability and visual appeal.
"""
import logging
import tkinter as tk
from tkinter import ttk
import platform

logger = logging.getLogger(__name__)

class AppTheme:
    """Manages application theming and styling."""
    
    # Refined professional color palette
    COLORS = {
        # Main colors
        'primary': "#1e3a5f",      # Rich navy blue
        'secondary': "#2d4a6d",    # Medium navy
        'accent': "#5d9cec",       # Vibrant blue - for emphasis
        'success': "#53b983",      # Soft green
        'warning': "#fcb941",      # Soft orange
        'danger': "#f06060",       # Soft red
        'light': "#f5f6fa",        # Off-white
        'dark': "#2b333e",         # Dark slate
        
        # UI element colors
        'bg': "#f0f4f8",           # Light blue-gray background
        'header_bg': "#1e3a5f",    # Rich navy header
        'header_fg': "#ffffff",    # White text for headers
        
        # Button colors
        'button_bg': "#456789",    # Default button background
        'button_fg': "#ffffff",    # Default button foreground (white)
        'button_hover': "#5d7799", # Lighter on hover
        'action_button_bg': "#2d567d", # Action button background
        'action_button_fg': "#ffffff", # Action button foreground
        'action_button_hover': "#3d6897", # Action button hover
        'exit_bg': "#c13636",      # Exit button background
        'exit_fg': "#ffffff",      # Exit button foreground
        'exit_hover': "#d84545",   # Exit button hover
        
        # List and selection colors
        'list_bg': '#ffffff',      # White
        'list_border': '#c0c2c4',  # Medium gray border
        'list_selected_bg': '#e1eeff', # Gentle blue selection
        'list_selected_fg': '#1e3a5f', # Dark text on selection
        
        # Role colors - softer and more distinct
        'role_question_bg': '#e5f0ff', # Light blue for questions 
        'role_answer_bg': '#ffffff',   # White for answers
        'role_ignore_bg': '#f0f0f0',   # Light gray for ignored
        'role_undetermined_bg': '#fff7e0', # Soft yellow for undetermined
        
        # Progress indicators
        'counter_match': '#53b983',    # Soft green
        'counter_close': '#fcb941',    # Soft orange
        'counter_far': '#f06060',      # Soft red
        
        # Additional UI element colors
        'separator': '#bdc3c7',    # Visible but subtle separators
        'progress_bg': '#e0e0e0',  # Progress bar background
        'progress_fg': '#5d9cec',  # Progress bar foreground
        'input_bg': '#ffffff',     # Input field background
        'input_border': '#a0a5aa', # Input field border
    }
    
    # Define font settings based on platform
    FONTS = {
        'normal': None,
        'bold': None,
        'title': None,
        'log': None,
        'list': None,
    }
    
    @classmethod
    def configure(cls, root):
        """
        Configure the application theme.
        
        Args:
            root: The root Tk instance
        """
        # Set up fonts based on platform
        cls._setup_fonts()
        
        # Configure ttk styles
        style = ttk.Style()
        
        # Use platform-specific theme as base
        if platform.system() == 'Windows':
            style.theme_use('vista')
        elif platform.system() == 'Darwin':  # macOS
            style.theme_use('aqua')
        else:  # Linux
            style.theme_use('clam')
        
        # Configure ttk styles
        cls._configure_ttk_styles(style)
        
        logger.info("Theme configured successfully")
    
    @classmethod
    def _setup_fonts(cls):
        """Set up fonts based on the platform."""
        if platform.system() == 'Windows':
            cls.FONTS['normal'] = ("Segoe UI", 10)
            cls.FONTS['bold'] = ("Segoe UI", 10, "bold")
            cls.FONTS['title'] = ("Segoe UI", 16, "bold")
            cls.FONTS['log'] = ("Consolas", 9)
            cls.FONTS['list'] = ("Segoe UI", 10)
        elif platform.system() == 'Darwin':  # macOS
            cls.FONTS['normal'] = ("SF Pro Text", 12)
            cls.FONTS['bold'] = ("SF Pro Text", 12, "bold")
            cls.FONTS['title'] = ("SF Pro Display", 18, "bold")
            cls.FONTS['log'] = ("Menlo", 11)
            cls.FONTS['list'] = ("SF Pro Text", 12)
        else:  # Linux
            cls.FONTS['normal'] = ("Ubuntu", 10)
            cls.FONTS['bold'] = ("Ubuntu", 10, "bold")
            cls.FONTS['title'] = ("Ubuntu", 16, "bold")
            cls.FONTS['log'] = ("Ubuntu Mono", 9)
            cls.FONTS['list'] = ("Ubuntu", 10)
    
    @classmethod
    def _configure_ttk_styles(cls, style):
        """Configure ttk widget styles for a consistent professional look."""
        # Configure TFrame
        style.configure('TFrame', background=cls.COLORS['bg'])
        style.configure('Header.TFrame', background=cls.COLORS['header_bg'])
        
        # Configure TLabel
        style.configure('TLabel', 
                        background=cls.COLORS['bg'], 
                        font=cls.FONTS['normal'])
        
        style.configure('Header.TLabel', 
                        background=cls.COLORS['header_bg'],
                        foreground=cls.COLORS['header_fg'],
                        font=cls.FONTS['title'])
        
        # Configure TButton styles
        # Default button
        style.configure('TButton', 
                        font=cls.FONTS['normal'],
                        padding=(12, 6))
        
        # Primary button (blue)
        style.configure('Primary.TButton', 
                        font=cls.FONTS['bold'])
        style.map('Primary.TButton',
                  background=[('active', cls.COLORS['button_hover']),
                              ('!disabled', cls.COLORS['button_bg'])],
                  foreground=[('!disabled', cls.COLORS['button_fg'])])
        
        # Action button (darker blue)
        style.configure('Action.TButton', 
                        font=cls.FONTS['normal'])
        style.map('Action.TButton',
                  background=[('active', cls.COLORS['action_button_hover']),
                              ('!disabled', cls.COLORS['action_button_bg'])],
                  foreground=[('!disabled', cls.COLORS['action_button_fg'])])
                  
        # Danger button (red)
        style.configure('Danger.TButton', 
                        font=cls.FONTS['normal'])
        style.map('Danger.TButton',
                  background=[('active', cls.COLORS['exit_hover']),
                              ('!disabled', cls.COLORS['exit_bg'])],
                  foreground=[('!disabled', cls.COLORS['exit_fg'])])
                  
        # Small action button
        style.configure('Small.Action.TButton',
                        font=cls.FONTS['normal'],
                        padding=(6, 3))
        style.map('Small.Action.TButton',
                  background=[('active', cls.COLORS['action_button_hover']),
                              ('!disabled', cls.COLORS['action_button_bg'])],
                  foreground=[('!disabled', cls.COLORS['action_button_fg'])])
        
        # White on blue button (for header)
        style.configure('Header.TButton',
                        font=cls.FONTS['normal'],
                        background=cls.COLORS['header_bg'],
                        foreground=cls.COLORS['header_fg'])
        style.map('Header.TButton',
                  background=[('active', cls.COLORS['button_hover']),
                              ('!disabled', cls.COLORS['button_bg'])],
                  foreground=[('!disabled', cls.COLORS['button_fg'])])
        
        # Configure TEntry
        style.configure('TEntry', 
                        fieldbackground=cls.COLORS['input_bg'],
                        font=cls.FONTS['normal'],
                        padding=5)
        style.map('TEntry',
                  fieldbackground=[('disabled', cls.COLORS['bg'])])
        
        # Configure TProgressbar
        style.configure("TProgressbar",
                        troughcolor=cls.COLORS['progress_bg'],
                        background=cls.COLORS['progress_fg'],
                        thickness=8)
        
        # Configure TSeparator
        style.configure('TSeparator',
                        background=cls.COLORS['separator'])