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
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI elements."""
        # Configure grid
        self.rowconfigure(0, weight=0)  # Header
        self.rowconfigure(1, weight=0)  # Filter
        self.rowconfigure(2, weight=1)  # Listbox
        self.rowconfigure(3, weight=0)  # Horizontal scrollbar
        self.columnconfigure(0, weight=1)  # Main content
        self.columnconfigure(1, weight=0)  # Vertical scrollbar
        
        # Document Paragraphs header
        header_container = ttk.Frame(self, style='TFrame')
        header_container.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        # Header with background
        header_bg = ttk.Frame(header_container, style='Header.TFrame')
        header_bg.pack(fill=tk.X, expand=True)
        
        # Create header content with icon and text
        header_content = ttk.Frame(header_bg, style='Header.TFrame')
        header_content.pack(fill=tk.X, padx=5, pady=3)
        
        # Document icon
        doc_icon = ttk.Label(
            header_content,
            text="📄",  # Document emoji
            style='Header.TLabel',
            font=("Segoe UI", 12)
        )
        doc_icon.pack(side=tk.LEFT, padx=(0, 8))
        
        header_label = ttk.Label(
            header_content,
            text="Document Paragraphs:",
            style='Header.TLabel',
            font=AppTheme.FONTS['bold']
        )
        header_label.pack(side=tk.LEFT)
        
        # Filter frame
        filter_frame = ttk.Frame(self, style='TFrame')
        filter_frame.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        
        # Filter label with background
        filter_bg = ttk.Frame(filter_frame, style='Header.TFrame')
        filter_bg.pack(side=tk.LEFT, padx=(0, 8))
        
        filter_label = ttk.Label(
            filter_bg,
            text="Filter:",
            style='Header.TLabel',
            font=AppTheme.FONTS['bold']
        )
        filter_label.pack(side=tk.LEFT, padx=5, pady=3)
        
        self.filter_var = tk.StringVar()
        self.filter_var.trace("w", self._on_filter_change)
        
        # Enhanced entry field
        filter_entry = ttk.Entry(
            filter_frame,
            textvariable=self.filter_var,
            width=20
        )
        filter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Clear button
        clear_btn = ttk.Button(
            filter_frame,
            text="Clear",
            command=self._clear_filter,
            style='Action.TButton',
            width=8
        )
        clear_btn.pack(side=tk.LEFT, padx=(8, 0))
        
        # Listbox with custom styling - improved design
        self.listbox = tk.Listbox(
            self,
            font=AppTheme.FONTS['list'],
            bg=AppTheme.COLORS['list_bg'],
            selectbackground=AppTheme.COLORS['list_selected_bg'],
            selectforeground=AppTheme.COLORS['list_selected_fg'],
            borderwidth=1,
            relief=tk.SUNKEN,
            exportselection=False,
            activestyle='none',
            highlightthickness=1,
            highlightbackground=AppTheme.COLORS['list_border'],
            highlightcolor=AppTheme.COLORS['accent'],
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
        
        # Bind selection event
        self.listbox.bind('<<ListboxSelect>>', self._on_selection_change)
        
        # Add keyboard shortcuts for Undo/Redo
        self.bind_all("<Control-z>", self._on_ctrl_z)
        self.bind_all("<Control-y>", self._on_ctrl_y)
    
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
        
        # Clear listbox
        self.listbox.delete(0, tk.END)
        
        # Get filter text
        filter_text = self.filter_var.get().lower()
        
        # Add filtered paragraphs
        for i, para in enumerate(self.paragraphs):
            if not filter_text or filter_text in para.text.lower():
                # Add paragraph to listbox
                self.listbox.insert(tk.END, para.display_text)
                
                # Set background color based on role
                if para.role == ParaRole.QUESTION:
                    bg_color = AppTheme.COLORS['role_question_bg']
                    self.listbox.itemconfig(self.listbox.size()-1, {'bg': bg_color})
                elif para.role == ParaRole.ANSWER:
                    bg_color = AppTheme.COLORS['role_answer_bg']
                    self.listbox.itemconfig(self.listbox.size()-1, {'bg': bg_color})
                elif para.role == ParaRole.IGNORE:
                    bg_color = AppTheme.COLORS['role_ignore_bg']
                    self.listbox.itemconfig(self.listbox.size()-1, {'bg': bg_color})
                else:  # UNDETERMINED
                    bg_color = AppTheme.COLORS['role_undetermined_bg']
                    self.listbox.itemconfig(self.listbox.size()-1, {'bg': bg_color})
        
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
    
    def _on_ctrl_z(self, event):
        """Handle Ctrl+Z keyboard shortcut."""
        # Find the parent window
        parent = self.winfo_toplevel()
        if hasattr(parent, 'event_generate'):
            parent.event_generate("<<Undo>>")
    
    def _on_ctrl_y(self, event):
        """Handle Ctrl+Y keyboard shortcut."""
        # Find the parent window
        parent = self.winfo_toplevel()
        if hasattr(parent, 'event_generate'):
            parent.event_generate("<<Redo>>")
    
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
            Set of selected indices
        """
        return set(self.listbox.curselection())
    
    def clear(self):
        """Clear the listbox and reset state."""
        self.paragraphs = []
        self.listbox.delete(0, tk.END)
        self.filter_var.set("")
        self.current_selection_index = -1