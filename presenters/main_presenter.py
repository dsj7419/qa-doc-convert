"""
Main presenter for handling application logic.
"""
from datetime import datetime
import logging
import os
from typing import Optional

from models.document import Document
from models.paragraph import ParaRole
from services.file_service import FileService
from ui.interfaces import IMainWindowView
from utils.config_manager import ConfigManager
from services.learning_service import LearningService

logger = logging.getLogger(__name__)

class MainPresenter:
    """Main presenter for the application."""
    
    def __init__(self, view: IMainWindowView, document: Document, root, config_manager: Optional[ConfigManager] = None):
        """
        Initialize the presenter.
        
        Args:
            view: The main window view
            document: The document model
            root: The root Tk object for window management
            config_manager: Configuration manager
        """
        self.view = view
        self.document = document
        self.root = root
        self.config_manager = config_manager or ConfigManager()
        self.learning_service = LearningService()
    
    def initialize(self) -> None:
        """Initialize the presenter."""
        self.view.show_status("Load a DOCX file to begin.")
    
    def load_file_requested(self) -> None:
        """Handle a load file request."""
        # Reset UI state
        self.view.reset_ui()
        self.document = Document(self.config_manager)
        
        # Get file path from dialog
        file_path = FileService.select_docx_file()
        if not file_path:
            return
        
        # Update status and disable UI
        self.view.show_status(f"Loading: {os.path.basename(file_path)}...")
        self.view.log_message(f"Loading file: {file_path}")
        self.view.set_loading_state(True)  # Disable UI during loading
        
        # Define completion callback
        def on_load_complete(success):
            # Re-enable UI
            self.view.set_loading_state(False)
            
            if success:
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
        
        # Load document with a status callback that updates the view
        status_callback = self.view.show_status
        
        # Load and process document asynchronously
        self.document.load_file_async(file_path, status_callback, on_load_complete)
    
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
        questions_data, q_count = self.document.get_qa_data()
        
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
            
            # Collect training data with explicit feedback
            self.view.log_message("Collecting training examples from verified document...", level="INFO")
            before_count = self.learning_service.get_training_stats()['total_examples']
            
            # Check if we have a detailed collection method available
            if hasattr(self.learning_service, 'collect_training_data_from_document_with_feedback'):
                # Use the detailed collection method if available
                self.learning_service.collect_training_data_from_document_with_feedback(
                    self.document.paragraphs,
                    self.view.log_message
                )
            else:
                # Fall back to the standard method
                self.learning_service.collect_training_data_from_document(self.document.paragraphs)
            
            after_count = self.learning_service.get_training_stats()['total_examples']
            examples_added = after_count - before_count
            
            # Provide feedback on examples added
            if examples_added > 0:
                self.view.log_message(f"Added {examples_added} new training examples", level="INFO")
            else:
                self.view.log_message("No new training examples collected", level="INFO")
            
            # Always attempt to train if we have any data, not just changed data
            train_attempt = False
            if self.learning_service.has_enough_data_to_train():
                self.view.log_message("Training AI model with collected examples...", level="INFO")
                
                # Train in background with a callback for logging
                success = self.learning_service.train_model(
                    force=True,  # Force training even if no new data
                    background=True,  # Train in background
                    callback=self.view.log_message  # Pass the log_message function as callback
                )
                
                train_attempt = True
                if success:
                    self.view.log_message("AI model training started in background", level="INFO")
                else:
                    self.view.log_message("Failed to start AI model training - check logs for details", level="WARNING")
            elif examples_added > 0:
                self.view.log_message("Added examples to training data, but not enough to train model yet", level="INFO")
            
            # Show success message with training info
            success_message = f"Verified Q&A data saved to:\n{save_path}"
            if examples_added > 0 and train_attempt:
                success_message += f"\n\nAdded {examples_added} training examples and started AI model training in the background."
            elif examples_added > 0:
                success_message += f"\n\nAdded {examples_added} training examples."
            self.view.show_info("Save Successful", success_message)
            
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

    def save_training_data_requested(self) -> None:
        """Save training data immediately."""
        success = self.learning_service._save_training_data()
        
        if success:
            self.view.show_info(
                "Training Data Saved",
                "Training data has been saved successfully."
            )
        else:
            self.view.show_error(
                "Save Failed",
                "Failed to save training data. Check the logs for details."
            )
    def toggle_manual_training_mode_requested(self) -> None:
        """Toggle manual training mode."""
        # Toggle the mode
        current_mode = self.learning_service.is_manual_training_mode()
        new_mode = not current_mode
        self.learning_service.set_manual_training_mode(new_mode)
        
        # Show confirmation
        if new_mode:
            self.view.show_info(
                "Manual Training Mode Enabled",
                "The AI will now learn ONLY from your manual corrections, not from automatic classifications.\n\n"
                "This ensures higher quality training data."
            )
        else:
            self.view.show_info(
                "Manual Training Mode Disabled",
                "The AI will learn from both your corrections and automatic classifications."
            )

    def show_ai_stats_requested(self) -> None:
        """Show AI training statistics."""
        try:
            self.view.log_message("Gathering AI training statistics...", "INFO")
            
            # Get basic stats from learning service
            stats = self.learning_service.get_training_stats()
            
            # Extract main values with defaults in case keys are missing
            total_examples = stats.get('total_examples', 0)
            by_class = stats.get('by_class', {})
            has_model = stats.get('has_model', False)
            
            # Get transformer and ONNX status
            transformers_available = stats.get('transformers_available', False)
            onnx_available = stats.get('onnx_available', False)
            ai_available = stats.get('ai_available', False)
            
            # Format data for better readability
            question_count = by_class.get('question', 0)
            answer_count = by_class.get('answer', 0)
            ignore_count = by_class.get('ignore', 0)
            
            # Add model details
            model_path = stats.get('model_path', 'Unknown')
            onnx_path = stats.get('onnx_path', 'Unknown')
            user_data_dir = stats.get('user_data_dir', 'Unknown')
            data_changed = stats.get('data_changed', False)
            is_training = stats.get('is_training', False)
            manual_mode = stats.get('manual_training_mode', True)
            
            # Check model file existence explicitly
            if has_model:
                model_status = "✓ Model exists"
                if os.path.exists(onnx_path):
                    try:
                        model_size = os.path.getsize(onnx_path) / (1024 * 1024)  # Convert to MB
                        model_status += f" ({model_size:.2f} MB)"
                        last_modified = datetime.fromtimestamp(os.path.getmtime(onnx_path))
                        model_status += f"\n  Last updated: {last_modified.strftime('%Y-%m-%d %H:%M:%S')}"
                    except:
                        pass
            else:
                model_status = "✗ Model does not exist"
            
            # AI capability summary
            capability_status = []
            if transformers_available and onnx_available:
                capability_status.append("✓ Full AI capability (Transformers + ONNX)")
            elif transformers_available:
                capability_status.append("⚠ Partial AI capability (Transformers only, no ONNX)")
            elif onnx_available:
                capability_status.append("⚠ Partial AI capability (ONNX only, no Transformers)")
            else:
                capability_status.append("✗ AI capability unavailable (requires Transformers and ONNX)")
            
            # Training status
            if is_training:
                training_status = "⟳ Training in progress"
                if 'training_progress' in stats:
                    progress = stats['training_progress']
                    if isinstance(progress, dict) and 'status' in progress and 'message' in progress:
                        training_status += f"\n  Status: {progress['status']}"
                        training_status += f"\n  Message: {progress['message']}"
            elif data_changed:
                training_status = "⚠ Training data has changed since last training"
            else:
                training_status = "✓ Training data is up to date"
                
            # Training mode
            mode_status = "Manual training mode" if manual_mode else "Automatic training mode"
            
            # Create formatted message
            message = (
                f"AI Training Statistics\n"
                f"======================================\n\n"
                f"Training Data:\n"
                f"  Total examples: {total_examples}\n"
                f"  Questions: {question_count}\n"
                f"  Answers: {answer_count}\n"
                f"  Ignore: {ignore_count}\n\n"
                f"Model Status:\n"
                f"  {model_status}\n\n"
                f"AI Capability:\n"
                f"  {capability_status[0]}\n"
                f"  {mode_status}\n\n"
                f"Training Status:\n"
                f"  {training_status}\n\n"
                f"File Locations:\n"
                f"  User data directory:\n    {user_data_dir}\n"
                f"  Model directory:\n    {model_path}\n"
                f"  ONNX model path:\n    {onnx_path}"
            )
            
            # Log success and show the info dialog
            self.view.log_message("AI training statistics gathered successfully", "INFO")
            self.view.show_info("AI Training Stats", message)
            
        except Exception as e:
            # Log the error for debugging
            error_message = f"Error showing AI training stats: {str(e)}"
            self.view.log_message(error_message, "ERROR")
            logger.error(error_message, exc_info=True)
            
            # Show error to user
            self.view.show_error(
                "Error Showing Stats", 
                f"An error occurred while gathering AI training statistics:\n\n{str(e)}\n\nPlease check the log for details."
            )

    def view_training_examples_requested(self) -> None:
        """Show a sample of training examples."""
        stats = self.learning_service.get_training_stats()
        examples = self.learning_service.get_sample_training_examples(5)
        
        if not examples or sum(len(role_examples) for role, role_examples in examples.items()) == 0:
            self.view.show_info(
                "No Training Examples",
                "No training examples found in the database."
            )
            return
        
        # Build message with examples
        message = "Sample Training Examples:\n\n"
        
        for role, role_examples in examples.items():
            if not role_examples:
                continue
                
            message += f"--- {role.upper()} Examples ({stats['by_class'].get(role, 0)} total) ---\n"
            for i, example in enumerate(role_examples):
                if i >= 3:  # Limit to 3 examples per role
                    message += f"... and {len(role_examples) - 3} more\n"
                    break
                    
                text = example[:100] + "..." if len(example) > 100 else example
                message += f"{i+1}. {text}\n"
            message += "\n"
        
        self.view.show_info("Training Examples", message)

    def collect_examples_now_requested(self) -> None:
        """Collect training examples from the current document."""
        if not self.document.paragraphs:
            self.view.show_warning(
                "No Document Loaded",
                "No document is loaded. Please load a document first."
            )
            return
        
        # Count paragraphs with roles
        total_paragraphs = len(self.document.paragraphs)
        role_assigned = sum(1 for p in self.document.paragraphs if p.role != ParaRole.UNDETERMINED)
        
        self.view.log_message(f"Processing {total_paragraphs} paragraphs ({role_assigned} with roles assigned)...", level="INFO")
        
        # Direct call to collect training data with verbose logging
        before_count = self.learning_service.get_training_stats()['total_examples']
        
        # Force saving to a specific path with detailed feedback
        success = self.learning_service.collect_training_data_from_document_with_feedback(
            self.document.paragraphs, 
            self.view.log_message
        )
        
        after_count = self.learning_service.get_training_stats()['total_examples']
        examples_added = after_count - before_count
        
        if success:
            if examples_added > 0:
                self.view.show_info(
                    "Examples Collected",
                    f"Successfully collected {examples_added} new training examples."
                )
            else:
                self.view.show_info(
                    "No New Examples",
                    "No new examples were collected. This may be because:\n"
                    "- All paragraphs were already in the training data\n"
                    "- No paragraphs had roles assigned\n"
                    "- Paragraphs were too short to be used as examples"
                )
        else:
            self.view.show_error(
                "Collection Failed",
                "Failed to collect training examples. Check the logs for details."
            )

    def force_ai_training_requested(self) -> None:
        """Force AI model training."""
        # Validate and fix training data
        self.learning_service._validate_and_fix_training_data()
        
        # Always force training, bypassing the "has enough data" check
        success = self.learning_service.train_model(force=True)
        
        if success:
            self.view.show_info(
                "Training Successful",
                "The AI model has been successfully trained with your corrections."
            )
            
            # Refresh stats after successful training
            self.show_ai_stats_requested()
        else:
            self.view.show_error(
                "Training Failed",
                "Failed to train the AI model. Check the log for details."
            )

    def diagnose_ai_training_requested(self) -> None:
        """Diagnose and fix AI training issues."""
        self.view.log_message("Running AI training diagnostics...", level="INFO")
        
        # Get current stats
        stats = self.learning_service.get_training_stats()
        initial_has_model = stats['has_model']
        
        # Validate and fix data
        self.learning_service._validate_and_fix_training_data()
        
        # Force save training data
        self.learning_service._save_training_data()
        
        # Force training regardless of "enough data" check
        success = self.learning_service.train_model(force=True)
        
        if success:
            self.view.show_info(
                "Diagnostics Successful",
                "AI diagnostics completed and training succeeded.\n\n"
                f"Model file: {stats['model_path']}\n"
                f"Training examples: {stats['total_examples']}"
            )
        else:
            self.view.show_error(
                "Diagnostics Failed",
                "AI diagnostics ran but training still failed.\n\n"
                "Please check the debug log for details."
            )
        
        # Show updated stats
        self.show_ai_stats_requested()

    def reset_and_use_ai_requested(self) -> None:
        """Reset configuration and force use of AI analyzer."""
        # Update config to use AI analyzer
        self.config_manager.update_config({'analysis': {'analyzer_type': 'ai'}})
        
        # Force retrain the model
        if self.learning_service.has_enough_data_to_train():
            success = self.learning_service.train_model(force=True)
            if success:
                self.view.log_message("AI model has been retrained", level="INFO")
            else:
                self.view.log_message("Failed to retrain AI model", level="WARNING")
        
        # Show confirmation dialog
        self.view.show_info(
            "AI Analyzer Enabled",
            "AI analyzer has been enabled in the configuration.\n\n"
            "Please reload your document to apply this change."
        )

    def reset_all_training_data_requested(self) -> None:
        """Reset all training data and the model."""
        success = self.learning_service.reset_all_training_data()
        
        if success:
            self.view.show_info(
                "Training Data Reset",
                "All training data has been cleared. The AI will now learn only from your new corrections."
            )
        else:
            self.view.show_error(
                "Reset Failed",
                "Failed to reset training data. Check logs for details."
            )

    def verify_file_permissions_requested(self) -> None:
        """Verify file permissions for training data."""
        directory = self.learning_service.user_data_dir
        training_file = self.learning_service.training_data_path
        model_dir = self.learning_service.fine_tuned_model_dir
        onnx_file = self.learning_service.onnx_model_path
        
        # Check directory
        dir_exists = os.path.exists(directory)
        dir_writable = os.access(directory, os.W_OK) if dir_exists else False
        
        # Check training data file
        training_exists = os.path.exists(training_file)
        training_readable = os.access(training_file, os.R_OK) if training_exists else False
        training_writable = os.access(training_file, os.W_OK) if training_exists else False
        training_size = os.path.getsize(training_file) if training_exists else 0
        
        # Check model directory
        model_exists = os.path.exists(model_dir)
        model_readable = os.access(model_dir, os.R_OK) if model_exists else False
        model_writable = os.access(model_dir, os.W_OK) if model_exists else False
        
        # Check ONNX file
        onnx_exists = os.path.exists(onnx_file)
        onnx_readable = os.access(onnx_file, os.R_OK) if onnx_exists else False
        onnx_size = os.path.getsize(onnx_file) if onnx_exists else 0
        
        # Format message
        message = (
            f"Data Directory: {directory}\n"
            f"  Exists: {dir_exists}\n"
            f"  Writable: {dir_writable}\n\n"
            f"Training Data File: {training_file}\n"
            f"  Exists: {training_exists}\n"
            f"  Readable: {training_readable}\n"
            f"  Writable: {training_writable}\n"
            f"  Size: {training_size} bytes\n\n"
            f"Model Directory: {model_dir}\n"
            f"  Exists: {model_exists}\n"
            f"  Readable: {model_readable}\n"
            f"  Writable: {model_writable}\n\n"
            f"ONNX Model File: {onnx_file}\n"
            f"  Exists: {onnx_exists}\n"
            f"  Readable: {onnx_readable}\n"
            f"  Size: {onnx_size} bytes\n"
        )
        
        # Try to create test files
        try:
            test_file = os.path.join(directory, "test_write.tmp")
            with open(test_file, 'w') as f:
                f.write("Test")
            os.remove(test_file)
            message += "\nWrite test: PASSED"
        except Exception as e:
            message += f"\nWrite test: FAILED - {str(e)}"
        
        self.view.show_info("File Permissions", message)

    def open_data_dir_requested(self) -> None:
        """Open the data directory in file explorer."""
        self.learning_service.open_data_directory()
    
    def set_analyzer_type(self, analyzer_type: str) -> None:
        """
        Set the analyzer type.
        
        Args:
            analyzer_type: Type of analyzer to use ('auto', 'heuristic', or 'ai')
        """
        if analyzer_type not in ['auto', 'heuristic', 'ai']:
            self.view.show_error("Invalid Analyzer", f"'{analyzer_type}' is not a valid analyzer type.")
            return
            
        # Update config
        self.config_manager.update_config({'analysis': {'analyzer_type': analyzer_type}})
        self.view.log_message(f"Set analyzer type to: {analyzer_type}")
    
    def paragraph_selection_changed(self) -> None:
        """Handle paragraph selection changes."""
        # Update action panel state based on selection
        has_selection = len(self.view.get_selected_indices()) > 0
        self.view.enable_editing_actions(has_selection)
    
    def change_role_requested(self, new_role: ParaRole) -> None:
        """Handle role change requests."""
        selected_indices = self.view.get_selected_indices()
        if not selected_indices:
            self.view.show_warning("No Selection", "Please select one or more paragraphs to change their role.")
            return
        
        self.view.log_message(f"Changing role to {new_role.name} for {len(selected_indices)} paragraph(s).")
        
        # Track paragraphs before changes
        if not hasattr(self, '_initial_roles'):
            self._initial_roles = {}
        
        # Record initial roles of selected paragraphs
        for idx in selected_indices:
            if 0 <= idx < len(self.document.paragraphs):
                # Only record if not already recorded
                if idx not in self._initial_roles:
                    self._initial_roles[idx] = self.document.paragraphs[idx].role
        
        # Now make the changes
        needs_renumber = False
        for idx in selected_indices:
            if self.document.change_paragraph_role(idx, new_role):
                needs_renumber = True
        
        # Add training examples ONLY for paragraphs where the role changed from the initial analysis
        examples_added = 0
        for idx in selected_indices:
            if idx in self._initial_roles and self._initial_roles[idx] != new_role:
                # This was a manual correction - add it to training
                if self.learning_service.add_training_example(
                    self.document.paragraphs[idx].text, 
                    new_role
                ):
                    examples_added += 1
                    
        if examples_added > 0:
            self.view.log_message(f"Added {examples_added} examples from your corrections", level="INFO")
        
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

    def show_training_progress(self) -> None:
        """Show a message about current training progress."""
        stats = self.learning_service.get_training_stats()
        
        # Calculate examples added in this session
        current_total = stats['total_examples']
        initial_total = getattr(self, '_initial_example_count', 0)
        if not hasattr(self, '_initial_example_count'):
            self._initial_example_count = current_total
            initial_total = current_total
        
        examples_added = current_total - initial_total
        
        message = (
            f"AI Training Progress:\n\n"
            f"Training examples: {current_total}\n"
            f"Examples added this session: {examples_added}\n\n"
            f"Questions: {stats['by_class'].get('question', 0)}\n"
            f"Answers: {stats['by_class'].get('answer', 0)}\n"
            f"Ignore: {stats['by_class'].get('ignore', 0)}\n\n"
            f"The AI model will automatically retrain when you save the document."
        )
        
        self.view.show_info("Training Progress", message)
    
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
        
        # Check if training is in progress
        try:
            is_training = False
            if hasattr(self, 'learning_service'):
                stats = self.learning_service.get_training_stats()
                is_training = stats.get('is_training', False)
                
            if is_training:
                # Ask user if they want to wait for training to complete
                response = self.view.ask_yes_no_cancel(
                    "Training in Progress",
                    "AI model training is currently in progress.\n\n"
                    "• Yes: Wait for training to complete (recommended)\n"
                    "• No: Stop training and exit now\n"
                    "• Cancel: Return to application\n\n"
                    "Note: Stopping training prematurely may result in an incomplete model."
                )
                
                if response is None:  # Cancel - abort exit
                    self.view.log_message("Exit cancelled - training will continue", "INFO")
                    return
                elif response is True:  # Yes - wait for training
                    self.view.log_message("Waiting for training to complete before exit...", "INFO")
                    self.view.set_loading_state(True)  # Show loading state
                    
                    # Get the training thread
                    training_thread = self.learning_service.training_thread if hasattr(self.learning_service, 'training_thread') else None
                    
                    # Wait for training thread to complete with timeout
                    if training_thread and training_thread.is_alive():
                        training_thread.join(timeout=10.0)  # Wait up to 10 seconds
                    
                    self.view.set_loading_state(False)
                    
                    # If still training after timeout, ask again
                    if training_thread and training_thread.is_alive():
                        force_exit = self.view.ask_yes_no(
                            "Training Still in Progress",
                            "Training is taking longer than expected.\n\n"
                            "Do you want to force exit now? This will leave the model in an incomplete state."
                        )
                        if not force_exit:
                            self.view.log_message("Exit cancelled - training will continue", "INFO")
                            return
                        
                        # Force stop training
                        if hasattr(self.learning_service, 'gracefully_stop_training'):
                            self.learning_service.gracefully_stop_training()
                else:  # No - stop training and exit
                    self.view.log_message("Stopping training and exiting...", "INFO")
                    if hasattr(self.learning_service, 'gracefully_stop_training'):
                        self.learning_service.gracefully_stop_training()
                        # Wait a moment for the stop to take effect
                        self.learning_service.training_completed.wait(timeout=1.0)
            
            # Ensure UI is in normal state before exiting
            self.view.set_loading_state(False)
            
            # Signal to the main thread we're actually exiting now
            self.view.log_message("Application exiting now", "INFO")
            
            # Force destroy - stronger than quit() for handling stuck threads
            self.root.after(100, self.root.destroy)
            
        except Exception as e:
            logger.error(f"Error during exit handling: {e}", exc_info=True)
            # Exit anyway - force destroy after a brief delay
            self.root.after(100, self.root.destroy)
    
    def _update_stats(self) -> None:
        """Update statistics display."""
        question_count = self.document.get_question_count()
        expected_count = self.document.expected_question_count
        
        # Update progress in UI
        self.view.update_progress(question_count, expected_count)