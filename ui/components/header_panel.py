"""
Header panel component.
"""
import tkinter as tk
from tkinter import ttk

from utils.theme import AppTheme

class HeaderPanel(ttk.Frame):
    """Header panel with logo and main controls."""
    
    def __init__(self, parent, on_load=None, on_save=None):
        """
        Initialize the header panel.
        
        Args:
            parent: Parent widget
            on_load: Callback for load button
            on_save: Callback for save button
        """
        super().__init__(
            parent, 
            style='Header.TFrame', 
            padding=(15, 10)
        )
        
        self.on_load = on_load
        self.on_save = on_save
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI elements."""
        # Configure grid
        self.columnconfigure(0, weight=1)  # Logo/title - expands
        self.columnconfigure(1, weight=0)  # Button area - fixed width
        
        # Create header container with padding
        title_container = ttk.Frame(self, style='Header.TFrame')
        title_container.grid(row=0, column=0, sticky="w", padx=(5, 20))
        
        # Icon/Logo (simulated with a label)
        icon_label = ttk.Label(
            title_container,
            text="QA",
            style='Header.TLabel',
            font=("Segoe UI", 18, "bold"),
            foreground=AppTheme.COLORS['header_fg']
        )
        icon_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Title with enhanced styling
        title_label = ttk.Label(
            title_container,
            text="Verifier Professional",
            style='Header.TLabel',
            font=AppTheme.FONTS['title'],
            foreground=AppTheme.COLORS['header_fg']
        )
        title_label.pack(side=tk.LEFT)
        
        # Buttons Frame (right-aligned)
        buttons_frame = ttk.Frame(self, style='Header.TFrame')
        buttons_frame.grid(row=0, column=1, sticky="e")
        
        # Load Button
        self.load_btn = ttk.Button(
            buttons_frame,
            text="Load DOCX File",
            command=self._on_load_click,
            style='Primary.TButton',
            width=15
        )
        self.load_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Save Button
        self.save_btn = ttk.Button(
            buttons_frame,
            text="Save Corrected CSV",
            command=self._on_save_click,
            style='Primary.TButton',
            width=18
        )
        self.save_btn.pack(side=tk.LEFT)
    
    def _on_load_click(self):
        """Handle load button click."""
        if callable(self.on_load):
            self.on_load()
    
    def _on_save_click(self):
        """Handle save button click."""
        if callable(self.on_save):
            self.on_save()