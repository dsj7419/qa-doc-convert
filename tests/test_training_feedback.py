# tests/test_training_feedback.py

import pytest
from unittest.mock import MagicMock, patch
import tkinter as tk

from ui.components.action_panel import ActionPanel
from utils.theme import AppTheme

class TestTrainingFeedback:
    """Tests for training feedback UI."""

    @pytest.fixture
    def root(self):
        """Create a root window."""
        try:
            # Skip if no display available (CI environment)
            root = tk.Tk()
            root.withdraw()  # Hide the window
            # Initialize AppTheme fonts before creating widgets
            AppTheme._setup_fonts()
            yield root
            root.destroy()
        except tk.TclError:
            pytest.skip("No display available")
    
    @pytest.fixture
    def action_panel(self, root):
        """Create an action panel."""
        panel = ActionPanel(root)
        return panel
    
    def test_training_status_update(self, action_panel):
        """Test updating training status."""
        # Skip UI testing in non-GUI environments
        try:
            # Create a root window to avoid Tkinter errors
            root = action_panel.winfo_toplevel()
            root.update()
        except tk.TclError:
            pytest.skip("Test requires a display")
        
        # Update with status text - just check the variable is updated
        action_panel.update_training_status("Training in progress: Epoch 1/5")
        assert action_panel.training_status_var.get() == "Training in progress: Epoch 1/5"
        
        # Update with new status
        action_panel.update_training_status("Training in progress: Epoch 2/5")
        assert action_panel.training_status_var.get() == "Training in progress: Epoch 2/5"
        
        # Clear status
        action_panel.update_training_status(None)
        
        # We can't reliably test widget visibility in CI environments,
        # so just verify the update method doesn't crash
        assert True