"""
Interfaces (abstract base classes) for UI components and presenters.
"""
from abc import ABC, abstractmethod
from typing import Callable, List, Optional, Set

from models.paragraph import Paragraph, ParaRole

class IView(ABC):
    """Base interface for all views."""
    pass

class IMainWindowView(IView):
    """Interface for the main window view."""
    
    @abstractmethod
    def display_paragraphs(self, paragraphs: List[Paragraph]) -> None:
        """Display paragraphs in the UI."""
        pass
    
    @abstractmethod
    def show_status(self, message: str) -> None:
        """Show a status message."""
        pass
    
    @abstractmethod
    def show_error(self, title: str, message: str) -> None:
        """Show an error message."""
        pass
        
    @abstractmethod
    def show_info(self, title: str, message: str) -> None:
        """Show an info message."""
        pass
        
    @abstractmethod
    def show_warning(self, title: str, message: str) -> None:
        """Show a warning message."""
        pass

    @abstractmethod
    def set_loading_state(self, loading: bool) -> None:
        """
        Set the loading state of the UI.
        
        Args:
            loading: Whether the application is in a loading state
        """
        pass
        
    @abstractmethod
    def ask_yes_no(self, title: str, message: str) -> bool:
        """Ask a yes/no question."""
        pass
        
    @abstractmethod
    def ask_yes_no_cancel(self, title: str, message: str) -> Optional[bool]:
        """Ask a yes/no/cancel question."""
        pass
    
    @abstractmethod
    def log_message(self, message: str, level: str = "INFO") -> None:
        """Log a message."""
        pass
    
    @abstractmethod
    def update_progress(self, question_count: int, expected_count: int) -> None:
        """Update the progress display."""
        pass
    
    @abstractmethod
    def set_expected_count(self, count: int) -> None:
        """Set the expected question count in the UI."""
        pass
    
    @abstractmethod
    def get_expected_count(self) -> str:
        """Get the expected question count from the UI."""
        pass
    
    @abstractmethod
    def enable_editing_actions(self, enabled: bool) -> None:
        """Enable or disable editing actions."""
        pass
    
    @abstractmethod
    def reset_ui(self) -> None:
        """Reset the UI state."""
        pass

class IParagraphListView(IView):
    """Interface for the paragraph list view."""
    
    @abstractmethod
    def set_paragraphs(self, paragraphs: List[Paragraph]) -> None:
        """Set the paragraphs to display."""
        pass
    
    @abstractmethod
    def get_selected_indices(self) -> Set[int]:
        """Get the indices of selected paragraphs."""
        pass
    
    @abstractmethod
    def set_selection_callback(self, callback: Callable[[], None]) -> None:
        """Set the callback for selection changes."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear the list and reset state."""
        pass

class IPresenter(ABC):
    """Base interface for all presenters."""
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the presenter."""
        pass

class IMainPresenter(IPresenter):
    """Interface for the main presenter."""
    
    @abstractmethod
    def load_file_requested(self) -> None:
        """Handle a load file request."""
        pass
    
    @abstractmethod
    def save_file_requested(self) -> None:
        """Handle a save file request."""
        pass
    
    @abstractmethod
    def paragraph_selection_changed(self) -> None:
        """Handle paragraph selection changes."""
        pass
    
    @abstractmethod
    def change_role_requested(self, new_role: ParaRole) -> None:
        """Handle role change requests."""
        pass
    
    @abstractmethod
    def merge_up_requested(self) -> None:
        """Handle merge up requests."""
        pass
    
    @abstractmethod
    def set_expected_count_requested(self) -> None:
        """Handle set expected count requests."""
        pass
    
    @abstractmethod
    def exit_requested(self) -> None:
        """Handle application exit requests."""
        pass