# tests/test_training_recovery.py

import pytest
import os
import json
import time
import threading
from unittest.mock import MagicMock, patch
import shutil

from services.learning_service import LearningService

class TestTrainingRecovery:
    """Tests for training recovery functionality."""
    
    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create a temporary directory."""
        return tmp_path
    
    @pytest.fixture
    def mock_learning_service(self, temp_dir):
        """Create a mock learning service with test directories."""
        with patch.object(LearningService, '__init__', return_value=None):
            service = LearningService()
            service.user_data_dir = str(temp_dir)
            service.training_data_path = str(temp_dir / "training_data.json")
            service.fine_tuned_model_dir = str(temp_dir / "fine_tuned_model")
            service.checkpoint_dir = str(temp_dir / "training_checkpoints")
            service.training_journal_path = str(temp_dir / "training_journal.json")
            service.training_completed = threading.Event()
            service._log_debug = MagicMock()
            
            # Create required directories
            os.makedirs(service.fine_tuned_model_dir, exist_ok=True)
            os.makedirs(service.checkpoint_dir, exist_ok=True)
            
            # Create a mock training data file
            training_data = {
                "question": [{"text": "Sample question?", "source": "test", "timestamp": "2023-01-01T00:00:00"}],
                "answer": [{"text": "Sample answer", "source": "test", "timestamp": "2023-01-01T00:00:00"}],
                "ignore": [{"text": "Sample ignore", "source": "test", "timestamp": "2023-01-01T00:00:00"}]
            }
            with open(service.training_data_path, 'w') as f:
                json.dump(training_data, f)
            
            return service
    
    def test_journal_creation_and_update(self, mock_learning_service):
        """Test journal creation and updating."""
        # Call the method
        mock_learning_service._update_training_journal("in_progress", checkpoint="test_checkpoint", epoch=1, batch=10)
        
        # Verify the journal was created
        assert os.path.exists(mock_learning_service.training_journal_path)
        
        # Check contents
        with open(mock_learning_service.training_journal_path, 'r') as f:
            journal = json.load(f)
            
        assert journal['status'] == "in_progress"
        assert journal['last_checkpoint'] == "test_checkpoint"
        assert journal['epoch'] == 1
        assert journal['batch'] == 10
    
    def test_checkpoint_preservation(self, mock_learning_service):
        """Test preservation of checkpoint path during interruption."""
        # Create an initial journal with a checkpoint
        mock_learning_service._update_training_journal("in_progress", checkpoint="original_checkpoint", epoch=1, batch=10)
        
        # Update with interrupted status but no checkpoint
        mock_learning_service._update_training_journal("interrupted")
        
        # Check that the original checkpoint path was preserved
        with open(mock_learning_service.training_journal_path, 'r') as f:
            journal = json.load(f)
            
        assert journal['status'] == "interrupted"
        assert journal['last_checkpoint'] == "original_checkpoint"
    
    def test_initialize_training_state_with_recovery(self, mock_learning_service, monkeypatch):
        """Test initializing training state with recovery needed."""
        # Create a mock checkpoint directory
        checkpoint_path = os.path.join(mock_learning_service.checkpoint_dir, "checkpoint-100")
        os.makedirs(checkpoint_path, exist_ok=True)
        
        # Create a fake trainer_state.json
        with open(os.path.join(checkpoint_path, "trainer_state.json"), 'w') as f:
            json.dump({"epoch": 2.0, "global_step": 100}, f)
        
        # Create journal with in-progress status and checkpoint
        mock_learning_service._update_training_journal("in_progress", checkpoint=checkpoint_path, epoch=2, batch=100)
        
        # Mock methods used in _initialize_training_state
        mock_learning_service._find_latest_checkpoint = MagicMock(return_value=checkpoint_path)
        mock_learning_service.has_enough_data_to_train = MagicMock(return_value=True)
        mock_learning_service.train_model = MagicMock()
        
        # Call the method
        mock_learning_service._initialize_training_state()
        
        # Check if recovery_needed was set
        assert hasattr(mock_learning_service, 'recovery_needed')
        assert mock_learning_service.recovery_needed
        assert mock_learning_service.recovery_checkpoint == checkpoint_path