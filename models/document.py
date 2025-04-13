"""
Document model for handling document data and operations.
"""
import logging
import os
import threading
from typing import List, Dict, Optional, Set, Tuple, Any, Callable

from models.paragraph import Paragraph, ParaRole
from services.analysis_service import AnalysisService
from services.file_service import FileService
from utils.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class Document:
    """Represents a document with paragraphs for Q&A analysis."""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Initialize an empty document.
        
        Args:
            config_manager: Configuration manager
        """
        self.file_path: Optional[str] = None
        self.paragraphs: List[Paragraph] = []
        self.expected_question_count: int = 0
        self._current_q_num: int = 0
        self.config_manager = config_manager or ConfigManager()
        self._loading_thread = None
        self._analyzing_thread = None
        
    def load_file(self, file_path: str, status_callback: Callable[[str], None]) -> bool:
        """
        Load a DOCX file, extract paragraphs, run initial analysis.
        
        Args:
            file_path: Path to the DOCX file
            status_callback: Callback function for status updates
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.file_path = file_path
            status_callback(f"Loading: {os.path.basename(file_path)}...")
            
            # Use FileService to load paragraphs
            raw_paragraphs = FileService.load_docx_paragraphs(file_path)
            
            if not raw_paragraphs:
                logger.error("Document contains no readable text.")
                return False
                
            # Create analysis service with config
            analysis_config = self.config_manager.get_config('analysis')
            analysis_service = AnalysisService(analysis_config)
            
            # Analyze paragraphs
            question_indices, est_count = analysis_service.analyze_paragraphs(raw_paragraphs, status_callback)
            
            # Set expected count
            self.expected_question_count = est_count
            
            # Process paragraphs
            self._process_paragraphs(raw_paragraphs, question_indices)
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading or processing file: {e}", exc_info=True)
            return False
    
    def load_file_async(self, file_path: str, status_callback: Callable[[str], None],
                       completion_callback: Callable[[bool], None]) -> None:
        """
        Load a DOCX file asynchronously, extract paragraphs, run initial analysis.
        
        Args:
            file_path: Path to the DOCX file
            status_callback: Callback function for status updates
            completion_callback: Callback function receiving success flag upon completion
        """
        self.file_path = file_path
        status_callback(f"Loading: {os.path.basename(file_path)}...")
        
        # Define callbacks
        def on_paragraphs_loaded(raw_paragraphs, exception):
            if exception:
                logger.error(f"Error loading file: {exception}")
                completion_callback(False)
                return
            
            if not raw_paragraphs:
                logger.error("Document contains no readable text.")
                completion_callback(False)
                return
                
            status_callback("Document loaded. Starting paragraph analysis...")
            
            # Create analysis service with config
            analysis_config = self.config_manager.get_config('analysis')
            analysis_service = AnalysisService(analysis_config)
            
            # Define analysis callback
            def on_analysis_complete(question_indices, est_count, exception):
                if exception:
                    logger.error(f"Error analyzing paragraphs: {exception}")
                    completion_callback(False)
                    return
                
                # Set expected count
                self.expected_question_count = est_count
                
                # Process paragraphs
                self._process_paragraphs(raw_paragraphs, question_indices)
                
                # Signal completion
                completion_callback(True)
            
            # Analyze paragraphs asynchronously
            self._analyzing_thread = analysis_service.analyze_paragraphs_async(
                raw_paragraphs, status_callback, on_analysis_complete
            )
        
        # Load paragraphs asynchronously
        self._loading_thread = FileService.load_docx_paragraphs_async(file_path, on_paragraphs_loaded)
    
    def _process_paragraphs(self, raw_paragraphs: List[str], question_indices: Set[int]) -> None:
        """
        Process paragraphs and assign roles based on initial analysis.
        
        Args:
            raw_paragraphs: List of paragraph texts
            question_indices: Set of indices identified as questions
        """
        self.paragraphs = []
        self._current_q_num = 0
        last_role = ParaRole.UNDETERMINED
        
        for i, text in enumerate(raw_paragraphs):
            role = ParaRole.UNDETERMINED
            q_num = None
            
            if i in question_indices:
                role = ParaRole.QUESTION
                self._current_q_num += 1
                q_num = self._current_q_num
            elif last_role == ParaRole.QUESTION or last_role == ParaRole.ANSWER:
                # If the previous was Q or A, assume this is an Answer
                role = ParaRole.ANSWER
                q_num = self._current_q_num
            else:
                # Could be header or undetermined
                # Mark short starting lines as IGNORE potentially
                if i < 5 and len(text) < 50:  # Crude header check
                    role = ParaRole.IGNORE
                else:
                    role = ParaRole.UNDETERMINED
            
            paragraph = Paragraph(index=i, text=text, role=role, q_num=q_num)
            self.paragraphs.append(paragraph)
            last_role = role
    
    def renumber_questions(self) -> None:
        """Renumber questions and answers sequentially."""
        q_counter = 0
        current_q_num_for_answers = 0
        
        for para in self.paragraphs:
            if para.role == ParaRole.QUESTION:
                q_counter += 1
                para.q_num = q_counter
                current_q_num_for_answers = q_counter
            elif para.role == ParaRole.ANSWER:
                # Assign answer to the most recently seen question number
                para.q_num = current_q_num_for_answers
            else:  # IGNORE or UNDETERMINED
                para.q_num = None
        
        self._current_q_num = q_counter
    
    def change_paragraph_role(self, index: int, new_role: ParaRole) -> bool:
        """
        Change the role of a paragraph.
        
        Args:
            index: Index of the paragraph to change
            new_role: New role to assign
            
        Returns:
            bool: True if renumbering is needed, False otherwise
        """
        if 0 <= index < len(self.paragraphs):
            old_role = self.paragraphs[index].role
            self.paragraphs[index].role = new_role
            
            # If changing to/from QUESTION, we need to renumber
            if old_role == ParaRole.QUESTION or new_role == ParaRole.QUESTION:
                return True
        return False
    
    def merge_paragraph_up(self, index: int) -> bool:
        """
        Merge a paragraph into the previous answer block.
        
        Args:
            index: Index of the paragraph to merge
            
        Returns:
            bool: True if renumbering is needed, False otherwise
        """
        if index <= 0 or index >= len(self.paragraphs):
            return False
            
        # Find the effective q_num of the *preceding* block
        preceding_q_num = None
        for prev_idx in range(index - 1, -1, -1):
            if self.paragraphs[prev_idx].q_num is not None:
                preceding_q_num = self.paragraphs[prev_idx].q_num
                break

        if preceding_q_num is not None:
            old_role = self.paragraphs[index].role
            self.paragraphs[index].role = ParaRole.ANSWER
            self.paragraphs[index].q_num = preceding_q_num
            
            # If it was a QUESTION, we need renumbering
            if old_role == ParaRole.QUESTION:
                return True
        return False
    
    def get_qa_data(self) -> Tuple[Dict[int, Dict[str, Any]], int]:
        """
        Get structured Q&A data for export.
        
        Returns:
            Tuple containing dictionary of QA pairs and question count
        """
        questions_data = {}  # {q_num: {'question': text, 'answers': [text]}}
        q_count = 0

        # First pass: Collect questions
        for para in self.paragraphs:
            if para.role == ParaRole.QUESTION:
                q_num = para.q_num
                if q_num is not None:
                    q_count += 1
                    questions_data[q_num] = {'number': q_num, 'question': para.text, 'answers': []}

        # Second pass: Collect answers
        for para in self.paragraphs:
            if para.role == ParaRole.ANSWER and para.q_num in questions_data:
                questions_data[para.q_num]['answers'].append(para.text)

        return questions_data, q_count
    
    def save_to_csv(self, save_path: str) -> bool:
        """
        Save the verified Q&A pairs to a CSV file.
        
        Args:
            save_path: Path to save the CSV file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            questions_data, _ = self.get_qa_data()
            
            # Prepare data for CSV
            csv_data = []
            for q_num in sorted(questions_data.keys()):
                q_data = questions_data[q_num]
                # Format: Question Number. Question Text in first column
                # Answer paragraphs in subsequent columns
                row = [f"{q_data['number']}. {q_data['question']}"] + q_data['answers']
                csv_data.append(row)
            
            # Use FileService to save CSV
            return FileService.save_data_to_csv(csv_data, save_path)
            
        except Exception as e:
            logger.error(f"Failed to prepare CSV data: {e}", exc_info=True)
            return False

    def get_question_count(self) -> int:
        """Get the current number of questions in the document."""
        return sum(1 for p in self.paragraphs if p.role == ParaRole.QUESTION)
    
    def set_expected_question_count(self, count: int) -> None:
        """Set the expected question count."""
        if count > 0:
            self.expected_question_count = count
            
    def cancel_loading(self) -> None:
        """
        Attempt to cancel any ongoing loading or analysis operations.
        Note: This doesn't actually stop the threads, since Python threads
        can't be forcibly terminated, but it allows the Document to be
        reset to a clean state.
        """
        self._loading_thread = None
        self._analyzing_thread = None