"""
AI-based paragraph analyzer using scikit-learn.
"""
import logging
import os
import re
import pickle
import platform
from datetime import datetime
from typing import List, Set, Tuple, Callable, Dict, Any

import numpy as np

from services.analyzers.base_analyzer import BaseAnalyzer
from services.analyzers.heuristic_analyzer import HeuristicAnalyzer

logger = logging.getLogger(__name__)

# Try to import sklearn, but allow falling back if not available
try:
    from sklearn.feature_extraction.text import CountVectorizer
    SKLEARN_AVAILABLE = True
except ImportError:
    logger.warning("scikit-learn not available. AI analyzer will fall back to heuristic.")
    SKLEARN_AVAILABLE = False

class AIAnalyzer(BaseAnalyzer):
    """Analyzer that uses a machine learning model to identify questions and answers."""
    
    def __init__(self):
        """Initialize the AI analyzer."""
        # Create a dedicated logger for detailed diagnostics
        self.logger = logging.getLogger("ai_analyzer")
        
        # Set up user data directory (platform-specific)
        self.app_name = "QA_Verifier"
        if platform.system() == "Windows":
            self.user_data_dir = os.path.join(os.environ["APPDATA"], self.app_name)
        elif platform.system() == "Darwin":  # macOS
            self.user_data_dir = os.path.join(os.path.expanduser("~/Library/Application Support"), self.app_name)
        else:  # Linux and others
            self.user_data_dir = os.path.join(os.path.expanduser("~/.local/share"), self.app_name)
        
        # Define paths for user data
        self.model_path = os.path.join(self.user_data_dir, "qa_classifier.pkl")
        self.vocab_path = os.path.join(self.user_data_dir, "vocabulary.npy")
        
        # Keep track of file paths for diagnostics
        self.logger.info(f"User data directory: {self.user_data_dir}")
        self.logger.info(f"Model path: {self.model_path}")
        self.logger.info(f"Vocabulary path: {self.vocab_path}")
        
        # Set up fallback analyzer
        self.fallback_analyzer = HeuristicAnalyzer()
        
        # Model and vectorizer will be loaded during initialization
        self.model = None
        self.vectorizer = None
        self.model_classes = None
        
        # Initialize the model if scikit-learn is available
        if SKLEARN_AVAILABLE:
            self._initialize_model()
            
            # Log initialization result
            if self.model is None:
                self.logger.warning("Failed to initialize AI model - falling back to heuristic")
            else:
                self.logger.info("AI model successfully initialized")
        else:
            self.logger.warning("scikit-learn not available - AI functionality disabled")
    
    def _initialize_model(self):
        """
        Initialize the model and vectorizer.
        """
        try:
            # Check if the model file exists
            if not os.path.exists(self.model_path):
                self.logger.warning(f"Model file not found: {self.model_path}")
                return
            
            # Check if file is readable and has content
            if not os.access(self.model_path, os.R_OK):
                self.logger.warning(f"Model file exists but is not readable: {self.model_path}")
                return
                
            # Check file size
            file_size = os.path.getsize(self.model_path)
            if file_size < 100:  # Arbitrary small size that's too small for a valid model
                self.logger.warning(f"Model file is too small ({file_size} bytes): {self.model_path}")
                return
                
            # Get file modification time
            mod_time = os.path.getmtime(self.model_path)
            self.logger.info(f"Loading model (size: {file_size} bytes, modified: {datetime.fromtimestamp(mod_time).isoformat()})")
            
            # Load the model with explicit error handling
            try:
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                self.logger.info(f"Successfully loaded model")
                
                # Store model classes if available
                if hasattr(self.model, 'classes_'):
                    self.model_classes = self.model.classes_
                    self.logger.info(f"Model classes: {self.model_classes}")
            except Exception as e:
                self.logger.error(f"Error loading model: {e}")
                return
            
            # Check if vocabulary file exists and is readable
            if not os.path.exists(self.vocab_path):
                self.logger.warning(f"Vocabulary file not found: {self.vocab_path}")
                return
                
            if not os.access(self.vocab_path, os.R_OK):
                self.logger.warning(f"Vocabulary file exists but is not readable: {self.vocab_path}")
                return
                
            # Initialize vectorizer with explicit error handling
            try:
                vocabulary = np.load(self.vocab_path, allow_pickle=True).item()
                self.vectorizer = CountVectorizer(vocabulary=vocabulary)
                self.logger.info(f"Successfully loaded vocabulary with {len(vocabulary)} features")
            except Exception as e:
                self.logger.error(f"Error loading vocabulary: {e}")
                self.model = None  # Reset model since we need both
                return
                
            self.logger.info("AI model and vectorizer successfully initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing AI model: {e}", exc_info=True)
            self.model = None
            self.vectorizer = None
    
    def analyze(self, paragraphs: List[str], status_callback: Callable[[str], None]) -> Tuple[Set[int], int]:
        """
        Analyze paragraphs using AI.
        
        Args:
            paragraphs: List of paragraph texts
            status_callback: Callback function for status updates
            
        Returns:
            Tuple containing set of question indices and estimated question count
        """
        # Check if model is available
        if not SKLEARN_AVAILABLE or self.model is None or self.vectorizer is None:
            self.logger.warning("AI model not available - using fallback analyzer")
            status_callback("AI model not available. Falling back to heuristic analysis...")
            return self.fallback_analyzer.analyze(paragraphs, status_callback)
        
        self.logger.info(f"Running AI-based analysis on {len(paragraphs)} paragraphs")
        status_callback("Running AI-based analysis...")
        
        # Get estimated count (using heuristic method)
        estimated_count = self.fallback_analyzer._estimate_question_count(paragraphs, status_callback)
        self.logger.info(f"Estimated question count: {estimated_count}")
        status_callback(f"Estimated question count from document structure: {estimated_count}")
        
        # Run AI model to classify each paragraph
        question_indices = self._classify_paragraphs(paragraphs, status_callback)
        self.logger.info(f"AI model identified {len(question_indices)} questions, expected ~{estimated_count}")
        
        # If we got too few questions, fall back to heuristics
        if len(question_indices) < estimated_count * 0.5:
            self.logger.warning(f"AI model found too few questions ({len(question_indices)}) compared to expected ({estimated_count})")
            status_callback(f"AI model found too few questions. Falling back to heuristic analysis...")
            return self.fallback_analyzer.analyze(paragraphs, status_callback)
        
        return question_indices, estimated_count
    
    def _classify_paragraphs(self, paragraphs: List[str], status_callback: Callable[[str], None]) -> Set[int]:
        """
        Classify paragraphs using the model.
        
        Args:
            paragraphs: List of paragraph texts
            status_callback: Callback function for status updates
            
        Returns:
            Set of paragraph indices classified as questions
        """
        question_indices = set()
        
        # Double-check model is loaded
        if self.model is None or self.vectorizer is None:
            self.logger.warning("Model or vectorizer not available for classification")
            return self.fallback_analyzer._identify_questions(
                paragraphs, 
                self.fallback_analyzer._estimate_question_count(paragraphs, status_callback),
                status_callback
            )
        
        try:
            self.logger.info(f"Starting AI classification of {len(paragraphs)} paragraphs")
            
            # Preprocess paragraphs
            processed_paragraphs = self._preprocess_paragraphs(paragraphs)
            self.logger.info(f"Preprocessed {len(processed_paragraphs)} paragraphs")
            
            # Convert paragraphs to feature vectors
            X = self.vectorizer.transform(processed_paragraphs).toarray()
            self.logger.info(f"Created feature matrix with shape {X.shape}")
            
            # Process in batches to avoid memory issues
            batch_size = 32
            num_paragraphs = len(paragraphs)
            
            # Find the question class index
            question_class_idx = None
            if hasattr(self.model, 'classes_') and self.model_classes is not None:
                # Find the index that corresponds to 'question'
                for i, cls in enumerate(self.model_classes):
                    if str(cls) == '2' or str(cls) == 'question':  # Look for either the index or name
                        question_class_idx = i
                        self.logger.info(f"Found question class at index {i} in {self.model_classes}")
                        break
            
            if question_class_idx is None:
                # Default assumption: 0=answer, 1=ignore, 2=question
                question_class_idx = 2
                self.logger.info(f"Using default question class index: {question_class_idx}")
            
            # Log predictions for first few paragraphs
            debug_samples = []
            
            for start_idx in range(0, num_paragraphs, batch_size):
                end_idx = min(start_idx + batch_size, num_paragraphs)
                batch = X[start_idx:end_idx]
                
                # Run model prediction
                predictions = self.model.predict(batch)
                
                # Collect debug samples for the first batch
                if start_idx == 0:
                    for i, pred in enumerate(predictions[:min(5, len(predictions))]):
                        p_text = paragraphs[i][:50] + "..." if len(paragraphs[i]) > 50 else paragraphs[i]
                        debug_samples.append(f"Para {i}: '{p_text}' → Class: {pred}")
                
                # Extract question indices based on determined class index
                for i, pred in enumerate(predictions):
                    if pred == question_class_idx:
                        question_indices.add(start_idx + i)
                
                # Update status
                status_callback(f"Analyzed {end_idx}/{num_paragraphs} paragraphs...")
            
            # Log sample predictions
            for sample in debug_samples:
                self.logger.info(sample)
                
            self.logger.info(f"AI model identified {len(question_indices)} questions")
            status_callback(f"AI model identified {len(question_indices)} questions.")
            
        except Exception as e:
            self.logger.error(f"Error in AI classification: {e}", exc_info=True)
            status_callback("Error in AI analysis. Falling back to heuristic method...")
            return self.fallback_analyzer._identify_questions(
                paragraphs, 
                self.fallback_analyzer._estimate_question_count(paragraphs, status_callback),
                status_callback
            )
        
        return question_indices
    
    def _preprocess_paragraphs(self, paragraphs: List[str]) -> List[str]:
        """
        Preprocess paragraphs for the model.
        
        Args:
            paragraphs: List of paragraph texts
            
        Returns:
            List of preprocessed paragraph texts
        """
        processed = []
        for p in paragraphs:
            # Basic preprocessing:
            text = p.lower()
            text = re.sub(r'[^\w\s\?]', ' ', text)  # Keep question marks
            text = re.sub(r'\s+', ' ', text).strip()
            processed.append(text)
        
        # Log first few processed paragraphs
        for i in range(min(3, len(processed))):
            self.logger.debug(f"Preprocessed [{i}]: {processed[i][:50]}...")
            
        return processed