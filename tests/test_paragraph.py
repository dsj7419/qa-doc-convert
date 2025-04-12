"""
Unit tests for the Paragraph class.
"""
import pytest
from models.paragraph import Paragraph, ParaRole

def test_paragraph_initialization():
    """Test that a paragraph can be properly initialized."""
    # Arrange
    index = 5
    text = "This is a test paragraph."
    role = ParaRole.QUESTION
    q_num = 3
    
    # Act
    paragraph = Paragraph(index, text, role, q_num)
    
    # Assert
    assert paragraph.index == index
    assert paragraph.text == text
    assert paragraph.role == role
    assert paragraph.q_num == q_num

def test_paragraph_display_text_question():
    """Test the display_text property for a question paragraph."""
    # Arrange
    paragraph = Paragraph(1, "Who is the president?", ParaRole.QUESTION, 2)
    
    # Act
    display = paragraph.display_text
    
    # Assert
    assert display == "Q2: Who is the president?"

def test_paragraph_display_text_answer():
    """Test the display_text property for an answer paragraph."""
    # Arrange
    paragraph = Paragraph(2, "The president is...", ParaRole.ANSWER, 2)
    
    # Act
    display = paragraph.display_text
    
    # Assert
    assert display == "  A2: The president is..."

def test_paragraph_display_text_ignore():
    """Test the display_text property for an ignored paragraph."""
    # Arrange
    paragraph = Paragraph(3, "Header text", ParaRole.IGNORE)
    
    # Act
    display = paragraph.display_text
    
    # Assert
    assert display == "[IGNORE]: Header text"

def test_paragraph_display_text_undetermined():
    """Test the display_text property for an undetermined paragraph."""
    # Arrange
    paragraph = Paragraph(4, "Unknown text", ParaRole.UNDETERMINED)
    
    # Act
    display = paragraph.display_text
    
    # Assert
    assert display == "[?]: Unknown text"

def test_paragraph_matches_filter():
    """Test the matches_filter method."""
    # Arrange
    paragraph = Paragraph(1, "This contains apple and banana", ParaRole.QUESTION, 1)
    
    # Act & Assert
    assert paragraph.matches_filter("apple") is True
    assert paragraph.matches_filter("orange") is False
    assert paragraph.matches_filter("") is True
    assert paragraph.matches_filter("APPLE") is True  # Case insensitive