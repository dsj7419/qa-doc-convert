"""
Script to prepare initial training data from sample document.
This extracts examples from a formatted Q&A document.
"""
import os
import sys
import json
import re
import argparse
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_qa_pairs(file_path: str) -> Tuple[List[Dict[str, str]], List[Dict[str, str]], List[Dict[str, str]]]:
    """
    Extract question and answer pairs from a formatted document.
    
    Args:
        file_path: Path to the text or DOCX file
        
    Returns:
        Tuple of (questions, answers, ignored) training examples
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split into lines
    lines = content.splitlines()
    
    # Initialize storage
    questions = []
    answers = []
    ignored = []
    
    current_state = "unknown"
    question_pattern = re.compile(r'^\s*\d+\.\s+')
    answer_marker = ">"
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Try to determine what this line is
        if question_pattern.match(line):
            # This looks like a numbered question
            questions.append({
                "text": line,
                "source": "extracted",
                "timestamp": datetime.now().isoformat()
            })
            current_state = "after_question"
        elif line.startswith(answer_marker):
            # This is the start of an answer
            clean_text = line[len(answer_marker):].strip()
            if clean_text:
                answers.append({
                    "text": clean_text,
                    "source": "extracted",
                    "timestamp": datetime.now().isoformat()
                })
            current_state = "in_answer"
        elif current_state == "in_answer" and not line.startswith("```"):
            # This is a continuation of an answer
            answers.append({
                "text": line,
                "source": "extracted",
                "timestamp": datetime.now().isoformat()
            })
        else:
            # This might be a header or other non-QA content
            ignored.append({
                "text": line,
                "source": "extracted",
                "timestamp": datetime.now().isoformat()
            })
            current_state = "unknown"
    
    return questions, answers, ignored

def main():
    """Main function to prepare training data."""
    parser = argparse.ArgumentParser(description="Prepare training data from sample document")
    parser.add_argument('file_path', help="Path to the formatted document")
    parser.add_argument('--output', '-o', default="resources/training_data.json", 
                      help="Output path for training_data.json")
    parser.add_argument('--merge', '-m', action='store_true', 
                      help="Merge with existing training data if it exists")
                      
    args = parser.parse_args()
    
    # Extract QA pairs
    questions, answers, ignored = extract_qa_pairs(args.file_path)
    
    logger.info(f"Extracted {len(questions)} questions, {len(answers)} answers, {len(ignored)} ignored passages")
    
    # Load existing data if merging
    if args.merge and os.path.exists(args.output):
        try:
            with open(args.output, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                
            # Merge with existing data
            existing_questions = existing_data.get('question', [])
            existing_answers = existing_data.get('answer', [])
            existing_ignored = existing_data.get('ignore', [])
            
            # Check for duplicates (simple text matching)
            existing_q_texts = {ex.get('text', '') for ex in existing_questions}
            existing_a_texts = {ex.get('text', '') for ex in existing_answers}
            existing_i_texts = {ex.get('text', '') for ex in existing_ignored}
            
            # Filter out duplicates
            questions = [q for q in questions if q['text'] not in existing_q_texts]
            answers = [a for a in answers if a['text'] not in existing_a_texts]
            ignored = [i for i in ignored if i['text'] not in existing_i_texts]
            
            # Add the new examples
            existing_questions.extend(questions)
            existing_answers.extend(answers)
            existing_ignored.extend(ignored)
            
            # Update the data
            questions = existing_questions
            answers = existing_answers
            ignored = existing_ignored
            
            logger.info(f"Merged with existing data, now have {len(questions)} questions, "
                        f"{len(answers)} answers, {len(ignored)} ignored passages")
        except Exception as e:
            logger.error(f"Error merging with existing data: {e}")
            logger.warning("Proceeding with only new data")
    
    # Create the final training data structure
    training_data = {
        'question': questions,
        'answer': answers,
        'ignore': ignored
    }
    
    # Make sure output directory exists
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    
    # Save the training data
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(training_data, f, indent=2)
    
    logger.info(f"Saved training data to {args.output}")

if __name__ == "__main__":
    main()