"""
Command manager for undo/redo functionality.
"""
import logging
from collections import deque
from typing import Deque, Optional, List, Dict, Any

from commands.base_command import Command

logger = logging.getLogger(__name__)

class CommandManager:
    """Manages commands for undo/redo functionality."""
    
    def __init__(self, max_history: int = 100):
        """
        Initialize the command manager.
        
        Args:
            max_history: Maximum number of commands to keep in history
        """
        self.undo_stack: Deque[Command] = deque(maxlen=max_history)
        self.redo_stack: Deque[Command] = deque(maxlen=max_history)
    
    def execute(self, command: Command) -> None:
        """
        Execute a command and add it to the undo stack.
        
        Args:
            command: Command to execute
        """
        # Execute the command
        command.execute()
        
        # Add to undo stack
        self.undo_stack.append(command)
        
        # Clear redo stack
        self.redo_stack.clear()
        
        logger.debug(f"Executed command: {command.__class__.__name__}, undo stack: {len(self.undo_stack)}, redo stack: {len(self.redo_stack)}")
    
    def undo(self) -> bool:
        """
        Undo the last command.
        
        Returns:
            bool: True if a command was undone, False if no commands to undo
        """
        if not self.undo_stack:
            logger.debug("No commands to undo")
            return False
        
        # Pop command from undo stack
        command = self.undo_stack.pop()
        
        # Undo the command
        command.undo()
        
        # Add to redo stack
        self.redo_stack.append(command)
        
        logger.debug(f"Undid command: {command.__class__.__name__}, undo stack: {len(self.undo_stack)}, redo stack: {len(self.redo_stack)}")
        return True
    
    def redo(self) -> bool:
        """
        Redo the last undone command.
        
        Returns:
            bool: True if a command was redone, False if no commands to redo
        """
        if not self.redo_stack:
            logger.debug("No commands to redo")
            return False
        
        # Pop command from redo stack
        command = self.redo_stack.pop()
        
        # Redo (execute) the command
        command.redo()
        
        # Add back to undo stack
        self.undo_stack.append(command)
        
        logger.debug(f"Redid command: {command.__class__.__name__}, undo stack: {len(self.undo_stack)}, redo stack: {len(self.redo_stack)}")
        return True
    
    def can_undo(self) -> bool:
        """
        Check if there are commands to undo.
        
        Returns:
            bool: True if there are commands to undo
        """
        return len(self.undo_stack) > 0
    
    def can_redo(self) -> bool:
        """
        Check if there are commands to redo.
        
        Returns:
            bool: True if there are commands to redo
        """
        return len(self.redo_stack) > 0
    
    def clear(self) -> None:
        """Clear all command history."""
        self.undo_stack.clear()
        self.redo_stack.clear()
        logger.debug("Command history cleared")