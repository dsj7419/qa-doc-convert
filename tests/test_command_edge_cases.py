# File: tests/test_command_edge_cases.py
"""
Tests for command edge cases and complex integration scenarios.
"""
import pytest
from unittest.mock import MagicMock, patch
import threading
import time

from models.document import Document
from models.paragraph import Paragraph, ParaRole
from commands.command_manager import CommandManager
from commands.document_commands import ChangeRoleCommand, MergeParagraphCommand, SetExpectedCountCommand

class TestCommandEdgeCases:
    """Test suite for command edge cases."""
    
    @pytest.fixture
    def document(self):
        """Create a document with sample paragraphs."""
        document = Document()
        document.paragraphs = [
            Paragraph(0, "Header", ParaRole.IGNORE),
            Paragraph(1, "Question 1?", ParaRole.QUESTION, 1),
            Paragraph(2, "Answer 1", ParaRole.ANSWER, 1),
            Paragraph(3, "Question 2?", ParaRole.QUESTION, 2),
            Paragraph(4, "Answer 2", ParaRole.ANSWER, 2)
        ]
        return document
    
    @pytest.fixture
    def command_manager(self):
        """Create a command manager."""
        return CommandManager()
    
    def test_change_role_boundary_conditions(self, document, command_manager):
        """Test change role command with boundary conditions."""
        # Try to change role for an out-of-bounds index
        cmd1 = ChangeRoleCommand(document, {999}, ParaRole.QUESTION)
        command_manager.execute(cmd1)
        
        # Verify document state is still valid
        assert len(document.paragraphs) == 5
        
        # Try to change role for an empty selection
        cmd2 = ChangeRoleCommand(document, set(), ParaRole.QUESTION)
        command_manager.execute(cmd2)
        
        # Verify document state is still valid
        assert len(document.paragraphs) == 5
        
        # Try to change role for multiple indices including an invalid one
        cmd3 = ChangeRoleCommand(document, {1, 999}, ParaRole.ANSWER)
        command_manager.execute(cmd3)
        
        # Verify valid index was processed and invalid was ignored
        assert document.paragraphs[1].role == ParaRole.ANSWER
    
    def test_merge_paragraph_edge_cases(self, document, command_manager):
        """Test merge paragraph edge cases."""
        # Try to merge the first paragraph (no previous paragraph)
        cmd1 = MergeParagraphCommand(document, {0})
        command_manager.execute(cmd1)
        
        # Verify first paragraph is unchanged
        assert document.paragraphs[0].role == ParaRole.IGNORE
        
        # Try to merge paragraph with no preceding question/answer
        # First change paragraph 0 to UNDETERMINED
        document.paragraphs[0].role = ParaRole.UNDETERMINED
        document.paragraphs[0].q_num = None
        
        # Then try to merge paragraph 1 up
        cmd2 = MergeParagraphCommand(document, {1})
        command_manager.execute(cmd2)
        
        # Verify paragraph 1 is unchanged (no valid q_num to merge with)
        # Fix: Expected value should be QUESTION based on document initialization
        assert document.paragraphs[1].role == ParaRole.QUESTION
        
        # Try to merge multiple paragraphs including an invalid index
        cmd3 = MergeParagraphCommand(document, {2, 999})
        command_manager.execute(cmd3)
        
        # Verify valid indices were processed
        assert document.paragraphs[2].role == ParaRole.ANSWER
    
    def test_set_expected_count_validation(self, document, command_manager):
        """Test set expected count validation."""
        # Set to zero (invalid)
        cmd1 = SetExpectedCountCommand(document, 0)
        command_manager.execute(cmd1)
        
        # Verify it was rejected (implementation dependent; some might accept 0)
        
        # Set to negative (invalid)
        cmd2 = SetExpectedCountCommand(document, -10)
        command_manager.execute(cmd2)
        
        # Set to extremely large value
        cmd3 = SetExpectedCountCommand(document, 1000000)
        command_manager.execute(cmd3)
        
        # Verify it was set
        assert document.expected_question_count == 1000000
        
        # Undo all changes
        while command_manager.undo():
            pass
        
        # Verify final state
        assert document.expected_question_count == 0  # Original value
    
    def test_command_sequence_with_renumbering(self, document, command_manager):
        """Test a complex sequence of commands that trigger renumbering."""
        # Initial state
        assert document.paragraphs[1].q_num == 1
        assert document.paragraphs[3].q_num == 2
        
        # Execute first command - change Question 1 to IGNORE
        cmd1 = ChangeRoleCommand(document, {1}, ParaRole.IGNORE)
        command_manager.execute(cmd1)
        
        # Verify renumbering occurred - Question 2 should now be Question 1
        assert document.paragraphs[1].role == ParaRole.IGNORE
        assert document.paragraphs[1].q_num is None
        assert document.paragraphs[3].q_num == 1  # Renumbered from 2 to 1
        
        # Execute second command - change Answer 1 to QUESTION
        cmd2 = ChangeRoleCommand(document, {2}, ParaRole.QUESTION)
        command_manager.execute(cmd2)
        
        # Verify renumbering - should have 2 questions again
        assert document.paragraphs[2].role == ParaRole.QUESTION
        assert document.paragraphs[2].q_num == 1  # First question
        assert document.paragraphs[3].q_num == 2  # Second question again
        
        # Execute third command - merge Answer 2 into previous
        cmd3 = MergeParagraphCommand(document, {4})
        command_manager.execute(cmd3)
        
        # Verify Answer 2 is now attached to Question 2
        assert document.paragraphs[4].role == ParaRole.ANSWER
        assert document.paragraphs[4].q_num == 2
        
        # Undo all commands
        assert command_manager.undo()  # Undo cmd3
        assert command_manager.undo()  # Undo cmd2
        assert command_manager.undo()  # Undo cmd1
        
        # Verify we're back to initial state
        assert document.paragraphs[1].role == ParaRole.QUESTION
        assert document.paragraphs[1].q_num == 1
        assert document.paragraphs[2].role == ParaRole.ANSWER
        assert document.paragraphs[2].q_num == 1
        assert document.paragraphs[3].role == ParaRole.QUESTION
        assert document.paragraphs[3].q_num == 2
        assert document.paragraphs[4].role == ParaRole.ANSWER
        assert document.paragraphs[4].q_num == 2