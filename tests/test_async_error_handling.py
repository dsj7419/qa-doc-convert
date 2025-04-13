# tests/test_async_error_handling.py

import pytest
from unittest.mock import MagicMock, patch
import threading
import time

from models.document import Document
from services.file_service import FileService
from services.analysis_service import AnalysisService

class TestAsyncErrorHandling:
    """Tests for async error handling."""
    
    @pytest.fixture
    def mock_document(self):
        """Create a mock document."""
        return Document()
    
    @pytest.fixture
    def mock_status_callback(self):
        """Create a mock status callback."""
        return MagicMock()
    
    @pytest.fixture
    def mock_completion_callback(self):
        """Create a mock completion callback."""
        return MagicMock()
    
    def test_file_loading_error_handling(self, mock_document, mock_status_callback, mock_completion_callback):
        """Test error handling in file loading."""
        # Mock file service to simulate an error
        with patch.object(FileService, 'load_docx_paragraphs_async') as mock_load:
            # Set up mock to call callback with an error
            def call_with_error(file_path, callback):
                error = Exception("Simulated file error")
                # Call callback with error
                callback(None, error)
                return threading.Thread()
                
            mock_load.side_effect = call_with_error
            
            # Start async loading
            mock_document.load_file_async("dummy_path.docx", mock_status_callback, mock_completion_callback)
            
            # Verify callbacks were called appropriately
            mock_status_callback.assert_called()
            mock_completion_callback.assert_called_once_with(False)
    
    def test_analysis_error_handling(self, mock_status_callback, mock_completion_callback):
        """Test error handling in analysis."""
        # Create analysis service
        analysis_service = AnalysisService()
        
        # Mock analyze method to raise an exception
        with patch.object(analysis_service.analyzer, 'analyze', side_effect=Exception("Analysis error")):
            # Start async analysis
            thread = analysis_service.analyze_paragraphs_async(
                ["Sample paragraph"], 
                mock_status_callback,
                mock_completion_callback
            )
            
            # Wait for thread to complete
            thread.join(timeout=1.0)
            
            # Verify completion callback was called
            mock_completion_callback.assert_called()
            args = mock_completion_callback.call_args[0]
            assert isinstance(args[0], set)  # Empty set
            assert len(args[0]) == 0  # Should be empty
            assert args[1] > 0  # There will be a default estimate
            # The service catches exceptions and provides graceful fallback
            assert args[2] is None  # No error object due to fallback