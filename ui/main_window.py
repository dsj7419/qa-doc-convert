"""
Main application window.
"""
import logging
import tkinter as tk
from tkinter import messagebox, ttk

from models.document import Document
from models.paragraph import ParaRole
from services.file_service import FileService
from ui.components.action_panel import ActionPanel
from ui.components.header_panel import HeaderPanel
from ui.components.log_panel import LogPanel
from ui.components.paragraph_list import ParagraphList
from ui.components.status_bar import StatusBar
from utils.theme import AppTheme

logger = logging.getLogger(__name__)

class MainWindow:
    """Main application window."""
    
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
        
        # Initialize document model
        self.document = Document()
        
        # Build UI
        self._build_ui()
        
        # Initialize components
        self._init_bindings()
    
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
            on_load=self.load_file,
            on_save=self.save_csv
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
            on_mark_question=lambda: self.change_role(ParaRole.QUESTION),
            on_mark_answer=lambda: self.change_role(ParaRole.ANSWER),
            on_mark_ignore=lambda: self.change_role(ParaRole.IGNORE),
            on_merge_up=self.merge_up,
            on_set_expected_count=self.set_expected_count
        )
        self.action_panel.pack(fill=tk.BOTH, expand=True)
        
        # Log Panel - reduced height
        self.log_panel = LogPanel(self.root)
        self.log_panel.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 5))
    
    def _init_bindings(self):
        """Initialize event bindings."""
        # Bind paragraph selection event
        self.para_list.set_selection_callback(self.on_paragraph_selected)
        
        # Set the status update callback
        self.status_callback = self.status_bar.update_status
        
        # Set the log callback
        self.log_callback = self.log_panel.log_message
    
    def on_paragraph_selected(self):
        """Handle paragraph selection events."""
        # Update action panel state based on selection
        self.action_panel.update_selection_state(bool(self.para_list.get_selected_indices()))
    
    def load_file(self):
        """Load a DOCX file for processing."""
        # Clear existing data first
        self.reset_ui()
        
        # Get file path from dialog
        file_path = FileService.select_docx_file()
        if not file_path:
            return
        
        # Update status
        self.status_callback(f"Loading: {os.path.basename(file_path)}...")
        self.log_callback(f"Loading file: {file_path}")
        
        # Load and process document
        if self.document.load_file(file_path, self.status_callback):
            # Update UI with paragraphs
            self.para_list.set_paragraphs(self.document.paragraphs)
            
            # Update expected count in action panel
            self.action_panel.set_expected_count(self.document.expected_question_count)
            
            # Update stats display
            self.update_stats()
            
            # Ready status
            self.status_callback("Ready for verification. Select a paragraph.")
        else:
            messagebox.showerror("Error", "Failed to load or process the document.")
            self.status_callback("Error loading document.")
    
    def reset_ui(self):
        """Reset UI state for new document."""
        self.document = Document()
        self.para_list.clear()
        self.action_panel.reset()
        self.status_callback("Load a DOCX file to begin.")
    
    def update_stats(self):
        """Update statistics display."""
        question_count = self.document.get_question_count()
        expected_count = self.document.expected_question_count
        
        # Update progress in action panel
        self.action_panel.update_progress(question_count, expected_count)
    
    def set_expected_count(self):
        """Set the expected question count from user input."""
        try:
            new_count = int(self.action_panel.get_expected_count())
            if new_count <= 0:
                messagebox.showwarning("Invalid Count", "Please enter a positive number of questions.")
                return
                
            self.document.set_expected_question_count(new_count)
            self.log_callback(f"Expected question count manually set to {new_count}")
            self.update_stats()
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter a valid number.")
    
    def change_role(self, new_role):
        """
        Change the role of selected paragraphs.
        
        Args:
            new_role: New role to assign
        """
        selected_indices = self.para_list.get_selected_indices()
        if not selected_indices:
            messagebox.showwarning("No Selection", "Please select one or more paragraphs to change their role.")
            return
        
        self.log_callback(f"Changing role to {new_role.name} for {len(selected_indices)} paragraph(s).")
        
        needs_renumber = False
        for idx in selected_indices:
            if self.document.change_paragraph_role(idx, new_role):
                needs_renumber = True
        
        if needs_renumber:
            self.document.renumber_questions()
            
        # Refresh UI
        self.para_list.set_paragraphs(self.document.paragraphs)
        self.update_stats()
    
    def multi_change_role(self, new_role):
        """
        Change role for multiple selected paragraphs.
        
        Args:
            new_role: New role to assign
        """
        # This is essentially the same as change_role, but we keep it
        # separate in case we want to add specific multi-selection behavior
        self.change_role(new_role)
    
    def merge_up(self):
        """Merge selected paragraphs into the previous answer block."""
        selected_indices = self.para_list.get_selected_indices()
        if not selected_indices:
            messagebox.showwarning(
                "No Selection", 
                "Please select paragraph(s) to merge into the preceding answer block."
            )
            return
        
        self.log_callback(f"Attempting to merge {len(selected_indices)} paragraph(s) into previous answer.")
        
        needs_renumber = False
        merged_count = 0
        
        # Process in order (sort indices)
        for idx in sorted(selected_indices):
            if idx == 0:
                self.log_callback(f"Cannot merge up paragraph at index 0.", level="WARNING")
                continue  # Cannot merge the very first paragraph
            
            if self.document.merge_paragraph_up(idx):
                needs_renumber = True
                merged_count += 1
        
        if merged_count == 0:
            messagebox.showinfo("Merge", "No paragraphs could be merged. Please ensure the selected paragraphs have a preceding question or answer.")
        elif needs_renumber:
            self.document.renumber_questions()
        
        # Refresh UI
        self.para_list.set_paragraphs(self.document.paragraphs)
        self.update_stats()
    
    def save_csv(self):
        """Save the verified Q&A pairs to a CSV file."""
        if not self.document.file_path:
            messagebox.showerror("Error", "No file loaded.")
            return
        
        if not self.document.paragraphs:
            messagebox.showerror("Error", "No paragraph data available.")
            return
        
        self.log_callback("Preparing to save CSV...")
        
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
            
            response = messagebox.askyesnocancel(
                "Question Count Mismatch", 
                message,
                icon=messagebox.WARNING
            )
            
            if response is None:  # Cancel - continue editing
                self.log_callback(f"Save cancelled. Continuing to edit.", level="INFO")
                return
            elif response is False:  # No - update expected count
                self.document.set_expected_question_count(q_count)
                self.action_panel.set_expected_count(q_count)
                self.update_stats()
                self.log_callback(f"Expected question count updated to {q_count}. Continuing to edit.", level="INFO")
                return
            # Yes - continue with saving
        
        # Get save path
        save_path = FileService.get_save_csv_path(self.document.file_path)
        if not save_path:
            return
        
        # Save file
        if self.document.save_to_csv(save_path):
            self.log_callback(f"Successfully saved verified data to: {save_path}")
            messagebox.showinfo("Save Successful", f"Verified Q&A data saved to:\n{save_path}")
            
            # Ask to open file
            if messagebox.askyesno("Open File?", f"CSV saved successfully.\n\nWould you like to open the file?"):
                success, error = FileService.open_file_externally(save_path)
                if not success:
                    messagebox.showwarning(
                        "Open File Error",
                        f"Could not automatically open the file.\nPlease navigate to it manually:\n{save_path}\n\nError: {error}"
                    )
        else:
            messagebox.showerror("Save Error", "Failed to save the CSV file.")

# Import statement at the end to avoid circular imports
import os  # For file operations in load_file