# tests/test_command_integration.py

import pytest
from unittest.mock import MagicMock

from commands.command_manager import CommandManager
from commands.document_commands import ChangeRoleCommand, MergeParagraphCommand
from models.document import Document
from models.paragraph import Paragraph, ParaRole

class TestCommandIntegration:
    """Tests for command integration scenarios."""
    
    @pytest.fixture
    def document(self):
        """Create a document with sample paragraphs."""
        document = Document()
        document.paragraphs = [
            Paragraph(0, "Header", ParaRole.IGNORE),
            Paragraph(1, "Question 1?", ParaRole.UNDETERMINED),
            Paragraph(2, "Answer 1", ParaRole.UNDETERMINED),
            Paragraph(3, "Question 2?", ParaRole.UNDETERMINED),
            Paragraph(4, "Answer 2", ParaRole.UNDETERMINED)
        ]
        return document
    
    @pytest.fixture
    def command_manager(self):
        """Create a command manager."""
        return CommandManager()
    
    def test_complex_command_chain(self, document, command_manager):
        """Test a complex chain of commands and undo/redo operations."""
        # Initial state verification
        assert document.paragraphs[1].role == ParaRole.UNDETERMINED
        assert document.paragraphs[2].role == ParaRole.UNDETERMINED
        
        # Execute first command - mark question
        cmd1 = ChangeRoleCommand(document, {1}, ParaRole.QUESTION)
        command_manager.execute(cmd1)
        assert document.paragraphs[1].role == ParaRole.QUESTION
        assert document.paragraphs[1].q_num == 1
        
        # Execute second command - mark answer
        cmd2 = ChangeRoleCommand(document, {2}, ParaRole.ANSWER)
        command_manager.execute(cmd2)
        assert document.paragraphs[2].role == ParaRole.ANSWER
        assert document.paragraphs[2].q_num == 1
        
        # Execute third command - mark another question
        cmd3 = ChangeRoleCommand(document, {3}, ParaRole.QUESTION)
        command_manager.execute(cmd3)
        assert document.paragraphs[3].role == ParaRole.QUESTION
        assert document.paragraphs[3].q_num == 2
        
        # Undo last command
        assert command_manager.undo()
        assert document.paragraphs[3].role == ParaRole.UNDETERMINED
        assert document.paragraphs[3].q_num is None
        
        # Redo last command
        assert command_manager.redo()
        assert document.paragraphs[3].role == ParaRole.QUESTION
        assert document.paragraphs[3].q_num == 2
        
        # Undo twice
        assert command_manager.undo()
        assert command_manager.undo()
        assert document.paragraphs[2].role == ParaRole.UNDETERMINED
        assert document.paragraphs[3].role == ParaRole.UNDETERMINED
        
        # Execute new command after undo (should clear redo stack)
        cmd4 = ChangeRoleCommand(document, {2, 4}, ParaRole.ANSWER)
        command_manager.execute(cmd4)
        assert document.paragraphs[2].role == ParaRole.ANSWER
        assert document.paragraphs[4].role == ParaRole.ANSWER
        
        # Verify redo is no longer possible
        assert not command_manager.can_redo()
    
    def test_command_history_limit(self):
        """Test the command history limit."""
        # Create command manager with small history limit
        limited_manager = CommandManager(max_history=3)
        
        # Create a mock document and mock commands
        mock_doc = MagicMock()
        
        # Execute more commands than the history limit
        for i in range(5):
            cmd = MagicMock()
            limited_manager.execute(cmd)
        
        # Verify we can only undo the last 3 commands
        assert limited_manager.can_undo()
        assert len(limited_manager.undo_stack) == 3
        
        # Undo all possible commands
        assert limited_manager.undo()
        assert limited_manager.undo()
        assert limited_manager.undo()
        assert not limited_manager.undo()  # No more to undo