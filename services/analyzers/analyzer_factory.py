"""
Factory for creating appropriate analyzers.
"""
import logging
import os
import sys
from typing import Dict, Any, Optional

from services.analyzers.base_analyzer import BaseAnalyzer
from services.analyzers.heuristic_analyzer import HeuristicAnalyzer
from services.analyzers.enhanced_rules_analyzer import EnhancedRuleAnalyzer

# Try to import the AI analyzer, but gracefully handle if dependencies are missing
try:
    from services.analyzers.ai_analyzer import AIAnalyzer
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

logger = logging.getLogger(__name__)

class AnalyzerFactory:
    """Factory for creating paragraph analyzers."""
    
    @staticmethod
    def create_analyzer(config: Optional[Dict[str, Any]] = None) -> BaseAnalyzer:
        """
        Create an appropriate analyzer based on configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            BaseAnalyzer: An instance of a paragraph analyzer
        """
        # Default to heuristic if no config provided
        if config is None:
            config = {}
        
        # Get analyzer type from config
        analyzer_type = config.get('analyzer_type', 'auto')
        
        # Create a logger for factory diagnostics
        logger = logging.getLogger("analyzer_factory")
        logger.info(f"Creating analyzer with type: {analyzer_type}")
        
        if analyzer_type == 'heuristic':
            logger.info("Using basic heuristic analyzer")
            return HeuristicAnalyzer()
        
        elif analyzer_type == 'enhanced':
            logger.info("Using enhanced rule-based analyzer")
            return EnhancedRuleAnalyzer()
        
        elif analyzer_type == 'ai':
            if AI_AVAILABLE:
                logger.info("Attempting to create AI analyzer")
                ai_analyzer = AIAnalyzer()
                
                # Check if model is available
                if ai_analyzer.model is not None:
                    logger.info("AI model loaded successfully, using AI analyzer")
                    return ai_analyzer
                else:
                    logger.warning("AI model not loaded, falling back to enhanced rules")
                    return EnhancedRuleAnalyzer()
            else:
                logger.warning("AI analyzer requested but dependencies not available. Using enhanced rules instead.")
                return EnhancedRuleAnalyzer()
        
        else:  # 'auto' - try AI, then enhanced rules, then basic heuristic
            if AI_AVAILABLE:
                logger.info("Auto mode: Attempting to use AI analyzer")
                ai_analyzer = AIAnalyzer()
                
                # Check if model is available
                if ai_analyzer.model is not None:
                    logger.info("AI model loaded successfully, using AI analyzer")
                    return ai_analyzer
            
            logger.info("Auto mode: Using enhanced rule-based analyzer")
            return EnhancedRuleAnalyzer()