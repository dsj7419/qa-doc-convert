"""
Main application window implementing the MVP pattern view interfaces.
"""
import logging
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, List, Optional, Set

from models.paragraph import Paragraph, ParaRole
from ui.components.action_panel import ActionPanel
from ui.components.header_panel import HeaderPanel
from ui.components.log_panel import LogPanel
from ui.components.paragraph_list import ParagraphList
from ui.components.status_bar import StatusBar
from ui.interfaces import IMainWindowView, IParagraphListView
from utils.theme import AppTheme

logger = logging.getLogger(__name__)

class MainWindow(IMainWindowView, IParagraphListView):
    """Main application window implementing the MVP view interfaces."""
    
    def __init__(self, root):
        """
        Initialize the main window.
        
        Args:
            root: The root Tk instance
        """
        self.root = root
        self.root.title("QA Verifier - Professional Edition")
        self.root.geometry("1100x750")
        self.root.minsize(900, 650)
        
        # Configure theme
        self.root.configure(bg=AppTheme.COLORS['bg'])
        AppTheme.configure(self.root)
        
        # Presenter reference - will be set by main.py
        self.presenter = None
        
        # Build UI
        self._build_ui()
    
    def set_presenter(self, presenter):
        """
        Set the presenter for this view.
        
        Args:
            presenter: The presenter to use
        """
        self.presenter = presenter
        
        # Set up the paragraph list selection callback
        self.para_list.set_selection_callback(self._on_paragraph_selected)
    
    def _build_ui(self):
        """Build the main UI structure."""
        # Configure grid layout
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=0)  # Header
        self.root.rowconfigure(1, weight=0)  # Status bar
        self.root.rowconfigure(2, weight=1)  # Main content
        self.root.rowconfigure(3, weight=0)  # Log panel
        
        # Apply the background color to the root window
        self.root.configure(bg=AppTheme.COLORS['bg'])
        
        # Create a gradient frame for the header
        self.header = HeaderPanel(
            self.root,
            on_load=self._on_load_click,
            on_save=self._on_save_click
        )
        self.header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        
        # Status Bar - reduced height
        self.status_bar = StatusBar(self.root)
        self.status_bar.grid(row=1, column=0, sticky="ew", padx=10, pady=(2, 0))
        
        # Main Content Area (Paragraph List and Actions)
        main_frame = ttk.Frame(self.root, style='TFrame')
        main_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        
        main_frame.columnconfigure(0, weight=3)  # Paragraph list
        main_frame.columnconfigure(1, weight=0)  # Separator
        main_frame.columnconfigure(2, weight=1)  # Actions
        main_frame.rowconfigure(0, weight=1)
        
        # Paragraph List
        self.para_list = ParagraphList(main_frame)
        self.para_list.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # Separator
        sep = ttk.Separator(main_frame, orient=tk.VERTICAL)
        sep.grid(row=0, column=1, sticky="ns", padx=5)
        
        # Action Panel - set to fixed width for better layout control
        action_frame = ttk.Frame(main_frame, width=250)
        action_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 0))
        action_frame.grid_propagate(False)  # Prevent resizing
        
        self.action_panel = ActionPanel(
            action_frame,
            on_mark_question=lambda: self._on_change_role(ParaRole.QUESTION),
            on_mark_answer=lambda: self._on_change_role(ParaRole.ANSWER),
            on_mark_ignore=lambda: self._on_change_role(ParaRole.IGNORE),
            on_merge_up=self._on_merge_up,
            on_set_expected_count=self._on_set_expected_count,
            on_exit=self._on_exit
        )
        self.action_panel.pack(fill=tk.BOTH, expand=True)
        
        # Log Panel - reduced height
        self.log_panel = LogPanel(self.root)
        self.log_panel.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 5))
    
    # IMainWindowView implementation
    def display_paragraphs(self, paragraphs: List[Paragraph]) -> None:
        """
        Display paragraphs in the UI.
        
        Args:
            paragraphs: List of paragraphs to display
        """
        self.para_list.set_paragraphs(paragraphs)
    
    def show_status(self, message: str) -> None:
        """
        Show a status message.
        
        Args:
            message: Status message to display
        """
        self.status_bar.update_status(message)
    
    def show_error(self, title: str, message: str) -> None:
        """
        Show an error message.
        
        Args:
            title: Error title
            message: Error message
        """
        messagebox.showerror(title, message)
    
    def show_info(self, title: str, message: str) -> None:
        """
        Show an info message.
        
        Args:
            title: Info title
            message: Info message
        """
        messagebox.showinfo(title, message)
    
    def show_warning(self, title: str, message: str) -> None:
        """
        Show a warning message.
        
        Args:
            title: Warning title
            message: Warning message
        """
        messagebox.showwarning(title, message)
    
    def ask_yes_no(self, title: str, message: str) -> bool:
        """
        Ask a yes/no question.
        
        Args:
            title: Question title
            message: Question message
            
        Returns:
            bool: True for yes, False for no
        """
        return messagebox.askyesno(title, message)
    
    def ask_yes_no_cancel(self, title: str, message: str) -> Optional[bool]:
        """
        Ask a yes/no/cancel question.
        
        Args:
            title: Question title
            message: Question message
            
        Returns:
            Optional[bool]: True for yes, False for no, None for cancel
        """
        return messagebox.askyesnocancel(title, message, icon=messagebox.WARNING)
    
    def log_message(self, message: str, level: str = "INFO") -> None:
        """
        Log a message.
        
        Args:
            message: Message to log
            level: Log level
        """
        self.log_panel.log_message(message, level)
    
    def update_progress(self, question_count: int, expected_count: int) -> None:
        """
        Update the progress display.
        
        Args:
            question_count: Current question count
            expected_count: Expected question count
        """
        self.action_panel.update_progress(question_count, expected_count)
    
    def set_expected_count(self, count: int) -> None:
        """
        Set the expected question count in the UI.
        
        Args:
            count: Expected question count
        """
        self.action_panel.set_expected_count(count)
    
    def get_expected_count(self) -> str:
        """
        Get the expected question count from the UI.
        
        Returns:
            str: Expected question count as string
        """
        return self.action_panel.get_expected_count()
    
    def enable_editing_actions(self, enabled: bool) -> None:
        """
        Enable or disable editing actions.
        
        Args:
            enabled: Whether actions should be enabled
        """
        self.action_panel.update_selection_state(enabled)
    
    def reset_ui(self) -> None:
        """Reset the UI state."""
        self.para_list.clear()
        self.action_panel.reset()
        self.show_status("Load a DOCX file to begin.")
    
    # IParagraphListView implementation (delegated to para_list)
    def set_paragraphs(self, paragraphs: List[Paragraph]) -> None:
        """
        Set the paragraphs to display.
        
        Args:
            paragraphs: List of paragraphs to display
        """
        self.para_list.set_paragraphs(paragraphs)
    
    def get_selected_indices(self) -> Set[int]:
        """
        Get the indices of selected paragraphs.
        
        Returns:
            Set of selected indices
        """
        return self.para_list.get_selected_indices()
    
    def set_selection_callback(self, callback: Callable[[], None]) -> None:
        """
        Set the callback for selection changes.
        
        Args:
            callback: Callback function
        """
        self.para_list.set_selection_callback(callback)
    
    def clear(self) -> None:
        """Clear the list and reset state."""
        self.para_list.clear()
    
    # Event handlers that delegate to the presenter
    def _on_paragraph_selected(self) -> None:
        """Handle paragraph selection events."""
        if self.presenter:
            self.presenter.paragraph_selection_changed()
    
    def _on_load_click(self) -> None:
        """Handle load button click."""
        if self.presenter:
            self.presenter.load_file_requested()
    
    def _on_save_click(self) -> None:
        """Handle save button click."""
        if self.presenter:
            self.presenter.save_file_requested()
    
    def _on_change_role(self, new_role: ParaRole) -> None:
        """
        Handle role change button clicks.
        
        Args:
            new_role: New role to assign
        """
        if self.presenter:
            self.presenter.change_role_requested(new_role)
    
    def _on_merge_up(self) -> None:
        """Handle merge up button click."""
        if self.presenter:
            self.presenter.merge_up_requested()
    
    def _on_set_expected_count(self) -> None:
        """Handle set expected count button click."""
        if self.presenter:
            self.presenter.set_expected_count_requested()
    
    def _on_exit(self) -> None:
        """Handle exit button click."""
        if self.presenter:
            self.presenter.exit_requested()