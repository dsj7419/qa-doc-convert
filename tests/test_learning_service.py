# File: tests/test_learning_service.py
"""
Comprehensive tests for the LearningService, focusing on reliability and recovery.
"""
import pytest
import os
import json
import time
import shutil
import threading
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from services.learning_service import LearningService
from models.paragraph import ParaRole, Paragraph

class TestLearningService:
    """Tests for the LearningService class."""
    
    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create a temporary directory."""
        return tmp_path
    
    @pytest.fixture
    def mock_service(self, temp_dir):
        """Create a mock learning service with test paths."""
        with patch.object(LearningService, '__init__', return_value=None) as init_mock:
            service = LearningService()
            service.user_data_dir = str(temp_dir)
            service.training_data_path = str(temp_dir / "training_data.json")
            service.fine_tuned_model_dir = str(temp_dir / "fine_tuned_model")
            service.checkpoint_dir = str(temp_dir / "training_checkpoints")
            service.training_journal_path = str(temp_dir / "training_journal.json")
            service.onnx_model_path = str(temp_dir / "qa_classifier.onnx")
            service.training_completed = threading.Event()
            service.training_should_stop = False
            service.is_training = False
            service.data_changed = False
            service._log_debug = MagicMock()
            
            # Create directories
            os.makedirs(service.fine_tuned_model_dir, exist_ok=True)
            os.makedirs(service.checkpoint_dir, exist_ok=True)
            
            # Create initial training data
            service.training_data = {
                "question": [{"text": "Sample question?", "source": "test", "timestamp": "2023-01-01T00:00:00"}],
                "answer": [{"text": "Sample answer", "source": "test", "timestamp": "2023-01-01T00:00:00"}],
                "ignore": [{"text": "Sample ignore", "source": "test", "timestamp": "2023-01-01T00:00:00"}]
            }
            
            # Save initial training data
            with open(service.training_data_path, 'w') as f:
                json.dump(service.training_data, f)
            
            return service
    
    def test_validate_and_fix_training_data(self, mock_service):
        """Test validation and fixing of training data."""
        # Break the training data structure
        mock_service.training_data = {
            "question": None,  # Invalid value
            # Missing "answer" key
            "ignore": []
        }
        
        # Run validation
        result = mock_service._validate_and_fix_training_data()
        
        # Check that structure was fixed
        assert "question" in mock_service.training_data
        assert isinstance(mock_service.training_data["question"], list)
        assert "answer" in mock_service.training_data
        assert isinstance(mock_service.training_data["answer"], list)
        assert "ignore" in mock_service.training_data
        assert isinstance(mock_service.training_data["ignore"], list)
        
        # Check examples were added if total count was 0
        total_examples = sum(len(examples) for _, examples in mock_service.training_data.items())
        assert total_examples > 0
        assert result is True
    
    def test_graceful_stop_training(self, mock_service):
        """Test graceful stopping of training."""
        # Set up mock thread
        mock_thread = MagicMock()
        mock_service.training_thread = mock_thread
        mock_service.is_training = True
        
        # Define a function to simulate the training thread
        def simulate_training_thread():
            # Wait for stop signal
            for _ in range(50):  # Wait up to 5 seconds
                if mock_service.training_should_stop:
                    mock_service.training_completed.set()
                    return
                time.sleep(0.1)
        
        # Start the simulated training thread
        real_thread = threading.Thread(target=simulate_training_thread)
        real_thread.daemon = True
        real_thread.start()
        
        # Call the method to stop training
        result = mock_service.gracefully_stop_training()
        
        # Verify training is marked as complete
        assert result is True
        assert mock_service.training_completed.is_set()
    
    def test_journal_creation_and_recovery(self, mock_service):
        """Test journal creation and recovery."""
        # Create a mock checkpoint
        checkpoint_path = os.path.join(mock_service.checkpoint_dir, "checkpoint-100")
        os.makedirs(checkpoint_path, exist_ok=True)
        
        # Create a mock trainer_state.json
        state_json = {
            "epoch": 2.5,
            "global_step": 100,
            "best_metric": 0.85
        }
        with open(os.path.join(checkpoint_path, "trainer_state.json"), 'w') as f:
            json.dump(state_json, f)
        
        # Create a journal entry
        mock_service._update_training_journal(
            "in_progress", 
            checkpoint=checkpoint_path,
            epoch=2.5,
            batch=100
        )
        
        # Verify journal was created
        assert os.path.exists(mock_service.training_journal_path)
        
        # Read the journal
        with open(mock_service.training_journal_path, 'r') as f:
            journal = json.load(f)
        
        assert journal["status"] == "in_progress"
        assert journal["last_checkpoint"] == checkpoint_path
        assert journal["epoch"] == 2.5
        assert journal["batch"] == 100
        
        # Reset service attributes
        mock_service.recovery_needed = False
        mock_service.recovery_checkpoint = None
        
        # Now initialize training state which should detect recovery
        mock_service._initialize_training_state()
        
        # Verify recovery was detected
        assert mock_service.recovery_needed
        assert mock_service.recovery_checkpoint == checkpoint_path
    
    def test_checkpoint_state_modification(self, mock_service):
        """Test modification of checkpoint state for recovery."""
        # Create a mock checkpoint
        checkpoint_path = os.path.join(mock_service.checkpoint_dir, "checkpoint-100")
        os.makedirs(checkpoint_path, exist_ok=True)
        
        # Create a mock trainer_state.json with high epoch that would normally terminate
        state_json = {
            "epoch": 5.0,  # High epoch number that would normally terminate training
            "global_step": 100
        }
        with open(os.path.join(checkpoint_path, "trainer_state.json"), 'w') as f:
            json.dump(state_json, f)
        
        # Call the modification method
        success = mock_service._modify_checkpoint_state(checkpoint_path)
        
        # Verify the method succeeded
        assert success is True
        
        # Read back the state and verify epoch was modified to continue training
        with open(os.path.join(checkpoint_path, "trainer_state.json"), 'r') as f:
            modified_state = json.load(f)
        
        assert modified_state["epoch"] < 5.0
        assert modified_state["global_step"] == 100
    
    def test_collect_training_with_feedback(self, mock_service):
        """Test collecting training examples with feedback."""
        # Create mock paragraphs
        paragraphs = [
            Paragraph(0, "Title", ParaRole.IGNORE),
            Paragraph(1, "What is testing?", ParaRole.QUESTION),
            Paragraph(2, "Testing is the process of evaluating software.", ParaRole.ANSWER),
            Paragraph(3, "What is too short?", ParaRole.QUESTION),
            Paragraph(4, "Short", ParaRole.ANSWER)  # Too short, should be skipped
        ]
        
        # Create a log callback
        log_messages = []
        def log_callback(message, level):
            log_messages.append((message, level))
        
        # Call the method
        result = mock_service.collect_training_data_from_document_with_feedback(
            paragraphs, log_callback
        )
        
        # Verify the result
        assert result is True
        
        # Verify log messages
        assert len(log_messages) > 0
        
        # Verify training data was updated
        # Note: The exact count depends on what was already in training_data and the content
        example_count = sum(len(examples) for role, examples in mock_service.training_data.items())
        assert example_count >= 3  # At least the 3 initial examples
    
    def test_find_latest_checkpoint(self, mock_service):
        """Test finding the latest checkpoint."""
        # Create multiple checkpoints
        os.makedirs(os.path.join(mock_service.checkpoint_dir, "checkpoint-10"), exist_ok=True)
        os.makedirs(os.path.join(mock_service.checkpoint_dir, "checkpoint-50"), exist_ok=True)
        os.makedirs(os.path.join(mock_service.checkpoint_dir, "checkpoint-100"), exist_ok=True)
        
        # Find the latest checkpoint
        latest = mock_service._find_latest_checkpoint(mock_service.checkpoint_dir)
        
        # Verify the latest checkpoint was found
        assert latest is not None
        assert "checkpoint-100" in latest