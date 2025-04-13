# services/analysis_service.py
"""
Analysis service for document paragraph analysis.
"""
import logging
import threading
from typing import List, Set, Tuple, Callable, Dict, Any, Optional

from services.analyzers.analyzer_factory import AnalyzerFactory
from services.analyzers.ai_analyzer import AIAnalyzer

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
    
    def analyze_paragraphs_async(self, raw_paragraphs: List[str], status_callback: Callable[[str], None],
                               completion_callback: Callable[[Set[int], int, Optional[Exception]], None]) -> threading.Thread:
        """
        Analyze raw paragraphs asynchronously to identify questions and estimate count.
        
        Args:
            raw_paragraphs: List of paragraph texts
            status_callback: Callback function for status updates
            completion_callback: Callback function receiving (indices, count, exception) upon completion
            
        Returns:
            Thread object
        """
        # Check if we have an AIAnalyzer and should use async mode
        if isinstance(self.analyzer, AIAnalyzer):
            # For AIAnalyzer, use its async method
            return self.analyzer.analyze_async(raw_paragraphs, status_callback, completion_callback)
        else:
            # For other analyzers, create a simple thread
            def _analyze_thread():
                try:
                    question_indices, estimated_count = self.analyzer.analyze(raw_paragraphs, status_callback)
                    completion_callback(question_indices, estimated_count, None)
                except Exception as e:
                    logger.error(f"Error in analysis: {e}", exc_info=True)
                    completion_callback(None, 0, e)
            
            thread = threading.Thread(target=_analyze_thread)
            thread.daemon = True
            thread.start()
            return thread