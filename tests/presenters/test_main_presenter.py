"""
Unit tests for the MainPresenter class.
"""
import pytest
from unittest.mock import MagicMock, patch

from models.document import Document
from models.paragraph import ParaRole, Paragraph
from presenters.main_presenter import MainPresenter

class TestMainPresenter:
    """Tests for the MainPresenter class."""
    
    @pytest.fixture
    def mock_view(self):
        """Create a mock view."""
        view = MagicMock()
        view.get_selected_indices.return_value = set()
        return view
    
    @pytest.fixture
    def mock_document(self):
        """Create a mock document."""
        document = MagicMock(spec=Document)
        document.paragraphs = []
        document.expected_question_count = 0
        document.file_path = None
        return document
    
    @pytest.fixture
    def mock_root(self):
        """Create a mock root window."""
        return MagicMock()
    
    @pytest.fixture
    def presenter(self, mock_view, mock_document, mock_root):
        """Create a presenter with mock dependencies."""
        return MainPresenter(mock_view, mock_document, mock_root)
    
    def test_initialize(self, presenter, mock_view):
        """Test the initialize method."""
        # Act
        presenter.initialize()
        
        # Assert
        mock_view.show_status.assert_called_once_with("Load a DOCX file to begin.")
    
    def test_exit_requested(self, presenter, mock_root):
        """Test the exit_requested method."""
        # Act
        presenter.exit_requested()
        
        # Assert
        mock_root.quit.assert_called_once()
    
    def test_paragraph_selection_changed_with_selection(self, presenter, mock_view):
        """Test paragraph_selection_changed with selection."""
        # Arrange
        mock_view.get_selected_indices.return_value = {1, 2, 3}
        
        # Act
        presenter.paragraph_selection_changed()
        
        # Assert
        mock_view.enable_editing_actions.assert_called_once_with(True)
    
    def test_paragraph_selection_changed_without_selection(self, presenter, mock_view):
        """Test paragraph_selection_changed without selection."""
        # Arrange
        mock_view.get_selected_indices.return_value = set()
        
        # Act
        presenter.paragraph_selection_changed()
        
        # Assert
        mock_view.enable_editing_actions.assert_called_once_with(False)
    
    def test_change_role_requested_no_selection(self, presenter, mock_view):
        """Test change_role_requested with no selection."""
        # Arrange
        mock_view.get_selected_indices.return_value = set()
        
        # Act
        presenter.change_role_requested(ParaRole.QUESTION)
        
        # Assert
        mock_view.show_warning.assert_called_once()
        mock_view.display_paragraphs.assert_not_called()
    
    def test_change_role_requested_with_selection(self, presenter, mock_view, mock_document):
        """Test change_role_requested with selection."""
        # Arrange
        mock_view.get_selected_indices.return_value = {1, 2}
        mock_document.change_paragraph_role.return_value = False
        
        # Act
        presenter.change_role_requested(ParaRole.QUESTION)
        
        # Assert
        assert mock_document.change_paragraph_role.call_count == 2
        mock_view.display_paragraphs.assert_called_once()
    
    def test_set_expected_count_requested_valid(self, presenter, mock_view, mock_document):
        """Test set_expected_count_requested with valid input."""
        # Arrange
        mock_view.get_expected_count.return_value = "42"
        
        # Act
        presenter.set_expected_count_requested()
        
        # Assert
        mock_document.set_expected_question_count.assert_called_once_with(42)
        mock_view.log_message.assert_called_once()
    
    def test_set_expected_count_requested_invalid(self, presenter, mock_view, mock_document):
        """Test set_expected_count_requested with invalid input."""
        # Arrange
        mock_view.get_expected_count.return_value = "not a number"
        
        # Act
        presenter.set_expected_count_requested()
        
        # Assert
        mock_document.set_expected_question_count.assert_not_called()
        mock_view.show_warning.assert_called_once()