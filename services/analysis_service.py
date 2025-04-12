"""
Analysis service for document paragraph analysis.
"""
import logging
from typing import List, Set, Tuple, Callable, Dict, Any, Optional

from services.analyzers.analyzer_factory import AnalyzerFactory

logger = logging.getLogger(__name__)

class AnalysisService:
    """Service for analyzing document paragraphs to identify questions and answers."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the analysis service.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.analyzer = AnalyzerFactory.create_analyzer(self.config)
    
    def analyze_paragraphs(self, raw_paragraphs: List[str], status_callback: Callable[[str], None]) -> Tuple[Set[int], int]:
        """
        Analyze raw paragraphs to identify questions and estimate count.
        
        Args:
            raw_paragraphs: List of paragraph texts
            status_callback: Callback function for status updates
            
        Returns:
            Tuple containing set of question indices and estimated question count
        """
        return self.analyzer.analyze(raw_paragraphs, status_callback)