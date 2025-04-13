"""
Tests for asynchronous operations and recovery features.
"""
import os
import pytest
import threading
import time
from unittest.mock import MagicMock, patch

from models.document import Document
from models.paragraph import Paragraph, ParaRole
from services.analysis_service import AnalysisService
from services.learning_service import LearningService
from services.file_service import FileService
from commands.command_manager import CommandManager
from commands.document_commands import ChangeRoleCommand, MergeParagraphCommand, SetExpectedCountCommand

class TestAsyncOperations:
    """Tests for asynchronous operations."""
    
    @pytest.fixture
    def mock_document(self):
        """Create a mock document."""
        document = Document()
        return document
    
    @pytest.fixture
    def mock_callback(self):
        """Create a mock callback."""
        return MagicMock()
    
    @pytest.fixture
    def sample_paragraphs(self):
        """Sample paragraphs for testing."""
        return [
            "CIVIL PROCEDURE (50 questions)",
            "1. What is jurisdiction?",
            "Answer: It's the power of a court to hear a case.",
            "2. What are the types of jurisdiction?",
            "Personal and subject matter jurisdiction."
        ]
        
    def test_async_file_loading(self, mock_document, mock_callback):
        """Test asynchronous file loading."""
        # First mock the FileService.load_docx_paragraphs_async
        with patch.object(FileService, 'load_docx_paragraphs_async') as mock_load:
            # Then mock the AnalysisService as well since it's used in the callback chain
            with patch('models.document.AnalysisService') as MockAnalysisService:
                # Set up the mock AnalysisService
                mock_analysis_service = MagicMock()
                MockAnalysisService.return_value = mock_analysis_service
                
                # Set up the mock analyze_paragraphs_async method
                mock_analysis_thread = MagicMock()
                mock_analysis_service.analyze_paragraphs_async.return_value = mock_analysis_thread
                
                # Set up the load_docx_paragraphs_async side effect to call its callback
                def load_side_effect(file_path, callback):
                    sample_paragraphs = [
                        "CIVIL PROCEDURE (50 questions)",
                        "1. What is jurisdiction?",
                        "Answer: It's the power of a court to hear a case."
                    ]
                    # Call the callback immediately with sample paragraphs
                    callback(sample_paragraphs, None)
                    return MagicMock()  # Return mock thread
                    
                mock_load.side_effect = load_side_effect
                
                # Set up the analyze_paragraphs_async side effect
                def analyze_side_effect(paragraphs, status_callback, completion_callback):
                    # Simulate analysis results
                    question_indices = {1}  # Index 1 as a question
                    est_count = 1
                    # Call the completion callback
                    completion_callback(question_indices, est_count, None)
                    return mock_analysis_thread
                    
                mock_analysis_service.analyze_paragraphs_async.side_effect = analyze_side_effect
                
                # Start async loading
                mock_document.load_file_async("dummy_path.docx", lambda msg: None, mock_callback)
                
                # Verify the callback was called with success
                mock_callback.assert_called_once_with(True)
    
    def test_async_analysis(self, sample_paragraphs, mock_callback):
        """Test asynchronous paragraph analysis."""
        # Create an analysis service
        analysis_service = AnalysisService()
        
        # Start async analysis
        thread = analysis_service.analyze_paragraphs_async(
            sample_paragraphs,
            lambda msg: None,
            mock_callback
        )
        
        # Wait for the async operation to complete
        thread.join(timeout=5.0)
        
        # Verify the callback was called
        assert mock_callback.called
        
        # Get the arguments passed to the callback
        args, _ = mock_callback.call_args
        
        # Verify we got question indices and an estimated count
        question_indices, est_count, exception = args
        
        # Should identify at least the 2 question paragraphs
        assert len(question_indices) >= 2
        assert 1 in question_indices  # "1. What is jurisdiction?"
        assert 3 in question_indices  # "2. What are the types of jurisdiction?"
        assert exception is None
    
    def test_learning_service_graceful_stop(self):
        """Test graceful stopping of training."""
        learning_service = LearningService()
        
        # Mock the training thread to simulate training
        learning_service.is_training = True
        learning_service.training_thread = MagicMock()
        learning_service.training_thread.is_alive.return_value = True
        
        # Create a simulated training thread that sets training_completed when stop flag is set
        def simulated_thread():
            time.sleep(0.1)  # Small delay to simulate work
            if learning_service.training_should_stop:
                learning_service.training_completed.set()
                
        threading.Thread(target=simulated_thread).start()
        
        # Try to stop gracefully
        result = learning_service.gracefully_stop_training()
        
        # Verify it stopped gracefully
        assert result is True
        assert learning_service.training_completed.is_set()

class TestCommandManager:
    """Tests for the command manager."""
    
    @pytest.fixture
    def command_manager(self):
        """Create a command manager."""
        return CommandManager()
    
    @pytest.fixture
    def document(self):
        """Create a document with sample paragraphs."""
        document = Document()
        document.paragraphs = [
            Paragraph(0, "Header", ParaRole.UNDETERMINED),
            Paragraph(1, "Question 1?", ParaRole.UNDETERMINED),
            Paragraph(2, "Answer 1", ParaRole.UNDETERMINED),
            Paragraph(3, "Question 2?", ParaRole.UNDETERMINED),
            Paragraph(4, "Answer 2", ParaRole.UNDETERMINED)
        ]
        return document
    
    def test_change_role_command(self, command_manager, document):
        """Test change role command."""
        # Initial state
        assert document.paragraphs[1].role == ParaRole.UNDETERMINED
        
        # Create and execute command
        command = ChangeRoleCommand(document, {1}, ParaRole.QUESTION)
        command_manager.execute(command)
        
        # Verify role was changed
        assert document.paragraphs[1].role == ParaRole.QUESTION
        
        # Undo
        assert command_manager.undo()
        
        # Verify role was restored
        assert document.paragraphs[1].role == ParaRole.UNDETERMINED
        
        # Redo
        assert command_manager.redo()
        
        # Verify role was changed again
        assert document.paragraphs[1].role == ParaRole.QUESTION
    
    def test_merge_paragraph_command(self, command_manager, document):
        """Test merge paragraph command."""
        # Set up initial state
        document.paragraphs[1].role = ParaRole.QUESTION
        document.paragraphs[1].q_num = 1
        document.paragraphs[2].role = ParaRole.ANSWER
        document.paragraphs[2].q_num = 1
        document.paragraphs[3].role = ParaRole.UNDETERMINED
        
        # Create and execute command
        command = MergeParagraphCommand(document, {3})
        command_manager.execute(command)
        
        # Verify paragraph was merged
        assert document.paragraphs[3].role == ParaRole.ANSWER
        assert document.paragraphs[3].q_num == 1
        
        # Undo
        assert command_manager.undo()
        
        # Verify role was restored
        assert document.paragraphs[3].role == ParaRole.UNDETERMINED
        assert document.paragraphs[3].q_num is None
    
    def test_set_expected_count_command(self, command_manager, document):
        """Test set expected count command."""
        # Initial state
        document.expected_question_count = 10
        
        # Create and execute command
        command = SetExpectedCountCommand(document, 20)
        command_manager.execute(command)
        
        # Verify count was changed
        assert document.expected_question_count == 20
        
        # Undo
        assert command_manager.undo()
        
        # Verify count was restored
        assert document.expected_question_count == 10