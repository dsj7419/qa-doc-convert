"""
Paragraph model for representing document paragraphs.
"""
from enum import Enum, auto
from typing import Optional

class ParaRole(Enum):
    """Enum representing the role of a paragraph in the Q&A structure."""
    QUESTION = auto()
    ANSWER = auto()
    IGNORE = auto()  # For headers, footers, formatting, etc.
    UNDETERMINED = auto()  # Initial state

class Paragraph:
    """Represents a paragraph in the document with Q&A metadata."""
    
    def __init__(self, 
                 index: int, 
                 text: str, 
                 role: ParaRole = ParaRole.UNDETERMINED, 
                 q_num: Optional[int] = None):
        """
        Initialize a paragraph.
        
        Args:
            index: Original index in the document
            text: Paragraph text
            role: Role in Q&A structure
            q_num: Question number this paragraph belongs to
        """
        self.index = index
        self.text = text
        self.role = role
        self.q_num = q_num
    
    @property
    def display_text(self) -> str:
        """Generate display text with appropriate prefix based on role."""
        if self.role == ParaRole.QUESTION:
            return f"Q{self.q_num}: {self.text}"
        elif self.role == ParaRole.ANSWER:
            return f"  A{self.q_num}: {self.text}"
        elif self.role == ParaRole.IGNORE:
            return f"[IGNORE]: {self.text}"
        else:  # UNDETERMINED
            return f"[?]: {self.text}"
    
    def matches_filter(self, filter_text: str) -> bool:
        """Check if paragraph matches a filter string."""
        if not filter_text:
            return True
        return filter_text.lower() in self.text.lower()