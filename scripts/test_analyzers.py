"""
Script to test analyzers on real documents.
"""
import logging
import os
import sys
from typing import Callable

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.analyzers.heuristic_analyzer import HeuristicAnalyzer
from services.analyzers.enhanced_rules_analyzer import EnhancedRuleAnalyzer
from services.file_service import FileService
from utils.config_manager import ConfigManager

# Try to import the AI analyzer, but gracefully handle if dependencies are missing
try:
    from services.analyzers.ai_analyzer import AIAnalyzer, SKLEARN_AVAILABLE
    AI_AVAILABLE = SKLEARN_AVAILABLE
except ImportError:
    AI_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def status_callback(message: str) -> None:
    """Simple status callback for testing."""
    logger.info(message)

def test_analyzers(file_path: str) -> None:
    """
    Test analyzers on a document.
    
    Args:
        file_path: Path to DOCX file
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return
    
    logger.info(f"Testing analyzers on: {file_path}")
    
    # Load paragraphs
    try:
        paragraphs = FileService.load_docx_paragraphs(file_path)
        logger.info(f"Loaded {len(paragraphs)} paragraphs")
        
        # Print first 3 paragraphs as sample
        logger.info("Sample paragraphs:")
        for i, p in enumerate(paragraphs[:3]):
            logger.info(f"  {i}: {p[:100]}...")
    except Exception as e:
        logger.error(f"Error loading file: {e}")
        return
    
    # Test heuristic analyzer
    logger.info("\n=== Testing HEURISTIC analyzer ===")
    heuristic_analyzer = HeuristicAnalyzer()
    heuristic_indices = set()
    heuristic_count = 0
    
    try:
        heuristic_indices, heuristic_count = heuristic_analyzer.analyze(paragraphs, status_callback)
        logger.info(f"Heuristic analyzer found {len(heuristic_indices)} questions (estimated {heuristic_count})")
        logger.info(f"First 5 question indices: {sorted(list(heuristic_indices))[:5]}")
        logger.info("First 5 questions:")
        for i, idx in enumerate(sorted(list(heuristic_indices))[:5]):
            logger.info(f"  Q{i+1}: {paragraphs[idx][:100]}...")
    except Exception as e:
        logger.error(f"Error in heuristic analyzer: {e}")
    
    # Test enhanced rule analyzer
    logger.info("\n=== Testing ENHANCED RULE analyzer ===")
    enhanced_analyzer = EnhancedRuleAnalyzer()
    enhanced_indices = set()
    enhanced_count = 0
    
    try:
        enhanced_indices, enhanced_count = enhanced_analyzer.analyze(paragraphs, status_callback)
        logger.info(f"Enhanced analyzer found {len(enhanced_indices)} questions (estimated {enhanced_count})")
        logger.info(f"First 5 question indices: {sorted(list(enhanced_indices))[:5]}")
        logger.info("First 5 questions:")
        for i, idx in enumerate(sorted(list(enhanced_indices))[:5]):
            logger.info(f"  Q{i+1}: {paragraphs[idx][:100]}...")
            
        # Compare with heuristic
        common_indices = heuristic_indices.intersection(enhanced_indices)
        logger.info(f"\nComparison: Common question indices: {len(common_indices)} of {max(len(heuristic_indices), len(enhanced_indices))}")
        agreement_pct = len(common_indices) / max(len(heuristic_indices), len(enhanced_indices)) * 100
        logger.info(f"Agreement percentage: {agreement_pct:.1f}%")
    except Exception as e:
        logger.error(f"Error in enhanced rule analyzer: {e}")
    
    # Test AI analyzer if available
    if AI_AVAILABLE:
        logger.info("\n=== Testing AI analyzer ===")
        ai_analyzer = AIAnalyzer()
        try:
            if ai_analyzer.model is None:
                logger.warning("AI model not loaded, skipping AI analyzer test")
            else:
                ai_indices, ai_count = ai_analyzer.analyze(paragraphs, status_callback)
                logger.info(f"AI analyzer found {len(ai_indices)} questions")
                logger.info(f"First 5 question indices: {sorted(list(ai_indices))[:5]}")
                logger.info("First 5 questions:")
                for i, idx in enumerate(sorted(list(ai_indices))[:5]):
                    logger.info(f"  Q{i+1}: {paragraphs[idx][:100]}...")
                
                # Compare with heuristic
                common_indices_h = heuristic_indices.intersection(ai_indices)
                logger.info(f"\nComparison with heuristic: Common indices: {len(common_indices_h)} of {max(len(heuristic_indices), len(ai_indices))}")
                agreement_pct_h = len(common_indices_h) / max(len(heuristic_indices), len(ai_indices)) * 100
                logger.info(f"Agreement percentage: {agreement_pct_h:.1f}%")
                
                # Compare with enhanced
                common_indices_e = enhanced_indices.intersection(ai_indices)
                logger.info(f"Comparison with enhanced: Common indices: {len(common_indices_e)} of {max(len(enhanced_indices), len(ai_indices))}")
                agreement_pct_e = len(common_indices_e) / max(len(enhanced_indices), len(ai_indices)) * 100
                logger.info(f"Agreement percentage: {agreement_pct_e:.1f}%")
        except Exception as e:
            logger.error(f"Error in AI analyzer: {e}")
    else:
        logger.warning("AI analyzer not available (scikit-learn not installed)")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.error("Please provide a DOCX file path")
        sys.exit(1)
    
    test_analyzers(sys.argv[1])