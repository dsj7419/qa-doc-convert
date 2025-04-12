"""
Tests for the AnalysisService.
"""
import pytest
from unittest.mock import MagicMock

from services.analysis_service import AnalysisService
from services.analyzers.heuristic_analyzer import HeuristicAnalyzer

def test_estimate_question_count():
    """Test question count estimation."""
    paragraphs = [
        "CIVIL PROCEDURE (50 questions)",
        "1. What is jurisdiction?",
        "Answer: It's the power of a court to hear a case.",
        "2. What are the types of jurisdiction?",
        "Personal and subject matter jurisdiction."
    ]
    
    # Mock status callback
    status_messages = []
    def status_callback(msg):
        status_messages.append(msg)
    
    # Create a heuristic analyzer to test with
    analyzer = HeuristicAnalyzer()
    
    # Run estimation
    count = analyzer._estimate_question_count(paragraphs, status_callback)
    
    # Should detect 50 from the header or 2 from the paragraphs
    assert count in [2, 50]

def test_get_initial_question_indices():
    """Test question identification."""
    paragraphs = [
        "Test Document",
        "1. What is jurisdiction?",
        "Answer: It's the power of a court to hear a case.",
        "2. What are the types of jurisdiction?",
        "Personal and subject matter jurisdiction."
    ]
    
    # Mock status callback
    status_messages = []
    def status_callback(msg):
        status_messages.append(msg)
    
    # Create a heuristic analyzer to test with
    analyzer = HeuristicAnalyzer()
    
    # Run analysis - using the heuristic analyzer's method
    question_indices = analyzer._identify_questions(
        paragraphs, 2, status_callback
    )
    
    # Should identify the question paragraphs
    assert 1 in question_indices  # "1. What is jurisdiction?"
    assert 3 in question_indices  # "2. What are the types of jurisdiction?"
    assert len(question_indices) == 2

def test_analysis_service_analyze():
    """Test the AnalysisService analyze method."""
    paragraphs = [
        "Test Document",
        "1. What is jurisdiction?",
        "Answer: It's the power of a court to hear a case.",
        "2. What are the types of jurisdiction?",
        "Personal and subject matter jurisdiction."
    ]
    
    # Mock status callback
    status_messages = []
    def status_callback(msg):
        status_messages.append(msg)
    
    # Create an analysis service with default config
    analysis_service = AnalysisService()
    
    # Run analysis
    question_indices, est_count = analysis_service.analyze_paragraphs(paragraphs, status_callback)
    
    # Should identify at least the 2 question paragraphs
    assert len(question_indices) >= 2
    assert 1 in question_indices  # "1. What is jurisdiction?"
    assert 3 in question_indices  # "2. What are the types of jurisdiction?"