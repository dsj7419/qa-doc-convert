# File: tests/test_async_edge_cases.py
"""
Tests for asynchronous operation edge cases and error handling.
"""
import pytest
from unittest.mock import MagicMock, patch
import threading
import time

from models.document import Document
from services.analysis_service import AnalysisService
from services.file_service import FileService
from services.learning_service import LearningService

class TestAsyncEdgeCases:
    """Test suite for async edge cases."""
    
    def test_document_async_load_cancel(self):
        """Test cancellation of document loading."""
        # Create document
        document = Document()
        
        # Create mock callbacks
        status_callback = MagicMock()
        completion_callback = MagicMock()
        
        # Mock file service to simulate delay
        with patch.object(FileService, 'load_docx_paragraphs_async') as mock_load:
            # Set up mock to delay callback
            def delay_callback(file_path, callback):
                thread = threading.Thread(target=lambda: None)
                thread.start()
                return thread
                
            mock_load.side_effect = delay_callback
            
            # Start loading
            document.load_file_async("dummy_path.docx", status_callback, completion_callback)
            
            # Cancel loading immediately
            document.cancel_loading()
            
            # Verify callbacks
            status_callback.assert_called()
            # Note: completion_callback might not be called since we cancelled before the delay finished
    
    def test_analysis_service_with_failed_analyzer(self):
        """Test analysis service with an analyzer that fails."""
        # Create analysis service
        analysis_service = AnalysisService()
        
        # Create mock analyzer that raises exception
        mock_analyzer = MagicMock()
        mock_analyzer.analyze.side_effect = Exception("Test analyzer failure")
        analysis_service.analyzer = mock_analyzer
        
        # Create callbacks
        status_callback = MagicMock()
        completion_callback = MagicMock()
        
        # Run async analysis
        thread = analysis_service.analyze_paragraphs_async(
            ["Test paragraph"], 
            status_callback, 
            completion_callback
        )
        
        # Wait for thread to complete
        thread.join(timeout=1.0)
        
        # Verify completion callback was called with empty set and no exception
        # The service should catch exceptions and provide a graceful fallback
        completion_callback.assert_called()
        args = completion_callback.call_args[0]
        assert args[2] is None  # No exception due to internal handling
    
    def test_learning_service_save_data_race(self, tmp_path):
        """Test race conditions when saving training data."""
        # This test simulates concurrent save operations to detect any race conditions
        
        with patch.object(LearningService, '__init__', return_value=None) as init_mock:
            service = LearningService()
            service.user_data_dir = str(tmp_path)
            service.training_data_path = str(tmp_path / "training_data.json")
            service._log_debug = MagicMock()
            
            # Initialize training data
            service.training_data = {
                "question": [{"text": "Sample question?", "source": "test", "timestamp": "2023-01-01T00:00:00"}],
                "answer": [{"text": "Sample answer", "source": "test", "timestamp": "2023-01-01T00:00:00"}],
                "ignore": [{"text": "Sample ignore", "source": "test", "timestamp": "2023-01-01T00:00:00"}]
            }
            
            # Create directory
            import os
            os.makedirs(service.user_data_dir, exist_ok=True)
            
            # Create multiple threads that try to save concurrently
            threads = []
            for i in range(5):
                thread = threading.Thread(
                    target=service._save_training_data
                )
                threads.append(thread)
            
            # Start all threads
            for thread in threads:
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join(timeout=2.0)
            
            # Verify the file was created and is valid JSON
            assert os.path.exists(service.training_data_path)
            
            # Check file is valid JSON
            import json
            with open(service.training_data_path, 'r') as f:
                data = json.load(f)
            
            # Check structure is intact
            assert "question" in data
            assert "answer" in data
            assert "ignore" in data