"""
Theme configuration and styling for the application.
Elegant dark-themed color scheme with enhanced readability and visual appeal.
"""
import tkinter as tk
from tkinter import ttk
import platform

class AppTheme:
    """Manages application theming and styling."""
    
    # Refined professional color palette
    COLORS = {
        # Main colors
        'primary': "#1e3a5f",      # Rich navy blue
        'secondary': "#2d4a6d",    # Medium navy
        'accent': "#5d9cec",       # Vibrant blue - for emphasis
        'success': "#53b983",      # Soft green - less harsh
        'warning': "#fcb941",      # Soft orange
        'danger': "#f06060",       # Soft red
        'light': "#f5f6fa",        # Off-white
        'dark': "#2b333e",         # Dark slate - nearly black
        
        # UI element colors - main interface
        'bg': "#f0f4f8",           # Very light blue-gray background
        'header_bg': "#1e3a5f",    # Rich navy header
        'header_fg': "#ffffff",    # White text for headers
        
        # Button colors
        'button_bg': "#456789",    # Darker blue for better contrast
        'button_fg': "#ffffff",    # White text
        'button_hover': "#5d7799", # Lighter on hover
        'action_button_bg': "#2d567d", # Darker blue for actions
        'action_button_fg': "#ffffff", # White text
        'action_button_hover': "#3d6897", # Lighter on hover
        'exit_bg': "#c13636",      # Darker red for better contrast
        'exit_fg': "#ffffff",      # White text
        'exit_hover': "#d84545",   # Lighter on hover
        
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
        """Configure ttk widget styles for an elegant professional look."""
        # TButton style - more refined with slight 3D effect
        style.configure(
            'TButton',
            background=cls.COLORS['button_bg'],
            foreground=cls.COLORS['button_fg'],
            font=cls.FONTS['normal'],
            padding=(12, 6),
            relief="raised",
            borderwidth=1
        )
        style.map('TButton',
            background=[('active', cls.COLORS['button_hover'])],
            relief=[('pressed', 'sunken')]
        )
        
        # Primary Button style
        style.configure(
            'Primary.TButton',
            background=cls.COLORS['button_bg'],
            foreground=cls.COLORS['button_fg'],
            font=cls.FONTS['bold'],
            padding=(12, 6)
        )
        style.map('Primary.TButton',
            background=[('active', cls.COLORS['button_hover'])],
            relief=[('pressed', 'sunken')]
        )
        
        # Action Button style (blue)
        style.configure(
            'Action.TButton',
            background=cls.COLORS['action_button_bg'],
            foreground=cls.COLORS['action_button_fg'],
            font=cls.FONTS['normal'],
            padding=(12, 6)
        )
        style.map('Action.TButton',
            background=[('active', cls.COLORS['action_button_hover'])],
            relief=[('pressed', 'sunken')]
        )
        
        # Danger Button style (red)
        style.configure(
            'Danger.TButton',
            background=cls.COLORS['exit_bg'],
            foreground=cls.COLORS['exit_fg'],
            font=cls.FONTS['normal'],
            padding=(12, 6)
        )
        style.map('Danger.TButton',
            background=[('active', cls.COLORS['exit_hover'])],
            relief=[('pressed', 'sunken')]
        )
        
        # TFrame
        style.configure(
            'TFrame',
            background=cls.COLORS['bg']
        )
        
        # TLabel
        style.configure(
            'TLabel',
            background=cls.COLORS['bg'],
            font=cls.FONTS['normal']
        )
        
        # Header Label
        style.configure(
            'Header.TLabel',
            background=cls.COLORS['header_bg'],
            foreground=cls.COLORS['header_fg'],
            font=cls.FONTS['title']
        )
        
        # Header Frame
        style.configure(
            'Header.TFrame',
            background=cls.COLORS['header_bg']
        )
        
        # TProgressbar - more elegant progress bar
        style.configure(
            "TProgressbar",
            troughcolor=cls.COLORS['progress_bg'],
            background=cls.COLORS['progress_fg'],
            thickness=8,
            borderwidth=0
        )
        
        # TEntry - improved entry fields
        style.configure(
            "TEntry",
            fieldbackground=cls.COLORS['input_bg'],
            bordercolor=cls.COLORS['input_border'],
            padding=5
        )
        style.map('TEntry',
            bordercolor=[('focus', cls.COLORS['accent'])]
        )
        
        # TSeparator
        style.configure(
            "TSeparator",
            background=cls.COLORS['separator']
        )

class TkButton(tk.Button):
    """Custom button class with elegant styling and forced text colors."""
    
    def __init__(self, parent, text, command=None, style='primary', **kwargs):
        """
        Initialize a custom button with forced text coloring.
        
        Args:
            parent: Parent widget
            text: Button text
            command: Button command
            style: Button style ('primary', 'action', 'danger')
            **kwargs: Additional Button parameters
        """
        self.style = style
        
        # Explicitly force white text for all buttons, regardless of style
        fg_color = "#ffffff"
        
        # Define colors based on style
        if style == 'primary':
            bg_color = AppTheme.COLORS['button_bg']
            hover_bg = AppTheme.COLORS['button_hover']
        elif style == 'action':
            bg_color = AppTheme.COLORS['action_button_bg']
            hover_bg = AppTheme.COLORS['action_button_hover']
        elif style == 'danger':
            bg_color = AppTheme.COLORS['exit_bg']
            hover_bg = AppTheme.COLORS['exit_hover']
        else:
            bg_color = AppTheme.COLORS['light']
            hover_bg = self._darken_color(bg_color)
        
        # Create a new kwargs dictionary to avoid modifying the original
        new_kwargs = kwargs.copy()
        
        # Explicitly set all style properties, overriding any provided values
        new_kwargs['bg'] = bg_color
        new_kwargs['fg'] = fg_color  # FORCE white text
        new_kwargs['activebackground'] = hover_bg
        new_kwargs['activeforeground'] = fg_color  # FORCE white text during clicks
        new_kwargs['font'] = AppTheme.FONTS['normal']
        new_kwargs['highlightthickness'] = 0
        new_kwargs['borderwidth'] = 1
        new_kwargs['relief'] = 'raised'
        new_kwargs['cursor'] = 'hand2'
        
        # Initialize with forced settings
        super().__init__(parent, text=text, command=command, **new_kwargs)
        
        # CRITICAL: Force text color again after initialization
        self.config(fg=fg_color)
        
        # Store original colors for hover effects
        self._original_bg = bg_color
        self._original_fg = fg_color
        
        # Bind hover events for visual feedback
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
        # Bind press events for visual feedback
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        
        # Add subtle rounding effect through relief and borderwidth
        if platform.system() == 'Windows':
            # Windows looks better with slightly different settings
            self.config(relief="ridge", borderwidth=1)
        else:
            # Default for other platforms
            self.config(relief="raised", borderwidth=1)
    
    def _on_enter(self, event):
        """Handle mouse enter event."""
        # Change background color on hover
        if self.style == 'primary':
            self.config(background=AppTheme.COLORS['button_hover'])
        elif self.style == 'action':
            self.config(background=AppTheme.COLORS['action_button_hover'])
        elif self.style == 'danger':
            self.config(background=AppTheme.COLORS['exit_hover'])
        
        # Ensure text remains white during hover
        self.config(fg="#ffffff")
        
        # Store current font for restoration
        current_font = self.cget('font')
        if isinstance(current_font, str):
            # Skip if font is a string name
            return
        self._original_font = current_font
    
    def _on_leave(self, event):
        """Handle mouse leave event."""
        # Restore original background color
        if self.style == 'primary':
            self.config(background=AppTheme.COLORS['button_bg'])
        elif self.style == 'action':
            self.config(background=AppTheme.COLORS['action_button_bg'])
        elif self.style == 'danger':
            self.config(background=AppTheme.COLORS['exit_bg'])
        
        # CRITICAL: Force text to white when mouse leaves
        self.config(fg="#ffffff")
        
        # Restore original font
        if hasattr(self, '_original_font'):
            self.config(font=self._original_font)
    
    def _on_press(self, event):
        """Handle button press event."""
        self.config(relief="sunken")
        # Ensure text remains white during press
        self.config(fg="#ffffff")
    
    def _on_release(self, event):
        """Handle button release event."""
        if platform.system() == 'Windows':
            self.config(relief="ridge")
        else:
            self.config(relief="raised")
        
        # CRITICAL: Force text to white when button is released
        self.config(fg="#ffffff")
        
        # Also restore background color
        self._on_leave(event)
    
    @staticmethod
    def _darken_color(hex_color, factor=0.8):
        """
        Darken a hex color by a factor.
        
        Args:
            hex_color: Hex color string
            factor: Darkening factor (0-1)
            
        Returns:
            Darkened hex color string
        """
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        
        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    @staticmethod
    def _darken_color(hex_color, factor=0.8):
        """
        Darken a hex color by a factor.
        
        Args:
            hex_color: Hex color string
            factor: Darkening factor (0-1)
            
        Returns:
            Darkened hex color string
        """
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        
        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)
        
        return f"#{r:02x}{g:02x}{b:02x}"