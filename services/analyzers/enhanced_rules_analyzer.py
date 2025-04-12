"""
Enhanced rule-based paragraph analyzer.
"""
import logging
import re
from typing import List, Set, Tuple, Callable, Dict, Any

from services.analyzers.base_analyzer import BaseAnalyzer
from services.analyzers.heuristic_analyzer import HeuristicAnalyzer

logger = logging.getLogger(__name__)

class EnhancedRuleAnalyzer(BaseAnalyzer):
    """Advanced rule-based analyzer with more sophisticated patterns."""
    
    def __init__(self):
        """Initialize the enhanced rule analyzer."""
        self.heuristic_analyzer = HeuristicAnalyzer()
        
        # Scoring weights
        self.weights = {
            'question_mark': 10,
            'question_start': 8,
            'wh_words': 5,
            'action_words': 5,
            'numeric_reference': 7,
            'length': 3,
            'next_numbered': 2,
            'answer_start': -5,
            'heading_style': -3,
            'numbered_start': 15,
            'previous_was_question': 3,
            'contains_vs': 4,
        }
    
    def analyze(self, paragraphs: List[str], status_callback: Callable[[str], None]) -> Tuple[Set[int], int]:
        """
        Analyze paragraphs using enhanced rules.
        
        Args:
            paragraphs: List of paragraph texts
            status_callback: Callback function for status updates
            
        Returns:
            Tuple containing set of question indices and estimated question count
        """
        status_callback("Running enhanced rule-based analysis...")
        
        # Use the heuristic analyzer to estimate the question count
        estimated_count = self.heuristic_analyzer._estimate_question_count(paragraphs, status_callback)
        status_callback(f"Estimated question count from document structure: {estimated_count}")
        
        # Identify questions using our enhanced rule set
        question_indices = self._identify_questions(paragraphs, estimated_count, status_callback)
        
        return question_indices, estimated_count
    
    def _identify_questions(self, paragraphs: List[str], estimated_count: int, status_callback: Callable[[str], None]) -> Set[int]:
        """
        Identify question paragraphs using enhanced scoring.
        
        Args:
            paragraphs: List of paragraph texts
            estimated_count: Estimated question count
            status_callback: Callback function for status updates
            
        Returns:
            Set of paragraph indices that are questions
        """
        scored_questions = []
        
        # First pass: Score each paragraph
        for i, text in enumerate(paragraphs):
            if len(text) < 8:  # Skip very short paragraphs
                continue
                
            score = self._calculate_question_score(i, text, paragraphs)
            
            if score > 0:
                scored_questions.append({'index': i, 'text': text, 'score': score})
        
        # Sort by score
        scored_questions.sort(key=lambda x: x['score'], reverse=True)
        
        # Calculate the number of questions to take
        take_count = min(len(scored_questions), max(estimated_count, int(estimated_count * 1.1)))
        
        # Take the top candidates
        top_question_indices = {q['index'] for q in scored_questions[:take_count]}
        
        # Second pass: Add questions that were missed but are in a sequence
        final_question_indices = self._refine_questions(top_question_indices, paragraphs)
        
        status_callback(f"Enhanced rules identified {len(final_question_indices)} questions.")
        return final_question_indices
    
    def _calculate_question_score(self, idx: int, text: str, paragraphs: List[str]) -> float:
        """
        Calculate a question score for a paragraph.
        
        Args:
            idx: Paragraph index
            text: Paragraph text
            paragraphs: All paragraphs
            
        Returns:
            Score (higher is more likely to be a question)
        """
        score = 0
        w = self.weights
        
        # Contains question mark
        if '?' in text:
            score += w['question_mark']
        
        # Starts with question words
        if re.match(r'^(What|When|Where|Why|How|Name|Which|Is|Are|Does|Do|Can|Could|Would|Should|List|Explain|Define|Describe|Identify)\b', 
                   text, re.IGNORECASE):
            score += w['question_start']
        
        # Contains WH-words
        if any(word in text.lower() for word in ['what', 'when', 'where', 'why', 'how']):
            score += w['wh_words']
        
        # Contains action words
        if any(word in text.lower() for word in ['name', 'list', 'identify', 'describe', 'define', 'explain', 'discuss']):
            score += w['action_words']
        
        # Contains numeric reference
        if re.search(r'(\d+)\s+(kinds|types|requirements|grounds|factors|situations|matters|things|elements|cases|examples)', 
                    text, re.IGNORECASE):
            score += w['numeric_reference']
        
        # Length factor - questions typically have a moderate length
        if 30 < len(text) < 200:
            score += w['length']
        
        # Next paragraph is numbered - might indicate an answer list
        if idx < len(paragraphs) - 1 and re.match(r'^\s*\d+[\.\)]', paragraphs[idx + 1]):
            score += w['next_numbered']
        
        # Starts like a typical answer
        if re.match(r'^(The|A|An|Both|It|I|We|PC|BRO|LAC|There|This|These|Those)', text):
            score += w['answer_start']
        
        # Looks like a heading style
        if text.isupper() or text.startswith('**'):
            score += w['heading_style']
        
        # Starts with a number followed by a dot or parenthesis
        if re.match(r"^\s*\d+\s*[\.\)]\s+", text):
            score += w['numbered_start']
        
        # Previous paragraph was likely a question
        if idx > 0:
            prev_text = paragraphs[idx - 1]
            if '?' in prev_text or re.match(r'^(What|When|Where|Why|How)', prev_text, re.IGNORECASE):
                score += w['previous_was_question']
        
        # Contains "vs" or "versus" (common in law questions)
        if re.search(r'\bvs\.?\b|\bversus\b', text, re.IGNORECASE):
            score += w['contains_vs']
        
        return score
    
    def _refine_questions(self, question_indices: Set[int], paragraphs: List[str]) -> Set[int]:
        """
        Refine question indices by checking for sequences and patterns.
        
        Args:
            question_indices: Initial set of question indices
            paragraphs: All paragraphs
            
        Returns:
            Refined set of question indices
        """
        final_indices = question_indices.copy()
        
        # Check for numbered sequences
        numbered_questions = {}
        for i in question_indices:
            match = re.match(r"^\s*(\d+)\s*[\.\)]", paragraphs[i])
            if match:
                num = int(match.group(1))
                numbered_questions[num] = i
        
        # If we have a good sequence, fill in any gaps
        if len(numbered_questions) >= 3:
            min_num = min(numbered_questions.keys())
            max_num = max(numbered_questions.keys())
            
            # If we have at least 75% of the sequence, try to fill in gaps
            if len(numbered_questions) / (max_num - min_num + 1) >= 0.75:
                for num in range(min_num, max_num + 1):
                    if num not in numbered_questions:
                        # Look for this numbered question
                        for i, text in enumerate(paragraphs):
                            if i not in final_indices and re.match(r"^\s*" + str(num) + r"\s*[\.\)]", text):
                                final_indices.add(i)
                                break
        
        return final_indices