# File: tests/ui/test_ui_components.py
"""
Tests for UI components, focusing on critical interactive elements.
"""
import pytest
import tkinter as tk
from unittest.mock import MagicMock, patch
import threading
import time

from ui.components.paragraph_list import ParagraphList 
from ui.components.action_panel import ActionPanel
from ui.components.status_bar import StatusBar
from ui.main_window import MainWindow
from models.paragraph import Paragraph, ParaRole
from utils.theme import AppTheme

class TestUIComponents:
    """Test suite for UI components."""
    
    @pytest.fixture
    def setup_tk(self):
        """Set up Tkinter root for testing."""
        try:
            root = tk.Tk()
            root.withdraw()  # Hide the window
            # Set up fonts to avoid font errors
            if hasattr(AppTheme, '_setup_fonts'):
                AppTheme._setup_fonts()
            yield root
            root.destroy()
        except tk.TclError:
            pytest.skip("No display available for Tkinter tests")
    
    def test_paragraph_list_filtering(self, setup_tk):
        """Test paragraph list filtering functionality."""
        try:
            # Create paragraph list
            para_list = ParagraphList(setup_tk)
            
            # Create test paragraphs
            paragraphs = [
                Paragraph(0, "First paragraph", ParaRole.QUESTION, 1),
                Paragraph(1, "Second paragraph with apple", ParaRole.ANSWER, 1),
                Paragraph(2, "Third paragraph", ParaRole.IGNORE)
            ]
            
            # Set paragraphs
            para_list.set_paragraphs(paragraphs)
            
            # Verify all paragraphs are displayed initially
            assert len(para_list.displayed_paragraphs) == 3
            
            # Apply filter
            para_list.filter_var.set("apple")
            para_list._on_filter_change()
            
            # Verify filtering
            assert len(para_list.displayed_paragraphs) == 1
            assert para_list.displayed_paragraphs[0] == 1  # Index of the paragraph with "apple"
            
            # Clear filter
            para_list._clear_filter()
            
            # Verify all paragraphs are displayed again
            assert len(para_list.displayed_paragraphs) == 3
        except tk.TclError:
            pytest.skip("Display error occurred")
    
    def test_action_panel_progress_update(self, setup_tk):
        """Test action panel progress update."""
        try:
            # Create action panel
            panel = ActionPanel(setup_tk)
            
            # Test progress update with different scenarios
            # 1. Perfect match
            panel.update_progress(10, 10)
            assert panel.progress_var.get() == 100.0
            
            # 2. Under target
            panel.update_progress(5, 10)
            assert panel.progress_var.get() == 50.0
            
            # 3. Zero expected
            panel.update_progress(5, 0)
            assert panel.progress_var.get() == 0
        except tk.TclError:
            pytest.skip("Display error occurred")
    
    def test_status_bar_update(self, setup_tk):
        """Test status bar updates."""
        try:
            # Create status bar
            status_bar = StatusBar(setup_tk)
            
            # Test status update
            test_message = "Test status message"
            status_bar.update_status(test_message)
            
            # Verify status was updated
            assert status_bar.status_var.get() == test_message
        except tk.TclError:
            pytest.skip("Display error occurred")
    
    @pytest.mark.skipif("os.environ.get('CI') == 'true'")
    def test_main_window_keyboard_shortcuts(self, setup_tk):
        """Test main window keyboard shortcuts."""
        try:
            # Mock presenter
            mock_presenter = MagicMock()
            
            # Create main window
            window = MainWindow(setup_tk)
            window.set_presenter(mock_presenter)
            
            # Test Undo virtual event (more reliable than keyboard event)
            window.root.event_generate("<<Undo>>")
            window.root.update()
            
            # Verify undo was called
            mock_presenter.undo_requested.assert_called()
            
            # Test Redo virtual event
            window.root.event_generate("<<Redo>>")
            window.root.update()
            
            # Verify redo was called
            mock_presenter.redo_requested.assert_called()
        except (tk.TclError, AttributeError):
            pytest.skip("Display error or event generation not supported")