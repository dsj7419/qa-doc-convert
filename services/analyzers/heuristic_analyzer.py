"""
Heuristic-based paragraph analyzer.
"""
import logging
import re
from typing import List, Set, Tuple, Callable, Dict

from services.analyzers.base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)

class HeuristicAnalyzer(BaseAnalyzer):
    """Analyzer that uses heuristic rules to identify questions and answers."""
    
    def analyze(self, paragraphs: List[str], status_callback: Callable[[str], None]) -> Tuple[Set[int], int]:
        """
        Analyze paragraphs using heuristics.
        
        Args:
            paragraphs: List of paragraph texts
            status_callback: Callback function for status updates
            
        Returns:
            Tuple containing set of question indices and estimated question count
        """
        status_callback("Running heuristic analysis...")
        
        # Estimate question count
        estimated_count = self._estimate_question_count(paragraphs, status_callback)
        status_callback(f"Estimated question count from document structure: {estimated_count}")
        
        # Identify questions
        question_indices = self._identify_questions(paragraphs, estimated_count, status_callback)
        
        return question_indices, estimated_count
    
    def _estimate_question_count(self, paragraphs: List[str], status_callback: Callable[[str], None]) -> int:
        """
        Estimates the number of questions in the document based on structure.
        
        Args:
            paragraphs: List of paragraph texts
            status_callback: Callback function for status updates
            
        Returns:
            int: Estimated question count
        """
        # Method 1: Look for sequential numbering patterns
        numbered_paragraphs = [p for p in paragraphs if re.match(r'^\s*\d+[\.\)]', p)]
        
        # Method 2: Look for question marks
        question_marks = [p for p in paragraphs if '?' in p]
        
        # Method 3: Check document title/header for question count
        title_count = None
        for i, p in enumerate(paragraphs[:10]):  # Check first 10 paragraphs for headers
            count_match = re.search(r'(\d+)\s*(?:questions|problems|items)', p, re.IGNORECASE)
            if count_match:
                title_count = int(count_match.group(1))
                status_callback(f"Found question count in document header: {title_count}")
                break
        
        # Method 4: Look at largest sequential number
        max_seq_num = 0
        for p in paragraphs:
            num_match = re.match(r'^\s*(\d+)[\.\)]', p)
            if num_match:
                try:
                    num = int(num_match.group(1))
                    max_seq_num = max(max_seq_num, num)
                except ValueError:
                    pass
        
        # Decide on the most likely count
        if title_count is not None:
            return title_count
        elif max_seq_num > 10:  # If we have sequential numbering with a reasonable max
            return max_seq_num
        elif len(numbered_paragraphs) > 10:
            return len(numbered_paragraphs)
        elif len(question_marks) > 5:
            return len(question_marks)
        else:
            # Default fallback - use a reasonable default
            return 25
    
    def _identify_questions(self, paragraphs: List[str], estimated_count: int, status_callback: Callable[[str], None]) -> Set[int]:
        """
        Identify question paragraphs using heuristic scoring.
        
        Args:
            paragraphs: List of paragraph texts
            estimated_count: Estimated question count
            status_callback: Callback function for status updates
            
        Returns:
            Set of paragraph indices that are questions
        """
        potential_questions = []
        # Map original index to paragraph text for scoring
        para_map = {i: p for i, p in enumerate(paragraphs)}

        # Identify potential questions based on keywords/structure
        for i, p in enumerate(paragraphs):
            if len(p) < 10: continue
            if p.startswith(('```', '<!--', '-->')): continue
            
            has_question_mark = '?' in p
            has_question_words = any(word in p.lower() for word in
                             ['what', 'when', 'where', 'why', 'how', 'name', 'list',
                              'identify', 'describe', 'define', 'explain'])
            has_numeric_reference = bool(re.search(r'(\d+)\s+(kinds|types|requirements|grounds|factors|situations|matters|things)', p, re.IGNORECASE))
            is_question_like = (
                p.lower().startswith(('what', 'when', 'where', 'why', 'how', 'name', 'is ', 'are ', 'does ')) or
                re.search(r'(what is|what are|name the|which|how many)', p.lower())
            )

            if has_question_mark or has_question_words or has_numeric_reference or is_question_like:
                potential_questions.append((i, p))

        status_callback(f"Found {len(potential_questions)} potential questions based on initial keywords/structure.")

        # Score the potential questions
        scored_questions = []
        for idx, text in potential_questions:
            score = 0
            if '?' in text: score += 10
            if re.match(r'^(What|When|Where|Why|How|Name|Which|Is|Are|Does|Do)\b', text, re.IGNORECASE): score += 8
            if any(word in text.lower() for word in ['what', 'when', 'where', 'why', 'how']): score += 5
            if any(word in text.lower() for word in ['name', 'list', 'identify', 'describe', 'define']): score += 5
            if re.search(r'(\d+)\s+(kinds|types|requirements|grounds|factors|situations|matters|things)', text, re.IGNORECASE): score += 7
            if len(text) > 30: score += 3
            # Simplified next paragraph check - less reliable, weighted lower
            if idx < len(paragraphs) - 1 and re.match(r'^\s*\d+[\.\)]', para_map.get(idx + 1, '')): score += 2
            if text.startswith(('The ', 'A ', 'An ', 'Both ', 'It ', 'PC', 'BRO', 'LAC', '1.', '2.', '3.', 'a.', 'b.')): score -= 5 # Penalize typical answer starts
            if text.isupper() or text.startswith('**'): score -= 3

            # Big boost if it *actually* starts with a number/dot/space pattern
            if re.match(r"^\s*\d+\s*[\.\)]\s+", text):
                score += 15

            # Only add if score is reasonably positive
            if score > 0:
               scored_questions.append({'index': idx, 'text': text, 'score': score})

        scored_questions.sort(key=lambda x: x['score'], reverse=True)
        status_callback(f"Scored {len(scored_questions)} potential questions.")

        # Take the top candidates based on the estimated count, but be slightly generous
        take_count = min(len(scored_questions), max(estimated_count, int(estimated_count * 1.1)))
        top_scored_indices = {q['index'] for q in scored_questions[:take_count]}

        status_callback(f"Identified initial {len(top_scored_indices)} candidates for questions.")
        return top_scored_indices