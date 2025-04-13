"""
Theme configuration and styling for the application.
Professional color scheme with excellent readability and visual hierarchy.
"""
import logging
import tkinter as tk
from tkinter import ttk
import platform

logger = logging.getLogger(__name__)

class AppTheme:
    """Manages application theming and styling."""
    
    # Professional color palette with proper contrast
    COLORS = {
        # Main colors - keeping navy header but changing button colors
        'primary': "#1e3a5f",       # Rich navy blue for headers
        'secondary': "#2d4a6d",     # Medium navy for secondary elements
        'accent': "#4285f4",        # Google blue
        'light': "#f8f9fa",         # Off-white background
        'dark': "#202124",          # Almost black text
        
        # UI element colors
        'bg': "#f8f9fa",            # Light background
        'text': "#202124",          # Dark text for light backgrounds
        'text_secondary': "#5f6368", # Secondary text
        'header_bg': "#1e3a5f",     # Rich navy header
        'header_fg': "#ffffff",     # White text for headers
        
        # Status/Alert colors
        'success': "#34a853",       # Google green
        'warning': "#fbbc05",       # Google yellow - ADDED THIS MISSING KEY
        'danger': "#ea4335",        # Google red
        'info': "#4285f4",          # Google blue
        
        # COMPLETELY REVISED BUTTON COLORS - Light background with dark text
        'button_bg': "#e8f0fe",         # Light blue button background
        'button_fg': "#1a73e8",         # Blue button text 
        'button_hover': "#d2e3fc",      # Slightly darker blue on hover
        'button_pressed': "#aecbfa",    # Even darker blue when pressed
        'button_disabled': "#f1f3f4",   # Light gray when disabled
        'button_disabled_fg': "#9aa0a6", # Gray text when disabled
        
        # Action button variants - Green action buttons
        'action_button_bg': "#e6f4ea",      # Light green background
        'action_button_fg': "#137333",      # Dark green text
        'action_button_hover': "#ceead6",   # Slightly darker green on hover
        'action_button_pressed': "#a8dab5", # Even darker green when pressed
        
        # Danger button variants - Red danger buttons
        'danger_button_bg': "#fce8e6",      # Light red background
        'danger_button_fg': "#c5221f",      # Dark red text
        'danger_button_hover': "#fad2cf",   # Slightly darker red on hover
        'danger_button_pressed': "#f6aea9", # Even darker red when pressed
        
        # List colors
        'list_bg': '#ffffff',              # White
        'list_fg': '#202124',              # Dark text
        'list_border': '#dadce0',          # Medium gray border
        
        # SELECTION HIGHLIGHT - High contrast with no role color conflicts
        'list_selected_bg': '#ffe082',     # Amber highlight - distinct from all roles
        'list_selected_fg': '#202124',     # Keep original text color visible
        
        # Role colors - distinct and easily distinguishable
        'role_question_bg': '#e6f4ea',     # Light green for questions
        'role_question_fg': '#137333',     # Dark green text
        'role_answer_bg': '#e8f0fe',       # Light blue for answers
        'role_answer_fg': '#1967d2',       # Dark blue text
        'role_ignore_bg': '#f1f3f4',       # Light gray for ignored
        'role_ignore_fg': '#5f6368',       # Dark gray text
        'role_undetermined_bg': '#fef7e0',  # Light yellow for undetermined
        'role_undetermined_fg': '#b06000',  # Dark amber text
        
        # Progress indicators
        'progress_bg': '#e6e6e6',         # Light gray background
        'progress_fg': '#34a853',         # Green for progress
        
        # Additional UI element colors
        'separator': '#dadce0',           # Medium gray
        'input_bg': '#ffffff',            # White background
        'input_border': '#dadce0',        # Medium gray border
        'input_border_focus': '#4285f4',  # Blue when focused
        
        # Header/section backgrounds
        'section_header_bg': '#e8eaed',   # Light gray section headers
        'section_header_fg': '#202124',   # Dark text for section headers
    }
    
    # Define font settings based on platform
    FONTS = {
        'normal': None,
        'bold': None,
        'title': None,
        'log': None,
        'list': None,
        'button': None,
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
            cls.FONTS['title'] = ("Segoe UI", 14, "bold")
            cls.FONTS['log'] = ("Consolas", 9)
            cls.FONTS['list'] = ("Segoe UI", 10)
            cls.FONTS['button'] = ("Segoe UI", 10)
        elif platform.system() == 'Darwin':  # macOS
            cls.FONTS['normal'] = ("SF Pro Text", 12)
            cls.FONTS['bold'] = ("SF Pro Text", 12, "bold")
            cls.FONTS['title'] = ("SF Pro Display", 16, "bold")
            cls.FONTS['log'] = ("Menlo", 11)
            cls.FONTS['list'] = ("SF Pro Text", 12)
            cls.FONTS['button'] = ("SF Pro Text", 12)
        else:  # Linux
            cls.FONTS['normal'] = ("Ubuntu", 10)
            cls.FONTS['bold'] = ("Ubuntu", 10, "bold")
            cls.FONTS['title'] = ("Ubuntu", 14, "bold")
            cls.FONTS['log'] = ("Ubuntu Mono", 9)
            cls.FONTS['list'] = ("Ubuntu", 10)
            cls.FONTS['button'] = ("Ubuntu", 10)
    
    @classmethod
    def _configure_ttk_styles(cls, style):
        """Configure ttk widget styles for a professional, modern look."""
        # Configure TFrame
        style.configure('TFrame', background=cls.COLORS['bg'])
        style.configure('Header.TFrame', background=cls.COLORS['header_bg'])
        style.configure('Section.TFrame', background=cls.COLORS['section_header_bg'])
        
        # Configure TLabel
        style.configure('TLabel', 
                        background=cls.COLORS['bg'], 
                        foreground=cls.COLORS['text'],
                        font=cls.FONTS['normal'])
        
        style.configure('Header.TLabel', 
                        background=cls.COLORS['header_bg'],
                        foreground=cls.COLORS['header_fg'],
                        font=cls.FONTS['title'])
        
        style.configure('Section.TLabel',
                        background=cls.COLORS['section_header_bg'],
                        foreground=cls.COLORS['text'],
                        font=cls.FONTS['bold'])
        
        # UPDATED BUTTON STYLES with better contrast
        # Default button - light blue with blue text
        style.configure('TButton', 
                        font=cls.FONTS['button'],
                        background=cls.COLORS['button_bg'],
                        foreground=cls.COLORS['button_fg'],
                        padding=(10, 5))
        
        style.map('TButton',
                  background=[('pressed', cls.COLORS['button_pressed']),
                              ('active', cls.COLORS['button_hover']),
                              ('disabled', cls.COLORS['button_disabled'])],
                  foreground=[('disabled', cls.COLORS['button_disabled_fg']),
                              ('pressed', cls.COLORS['button_fg']),
                              ('active', cls.COLORS['button_fg'])])
        
        # Primary button - slightly larger
        style.configure('Primary.TButton', 
                        font=cls.FONTS['bold'],
                        padding=(12, 6))
        
        # Action button - light green with green text
        style.configure('Action.TButton', 
                        font=cls.FONTS['button'],
                        background=cls.COLORS['action_button_bg'],
                        foreground=cls.COLORS['action_button_fg'],
                        padding=(10, 6))
        
        style.map('Action.TButton',
                  background=[('pressed', cls.COLORS['action_button_pressed']),
                              ('active', cls.COLORS['action_button_hover']),
                              ('disabled', cls.COLORS['button_disabled'])],
                  foreground=[('disabled', cls.COLORS['button_disabled_fg']),
                              ('pressed', cls.COLORS['action_button_fg']),
                              ('active', cls.COLORS['action_button_fg'])])
                  
        # Danger button - light red with red text
        style.configure('Danger.TButton', 
                        font=cls.FONTS['button'],
                        background=cls.COLORS['danger_button_bg'],
                        foreground=cls.COLORS['danger_button_fg'],
                        padding=(10, 6))
        
        style.map('Danger.TButton',
                  background=[('pressed', cls.COLORS['danger_button_pressed']),
                              ('active', cls.COLORS['danger_button_hover']),
                              ('disabled', cls.COLORS['button_disabled'])],
                  foreground=[('disabled', cls.COLORS['button_disabled_fg']),
                              ('pressed', cls.COLORS['danger_button_fg']),
                              ('active', cls.COLORS['danger_button_fg'])])
                  
        # Small action button
        style.configure('Small.Action.TButton',
                        font=cls.FONTS['button'],
                        padding=(6, 3))
        
        # Configure TEntry - text input fields
        style.configure('TEntry', 
                        fieldbackground=cls.COLORS['input_bg'],
                        foreground=cls.COLORS['text'],
                        bordercolor=cls.COLORS['input_border'],
                        lightcolor=cls.COLORS['input_border'],
                        darkcolor=cls.COLORS['input_border'],
                        borderwidth=1,
                        font=cls.FONTS['normal'],
                        padding=5)
        
        style.map('TEntry',
                  fieldbackground=[('disabled', cls.COLORS['button_disabled'])],
                  bordercolor=[('focus', cls.COLORS['input_border_focus'])])
        
        # Configure TProgressbar
        style.configure("TProgressbar",
                        troughcolor=cls.COLORS['progress_bg'],
                        background=cls.COLORS['progress_fg'],
                        thickness=8)
        
        # Configure TSeparator
        style.configure('TSeparator',
                        background=cls.COLORS['separator'])
        
        # Configure TNotebook (for tabs if used)
        style.configure('TNotebook',
                        background=cls.COLORS['bg'],
                        tabmargins=(0, 0, 0, 0))
       
        style.configure('TNotebook.Tab',
                        background=cls.COLORS['bg'],
                        foreground=cls.COLORS['text'],
                        font=cls.FONTS['normal'],
                        padding=(10, 4))
                       
        style.map('TNotebook.Tab',
                  background=[('selected', cls.COLORS['list_selected_bg']),
                              ('active', cls.COLORS['button_hover'])],
                  foreground=[('selected', cls.COLORS['list_selected_fg']),
                              ('active', cls.COLORS['text'])])
                             
        # Configure TCheckbutton
        style.configure('TCheckbutton',
                        background=cls.COLORS['bg'],
                        foreground=cls.COLORS['text'],
                        font=cls.FONTS['normal'])
                       
        # Configure TRadiobutton
        style.configure('TRadiobutton',
                        background=cls.COLORS['bg'],
                        foreground=cls.COLORS['text'],
                        font=cls.FONTS['normal'])