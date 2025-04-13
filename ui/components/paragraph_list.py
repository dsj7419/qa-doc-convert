"""
Paragraph list component.
"""
import tkinter as tk
from tkinter import ttk
from typing import List, Callable, Optional, Set

from models.paragraph import Paragraph, ParaRole
from utils.theme import AppTheme

class ParagraphList(ttk.Frame):
    """List of paragraphs with filtering capability."""
    
    def __init__(self, parent):
        """
        Initialize the paragraph list.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent, style='TFrame')
        
        self.paragraphs = []
        self.selection_callback = None
        self.current_selection_index = -1
        self.displayed_paragraphs = []  # Track which paragraphs are currently displayed
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI elements."""
        # Configure grid
        self.rowconfigure(0, weight=0)  # Header - fixed
        self.rowconfigure(1, weight=0)  # Filter - fixed
        self.rowconfigure(2, weight=1)  # Listbox - expandable
        self.rowconfigure(3, weight=0)  # Horizontal scrollbar - fixed
        self.rowconfigure(4, weight=0)  # Legend - fixed
        self.columnconfigure(0, weight=1)  # Main content - expandable
        self.columnconfigure(1, weight=0)  # Vertical scrollbar - fixed
        
        # Document Paragraphs header
        header_frame = ttk.Frame(self, style='Header.TFrame')
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        
        header_label = ttk.Label(
            header_frame,
            text="Document Paragraphs",
            style='Header.TLabel',
            font=AppTheme.FONTS['title'],
            foreground=AppTheme.COLORS['header_fg'],
            padding=(10, 8)
        )
        header_label.pack(anchor="w", fill=tk.X)
        
        # Filter container
        filter_container = ttk.Frame(self, style='Section.TFrame')
        filter_container.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        
        # Filter label
        filter_label = ttk.Label(
            filter_container,
            text="Filter:",
            style='Section.TLabel',
            padding=(10, 5)
        )
        filter_label.pack(side=tk.LEFT)
        
        self.filter_var = tk.StringVar()
        self.filter_var.trace("w", self._on_filter_change)
        
        # Filter entry field
        filter_entry = ttk.Entry(
            filter_container,
            textvariable=self.filter_var,
            width=30
        )
        filter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Clear button
        clear_btn = ttk.Button(
            filter_container,
            text="Clear",
            command=self._clear_filter,
            style='TButton',
            width=8
        )
        clear_btn.pack(side=tk.LEFT, padx=(5, 10))
        
        # Listbox with custom styling - CRITICAL FIX: updated selection colors
        self.listbox = tk.Listbox(
            self,
            font=AppTheme.FONTS['list'],
            bg=AppTheme.COLORS['list_bg'],
            fg=AppTheme.COLORS['list_fg'],
            selectbackground=AppTheme.COLORS['list_selected_bg'],
            selectforeground=AppTheme.COLORS['text'],  # CRITICAL FIX: Keep text color visible on selection
            borderwidth=1,
            relief=tk.SUNKEN,
            highlightthickness=1,
            highlightbackground=AppTheme.COLORS['list_border'],
            activestyle='none',
            exportselection=False,
            selectmode=tk.EXTENDED  # Allow multiple selection
        )
        self.listbox.grid(row=2, column=0, sticky="nsew")
        
        # Scrollbars
        y_scrollbar = ttk.Scrollbar(
            self,
            orient=tk.VERTICAL,
            command=self.listbox.yview
        )
        y_scrollbar.grid(row=2, column=1, sticky="ns")
        self.listbox.config(yscrollcommand=y_scrollbar.set)
        
        x_scrollbar = ttk.Scrollbar(
            self,
            orient=tk.HORIZONTAL,
            command=self.listbox.xview
        )
        x_scrollbar.grid(row=3, column=0, sticky="ew")
        self.listbox.config(xscrollcommand=x_scrollbar.set)
        
        # Create legend for paragraph roles
        legend_frame = ttk.Frame(self, style='TFrame', padding=5)
        legend_frame.grid(row=4, column=0, columnspan=2, sticky="ew")
        
        # Title for legend
        legend_title = ttk.Label(
            legend_frame,
            text="Role Legend:",
            font=AppTheme.FONTS['bold']
        )
        legend_title.pack(side=tk.LEFT, padx=(0, 10))
        
        # Create color swatches for each role
        self._create_legend_item(legend_frame, "Question", AppTheme.COLORS['role_question_bg'], AppTheme.COLORS['role_question_fg'])
        self._create_legend_item(legend_frame, "Answer", AppTheme.COLORS['role_answer_bg'], AppTheme.COLORS['role_answer_fg'])
        self._create_legend_item(legend_frame, "Ignore", AppTheme.COLORS['role_ignore_bg'], AppTheme.COLORS['role_ignore_fg'])
        self._create_legend_item(legend_frame, "Undetermined", AppTheme.COLORS['role_undetermined_bg'], AppTheme.COLORS['role_undetermined_fg'])
        
        # Bind selection event
        self.listbox.bind('<<ListboxSelect>>', self._on_selection_change)
    
    def _create_legend_item(self, parent, text, bg_color, fg_color):
        """Create a legend item with color swatch and text."""
        item_frame = ttk.Frame(parent)
        item_frame.pack(side=tk.LEFT, padx=10)
        
        # Color swatch
        swatch = tk.Label(
            item_frame, 
            bg=bg_color, 
            width=3, 
            height=1
        )
        swatch.pack(side=tk.LEFT, padx=(0, 3))
        
        # Text label
        label = ttk.Label(
            item_frame,
            text=text,
            foreground=fg_color
        )
        label.pack(side=tk.LEFT)
    
    def set_paragraphs(self, paragraphs: List[Paragraph]):
        """
        Set the paragraphs to display.
        
        Args:
            paragraphs: List of paragraphs
        """
        self.paragraphs = paragraphs
        self.refresh_display()
    
    def refresh_display(self):
        """Refresh the listbox display."""
        # Store current selection if possible
        selected_indices = self.listbox.curselection()
        selected_idx = selected_indices[0] if selected_indices else -1
        
        # Clear listbox and tracking
        self.listbox.delete(0, tk.END)
        self.displayed_paragraphs = []
        
        # Get filter text
        filter_text = self.filter_var.get().lower()
        
        # Add filtered paragraphs
        for i, para in enumerate(self.paragraphs):
            if not filter_text or filter_text in para.text.lower():
                # Add paragraph to listbox
                self.listbox.insert(tk.END, para.display_text)
                
                # Add to displayed paragraphs tracking
                self.displayed_paragraphs.append(i)
                
                # CRITICAL FIX: Store original colors
                # Set background and foreground colors based on role
                if para.role == ParaRole.QUESTION:
                    bg_color = AppTheme.COLORS['role_question_bg']
                    fg_color = AppTheme.COLORS['role_question_fg']
                elif para.role == ParaRole.ANSWER:
                    bg_color = AppTheme.COLORS['role_answer_bg']
                    fg_color = AppTheme.COLORS['role_answer_fg']
                elif para.role == ParaRole.IGNORE:
                    bg_color = AppTheme.COLORS['role_ignore_bg']
                    fg_color = AppTheme.COLORS['role_ignore_fg']
                else:  # UNDETERMINED
                    bg_color = AppTheme.COLORS['role_undetermined_bg']
                    fg_color = AppTheme.COLORS['role_undetermined_fg']
                
                # Configure item appearance
                self.listbox.itemconfig(
                    len(self.displayed_paragraphs) - 1, 
                    {'bg': bg_color, 'fg': fg_color}
                )
        
        # Try to restore selection
        if selected_idx >= 0 and selected_idx < self.listbox.size():
            self.listbox.selection_set(selected_idx)
            self.listbox.activate(selected_idx)
            self.listbox.see(selected_idx)
            self.current_selection_index = selected_idx
        else:
            self.current_selection_index = -1
    
    def _on_filter_change(self, *args):
        """Handle filter text changes."""
        self.refresh_display()
    
    def _clear_filter(self):
        """Clear the filter text."""
        self.filter_var.set("")
        self.refresh_display()
    
    def _on_selection_change(self, event):
        """Handle selection changes in the listbox."""
        selected_indices = self.listbox.curselection()
        if selected_indices:
            self.current_selection_index = selected_indices[0]
        else:
            self.current_selection_index = -1
        
        # Call the selection callback if registered
        if callable(self.selection_callback):
            self.selection_callback()
    
    def set_selection_callback(self, callback: Callable[[], None]):
        """
        Set the callback for selection changes.
        
        Args:
            callback: Callback function
        """
        self.selection_callback = callback
    
    def get_selected_indices(self) -> Set[int]:
        """
        Get the indices of selected paragraphs.
        
        Returns:
            Set of selected indices in the original paragraphs list
        """
        # Convert listbox indices to original paragraph indices
        listbox_indices = set(self.listbox.curselection())
        original_indices = set()
        
        for idx in listbox_indices:
            if 0 <= idx < len(self.displayed_paragraphs):
                original_indices.add(self.displayed_paragraphs[idx])
        
        return original_indices
    
    def clear(self):
        """Clear the listbox and reset state."""
        self.paragraphs = []
        self.displayed_paragraphs = []
        self.listbox.delete(0, tk.END)
        self.filter_var.set("")
        self.current_selection_index = -1