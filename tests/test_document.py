"""
Unit tests for the Document class, focusing on data holding aspects.
"""
import pytest
from models.document import Document
from models.paragraph import Paragraph, ParaRole

def test_document_initialization():
    """Test that a document can be properly initialized."""
    # Arrange & Act
    document = Document()
    
    # Assert
    assert document.file_path is None
    assert document.paragraphs == []
    assert document.expected_question_count == 0
    assert document._current_q_num == 0

def test_document_change_paragraph_role():
    """Test changing paragraph role."""
    # Arrange
    document = Document()
    document.paragraphs = [
        Paragraph(0, "Question 1?", ParaRole.QUESTION, 1),
        Paragraph(1, "Answer 1", ParaRole.ANSWER, 1),
        Paragraph(2, "Question 2?", ParaRole.QUESTION, 2)
    ]
    
    # Act
    needs_renumber = document.change_paragraph_role(1, ParaRole.IGNORE)
    
    # Assert
    assert document.paragraphs[1].role == ParaRole.IGNORE
    assert needs_renumber is False  # Changing ANSWER to IGNORE doesn't require renumbering
    
    # Act again - changing a question should require renumbering
    needs_renumber = document.change_paragraph_role(0, ParaRole.IGNORE)
    
    # Assert
    assert document.paragraphs[0].role == ParaRole.IGNORE
    assert needs_renumber is True  # Changing QUESTION to something else requires renumbering

def test_document_renumber_questions():
    """Test renumbering questions."""
    # Arrange
    document = Document()
    document.paragraphs = [
        Paragraph(0, "Header", ParaRole.IGNORE),
        Paragraph(1, "Question 1?", ParaRole.QUESTION, None),
        Paragraph(2, "Answer 1", ParaRole.ANSWER, None),
        Paragraph(3, "Question 2?", ParaRole.QUESTION, None),
        Paragraph(4, "Answer 2", ParaRole.ANSWER, None)
    ]
    
    # Act
    document.renumber_questions()
    
    # Assert
    assert document.paragraphs[0].q_num is None  # IGNORE
    assert document.paragraphs[1].q_num == 1     # QUESTION
    assert document.paragraphs[2].q_num == 1     # ANSWER
    assert document.paragraphs[3].q_num == 2     # QUESTION
    assert document.paragraphs[4].q_num == 2     # ANSWER
    assert document._current_q_num == 2

def test_document_get_question_count():
    """Test getting question count."""
    # Arrange
    document = Document()
    document.paragraphs = [
        Paragraph(0, "Header", ParaRole.IGNORE),
        Paragraph(1, "Question 1?", ParaRole.QUESTION, 1),
        Paragraph(2, "Answer 1", ParaRole.ANSWER, 1),
        Paragraph(3, "Question 2?", ParaRole.QUESTION, 2),
        Paragraph(4, "Answer 2", ParaRole.ANSWER, 2)
    ]
    
    # Act
    count = document.get_question_count()
    
    # Assert
    assert count == 2

def test_document_set_expected_question_count():
    """Test setting expected question count."""
    # Arrange
    document = Document()
    
    # Act
    document.set_expected_question_count(25)
    
    # Assert
    assert document.expected_question_count == 25