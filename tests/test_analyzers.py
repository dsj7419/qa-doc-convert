"""
Tests for the analyzers.
"""
import pytest
from unittest.mock import MagicMock, patch

from services.analyzers.heuristic_analyzer import HeuristicAnalyzer
from services.analyzers.enhanced_rules_analyzer import EnhancedRuleAnalyzer
from services.analyzers.analyzer_factory import AnalyzerFactory

class TestHeuristicAnalyzer:
    """Tests for the HeuristicAnalyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create a heuristic analyzer."""
        return HeuristicAnalyzer()
    
    @pytest.fixture
    def sample_paragraphs(self):
        """Sample paragraphs for testing."""
        return [
            "CIVIL PROCEDURE (50 questions)",
            "1. What is jurisdiction?",
            "Answer: It's the power of a court to hear a case.",
            "2. What are the types of jurisdiction?",
            "Personal and subject matter jurisdiction."
        ]
    
    def test_estimate_question_count(self, analyzer, sample_paragraphs):
        """Test question count estimation."""
        # Mock status callback
        status_callback = MagicMock()
        
        # Run estimation
        count = analyzer._estimate_question_count(sample_paragraphs, status_callback)
        
        # Should detect 50 from the header or 2 from the paragraphs
        assert count in [2, 50]
    
    def test_identify_questions(self, analyzer, sample_paragraphs):
        """Test question identification."""
        # Mock status callback
        status_callback = MagicMock()
        
        # Run analysis
        question_indices = analyzer._identify_questions(sample_paragraphs, 2, status_callback)
        
        # Should identify the question paragraphs
        assert 1 in question_indices  # "1. What is jurisdiction?"
        assert 3 in question_indices  # "2. What are the types of jurisdiction?"
        assert len(question_indices) == 2

class TestAnalyzerFactory:
    """Tests for the AnalyzerFactory."""
    
    def test_create_analyzer_default(self):
        """Test factory with default config."""
        # Mock AI_AVAILABLE to return False for testing
        with patch('services.analyzers.analyzer_factory.AI_AVAILABLE', False):
            analyzer = AnalyzerFactory.create_analyzer()
            
            # By default, should return either HeuristicAnalyzer or EnhancedRuleAnalyzer
            # when AI is not available
            assert isinstance(analyzer, (HeuristicAnalyzer, EnhancedRuleAnalyzer))
    
    def test_create_analyzer_heuristic(self):
        """Test factory with heuristic config."""
        analyzer = AnalyzerFactory.create_analyzer({'analyzer_type': 'heuristic'})
        assert isinstance(analyzer, HeuristicAnalyzer)
        
    def test_create_analyzer_enhanced(self):
        """Test factory with enhanced config."""
        analyzer = AnalyzerFactory.create_analyzer({'analyzer_type': 'enhanced'})
        assert isinstance(analyzer, EnhancedRuleAnalyzer)