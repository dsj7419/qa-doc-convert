"""
Command implementations for Document operations.
"""
import logging
from typing import Set, Dict, Any, List, Optional

from commands.base_command import Command
from models.document import Document
from models.paragraph import ParaRole, Paragraph

logger = logging.getLogger(__name__)

class ChangeRoleCommand(Command):
    """Command to change the role of paragraphs."""
    
    def __init__(self, document: Document, indices: Set[int], new_role: ParaRole):
        """
        Initialize the command.
        
        Args:
            document: Document to operate on
            indices: Set of paragraph indices to change
            new_role: New role to assign
        """
        self.document = document
        self.indices = indices
        self.new_role = new_role
        self.old_roles = {}  # Will store old roles for undo
        self.needs_renumber = False
    
    def execute(self) -> None:
        """Execute the command."""
        logger.info(f"Executing ChangeRoleCommand for {len(self.indices)} paragraphs to {self.new_role.name}")
        
        # Save old roles for undo
        self.old_roles = {}
        for idx in self.indices:
            if 0 <= idx < len(self.document.paragraphs):
                self.old_roles[idx] = self.document.paragraphs[idx].role
        
        # Change roles
        self.needs_renumber = False
        for idx in self.indices:
            if self.document.change_paragraph_role(idx, self.new_role):
                self.needs_renumber = True
        
        # Renumber if needed
        if self.needs_renumber:
            self.document.renumber_questions()
        
        # Additional fix: If we're setting to ANSWER role, ensure q_num is set properly
        if self.new_role == ParaRole.ANSWER:
            for idx in sorted(self.indices):
                if self.document.paragraphs[idx].q_num is None:
                    # Find the nearest preceding question number
                    q_num = None
                    for i in range(idx-1, -1, -1):
                        if (self.document.paragraphs[i].role == ParaRole.QUESTION or 
                            self.document.paragraphs[i].role == ParaRole.ANSWER) and \
                        self.document.paragraphs[i].q_num is not None:
                            q_num = self.document.paragraphs[i].q_num
                            break
                    
                    if q_num is not None:
                        # Assign the found question number
                        self.document.paragraphs[idx].q_num = q_num
    
    def undo(self) -> None:
        """Undo the command."""
        logger.info(f"Undoing ChangeRoleCommand for {len(self.indices)} paragraphs")
        
        # Restore old roles
        needs_renumber = False
        for idx, old_role in self.old_roles.items():
            if self.document.change_paragraph_role(idx, old_role):
                needs_renumber = True
        
        # Renumber if needed
        if needs_renumber or self.needs_renumber:
            self.document.renumber_questions()

class MergeParagraphCommand(Command):
    """Command to merge paragraphs into the previous answer."""
    
    def __init__(self, document: Document, indices: Set[int]):
        """
        Initialize the command.
        
        Args:
            document: Document to operate on
            indices: Set of paragraph indices to merge
        """
        self.document = document
        self.indices = indices
        self.old_states = {}  # Will store old states for undo
        self.needs_renumber = False
    
    def execute(self) -> None:
        """Execute the command."""
        logger.info(f"Executing MergeParagraphCommand for {len(self.indices)} paragraphs")
        
        # Save old states for undo
        self.old_states = {}
        for idx in self.indices:
            if 0 <= idx < len(self.document.paragraphs):
                self.old_states[idx] = {
                    'role': self.document.paragraphs[idx].role,
                    'q_num': self.document.paragraphs[idx].q_num
                }
        
        # Process in order (sort indices)
        self.needs_renumber = False
        for idx in sorted(self.indices):
            if idx == 0:
                logger.warning(f"Cannot merge up paragraph at index 0.")
                continue  # Cannot merge the very first paragraph
            
            if self.document.merge_paragraph_up(idx):
                self.needs_renumber = True
        
        # Renumber if needed
        if self.needs_renumber:
            self.document.renumber_questions()
        
    def undo(self) -> None:
        """Undo the command."""
        logger.info(f"Undoing MergeParagraphCommand for {len(self.indices)} paragraphs")
        
        # Restore old states
        needs_renumber = False
        for idx, state in self.old_states.items():
            if self.document.paragraphs[idx].role != state['role']:
                if self.document.change_paragraph_role(idx, state['role']):
                    needs_renumber = True
                # Manually restore q_num
                self.document.paragraphs[idx].q_num = state['q_num']
        
        # Renumber if needed
        if needs_renumber or self.needs_renumber:
            self.document.renumber_questions()

class SetExpectedCountCommand(Command):
    """Command to set the expected question count."""
    
    def __init__(self, document: Document, new_count: int):
        """
        Initialize the command.
        
        Args:
            document: Document to operate on
            new_count: New expected question count
        """
        self.document = document
        self.new_count = new_count
        self.old_count = document.expected_question_count
    
    def execute(self) -> None:
        """Execute the command."""
        logger.info(f"Executing SetExpectedCountCommand from {self.old_count} to {self.new_count}")
        self.document.set_expected_question_count(self.new_count)
    
    def undo(self) -> None:
        """Undo the command."""
        logger.info(f"Undoing SetExpectedCountCommand from {self.new_count} to {self.old_count}")
        self.document.set_expected_question_count(self.old_count)