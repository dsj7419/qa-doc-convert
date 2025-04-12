"""
Base analyzer interface for paragraph analysis.
"""
from abc import ABC, abstractmethod
from typing import List, Set, Tuple, Callable

class BaseAnalyzer(ABC):
    """Base interface for paragraph analyzers."""
    
    @abstractmethod
    def analyze(self, paragraphs: List[str], status_callback: Callable[[str], None]) -> Tuple[Set[int], int]:
        """
        Analyze paragraphs to identify questions and estimate count.
        
        Args:
            paragraphs: List of paragraph texts
            status_callback: Callback function for status updates
            
        Returns:
            Tuple containing set of question indices and estimated question count
        """
        pass