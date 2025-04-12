"""
Tests for the FileService.
"""
import os
import pytest
from pathlib import Path
from services.file_service import FileService

# Skip tests that require UI interaction or actual file I/O
pytestmark = pytest.mark.skipif(
    "CI" in os.environ, 
    reason="Skip UI-dependent tests in CI environment"
)

def test_save_data_to_csv(tmp_path):
    """Test saving data to CSV."""
    # Create test data
    data = [
        ["Q1. What is jurisdiction?", "It's the power of a court to hear a case."],
        ["Q2. What are the types of jurisdiction?", "Personal and subject matter jurisdiction."]
    ]
    
    # Save to a temporary file
    save_path = tmp_path / "test_output.csv"
    result = FileService.save_data_to_csv(data, str(save_path))
    
    # Verify the result and file contents
    assert result is True
    assert save_path.exists()
    
    # Read back and verify contents
    with open(save_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    assert len(lines) == 2
    assert "Q1. What is jurisdiction?" in lines[0]
    assert "Q2. What are the types of jurisdiction?" in lines[1]