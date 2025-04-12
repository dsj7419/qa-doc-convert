"""
Main presenter for handling application logic.
"""
import logging
import os
from typing import Optional

from models.document import Document
from models.paragraph import ParaRole
from services.file_service import FileService
from ui.interfaces import IMainWindowView

logger = logging.getLogger(__name__)

class MainPresenter:
    """Main presenter for the application."""
    
    def __init__(self, view: IMainWindowView, document: Document, root):
        """
        Initialize the presenter.
        
        Args:
            view: The main window view
            document: The document model
            root: The root Tk object for window management
        """
        self.view = view
        self.document = document
        self.root = root
    
    def initialize(self) -> None:
        """Initialize the presenter."""
        self.view.show_status("Load a DOCX file to begin.")
    
    def load_file_requested(self) -> None:
        """Handle a load file request."""
        # Reset UI state
        self.view.reset_ui()
        self.document = Document()
        
        # Get file path from dialog
        file_path = FileService.select_docx_file()
        if not file_path:
            return
        
        # Update status
        self.view.show_status(f"Loading: {os.path.basename(file_path)}...")
        self.view.log_message(f"Loading file: {file_path}")
        
        # Load document with a status callback that updates the view
        status_callback = self.view.show_status
        
        # Load and process document
        if self.document.load_file(file_path, status_callback):
            # Update UI with paragraphs
            self.view.display_paragraphs(self.document.paragraphs)
            
            # Update expected count in UI
            self.view.set_expected_count(self.document.expected_question_count)
            
            # Update stats display
            self._update_stats()
            
            # Ready status
            self.view.show_status("Ready for verification. Select a paragraph.")
        else:
            self.view.show_error("Error", "Failed to load or process the document.")
            self.view.show_status("Error loading document.")
    
    def save_file_requested(self) -> None:
        """Handle a save file request."""
        if not self.document.file_path:
            self.view.show_error("Error", "No file loaded.")
            return
        
        if not self.document.paragraphs:
            self.view.show_error("Error", "No paragraph data available.")
            return
        
        self.view.log_message("Preparing to save CSV...")
        
        # Get Q&A data for validation
        _, q_count = self.document.get_qa_data()
        
        # Validate question count
        if q_count != self.document.expected_question_count:
            message = (
                f"You have {q_count} questions marked, but expected {self.document.expected_question_count}.\n\n"
                f"Would you like to:\n"
                f"- Save with the current {q_count} questions\n"
                f"- Update the expected count to {q_count} and continue editing\n"
                f"- Cancel and continue editing"
            )
            
            response = self.view.ask_yes_no_cancel(
                "Question Count Mismatch", 
                message
            )
            
            if response is None:  # Cancel - continue editing
                self.view.log_message(f"Save cancelled. Continuing to edit.", level="INFO")
                return
            elif response is False:  # No - update expected count
                self.document.set_expected_question_count(q_count)
                self.view.set_expected_count(q_count)
                self._update_stats()
                self.view.log_message(f"Expected question count updated to {q_count}. Continuing to edit.", level="INFO")
                return
            # Yes - continue with saving
        
        # Get save path
        save_path = FileService.get_save_csv_path(self.document.file_path)
        if not save_path:
            return
        
        # Save file
        if self.document.save_to_csv(save_path):
            self.view.log_message(f"Successfully saved verified data to: {save_path}")
            self.view.show_info("Save Successful", f"Verified Q&A data saved to:\n{save_path}")
            
            # Ask to open file
            if self.view.ask_yes_no("Open File?", f"CSV saved successfully.\n\nWould you like to open the file?"):
                success, error = FileService.open_file_externally(save_path)
                if not success:
                    self.view.show_warning(
                        "Open File Error",
                        f"Could not automatically open the file.\nPlease navigate to it manually:\n{save_path}\n\nError: {error}"
                    )
        else:
            self.view.show_error("Save Error", "Failed to save the CSV file.")
    
    def paragraph_selection_changed(self) -> None:
        """Handle paragraph selection changes."""
        # Update action panel state based on selection
        has_selection = len(self.view.get_selected_indices()) > 0
        self.view.enable_editing_actions(has_selection)
    
    def change_role_requested(self, new_role: ParaRole) -> None:
        """
        Handle role change requests.
        
        Args:
            new_role: New role to assign
        """
        selected_indices = self.view.get_selected_indices()
        if not selected_indices:
            self.view.show_warning("No Selection", "Please select one or more paragraphs to change their role.")
            return
        
        self.view.log_message(f"Changing role to {new_role.name} for {len(selected_indices)} paragraph(s).")
        
        needs_renumber = False
        for idx in selected_indices:
            if self.document.change_paragraph_role(idx, new_role):
                needs_renumber = True
        
        if needs_renumber:
            self.document.renumber_questions()
            
        # Refresh UI
        self.view.display_paragraphs(self.document.paragraphs)
        self._update_stats()
    
    def merge_up_requested(self) -> None:
        """Handle merge up requests."""
        selected_indices = self.view.get_selected_indices()
        if not selected_indices:
            self.view.show_warning(
                "No Selection", 
                "Please select paragraph(s) to merge into the preceding answer block."
            )
            return
        
        self.view.log_message(f"Attempting to merge {len(selected_indices)} paragraph(s) into previous answer.")
        
        needs_renumber = False
        merged_count = 0
        
        # Process in order (sort indices)
        for idx in sorted(selected_indices):
            if idx == 0:
                self.view.log_message(f"Cannot merge up paragraph at index 0.", level="WARNING")
                continue  # Cannot merge the very first paragraph
            
            if self.document.merge_paragraph_up(idx):
                needs_renumber = True
                merged_count += 1
        
        if merged_count == 0:
            self.view.show_info("Merge", "No paragraphs could be merged. Please ensure the selected paragraphs have a preceding question or answer.")
        elif needs_renumber:
            self.document.renumber_questions()
        
        # Refresh UI
        self.view.display_paragraphs(self.document.paragraphs)
        self._update_stats()
    
    def set_expected_count_requested(self) -> None:
        """Handle set expected count requests."""
        try:
            new_count = int(self.view.get_expected_count())
            if new_count <= 0:
                self.view.show_warning("Invalid Count", "Please enter a positive number of questions.")
                return
                
            self.document.set_expected_question_count(new_count)
            self.view.log_message(f"Expected question count manually set to {new_count}")
            self._update_stats()
        except ValueError:
            self.view.show_warning("Invalid Input", "Please enter a valid number.")
    
    def exit_requested(self) -> None:
        """Handle application exit requests."""
        logger.info("Exit requested by user")
        self.root.quit()
    
    def _update_stats(self) -> None:
        """Update statistics display."""
        question_count = self.document.get_question_count()
        expected_count = self.document.expected_question_count
        
        # Update progress in UI
        self.view.update_progress(question_count, expected_count)