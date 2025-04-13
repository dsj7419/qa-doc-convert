"""
Base command class for the Command pattern.
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

class Command(ABC):
    """Base command class for the Command pattern."""
    
    @abstractmethod
    def execute(self) -> None:
        """Execute the command."""
        pass
    
    @abstractmethod
    def undo(self) -> None:
        """Undo the command."""
        pass
    
    def redo(self) -> None:
        """Redo the command. By default, just executes again."""
        self.execute()