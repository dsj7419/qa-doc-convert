"""
AI-based paragraph analyzer using transformer models with ONNX runtime.
"""
import logging
import os
import platform
import threading
from datetime import datetime
from typing import List, Set, Tuple, Callable, Dict, Any, Optional
import json
import numpy as np

from services.analyzers.base_analyzer import BaseAnalyzer
from services.analyzers.heuristic_analyzer import HeuristicAnalyzer
from models.paragraph import ParaRole

logger = logging.getLogger(__name__)

# Try to import transformers and onnxruntime, but allow falling back if not available
try:
    from transformers import AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    logger.warning("transformers not available. AI analyzer will fall back to heuristic.")
    TRANSFORMERS_AVAILABLE = False

try:
    import onnxruntime
    ONNX_AVAILABLE = True
except ImportError:
    logger.warning("onnxruntime not available. AI analyzer will fall back to heuristic.")
    ONNX_AVAILABLE = False

class AIAnalyzer(BaseAnalyzer):
    """Analyzer that uses a transformer model to identify questions and answers."""
    
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
        self.fine_tuned_model_dir = os.path.join(self.user_data_dir, "fine_tuned_model")
        self.onnx_model_path = os.path.join(self.user_data_dir, "qa_classifier.onnx")
        self.label_map_path = os.path.join(self.fine_tuned_model_dir, "label_map.json")
        
        # Keep track of file paths for diagnostics
        self.logger.info(f"User data directory: {self.user_data_dir}")
        self.logger.info(f"ONNX model path: {self.onnx_model_path}")
        self.logger.info(f"Fine-tuned model directory: {self.fine_tuned_model_dir}")
        
        # Set up fallback analyzer
        self.fallback_analyzer = HeuristicAnalyzer()
        
        # Model components to be initialized
        self.onnx_session = None
        self.tokenizer = None
        self.label_map = None
        self.id_to_role_map = None
        
        # Initialize the model
        if TRANSFORMERS_AVAILABLE and ONNX_AVAILABLE:
            self._initialize_model()
            
            # Log initialization result
            if self.onnx_session is None:
                self.logger.warning("Failed to initialize ONNX model - falling back to heuristic")
            else:
                self.logger.info("ONNX model successfully initialized")
        else:
            self.logger.warning("Required dependencies not available - AI functionality disabled")
    
    def _initialize_model(self):
        """
        Initialize the ONNX model and tokenizer.
        """
        try:
            # Check if the ONNX model file exists
            if not os.path.exists(self.onnx_model_path):
                self.logger.warning(f"ONNX model file not found: {self.onnx_model_path}")
                # Check if we can use the PyTorch model directly as a fallback
                if os.path.exists(os.path.join(self.fine_tuned_model_dir, "pytorch_model.bin")):
                    self.logger.info("PyTorch model exists but no ONNX model. Please run training again.")
                return
            
            # Check if file is readable and has content
            if not os.access(self.onnx_model_path, os.R_OK):
                self.logger.warning(f"ONNX model file exists but is not readable: {self.onnx_model_path}")
                return
                
            # Check file size
            file_size = os.path.getsize(self.onnx_model_path)
            if file_size < 1000:  # Arbitrary small size that's too small for a valid model
                self.logger.warning(f"ONNX model file is too small ({file_size} bytes): {self.onnx_model_path}")
                return
                
            # Get file modification time
            mod_time = os.path.getmtime(self.onnx_model_path)
            self.logger.info(f"Loading ONNX model (size: {file_size} bytes, modified: {datetime.fromtimestamp(mod_time).isoformat()})")
            
            # Load the ONNX model with explicit error handling
            try:
                # Create an ONNX Runtime inference session
                self.onnx_session = onnxruntime.InferenceSession(self.onnx_model_path)
                self.logger.info(f"Successfully loaded ONNX model")
                
                # Log input and output names for debugging
                input_names = [input.name for input in self.onnx_session.get_inputs()]
                output_names = [output.name for output in self.onnx_session.get_outputs()]
                self.logger.info(f"ONNX model input names: {input_names}")
                self.logger.info(f"ONNX model output names: {output_names}")
            except Exception as e:
                self.logger.error(f"Error loading ONNX model: {e}")
                return
            
            # Load the tokenizer
            try:
                if os.path.exists(self.fine_tuned_model_dir):
                    self.tokenizer = AutoTokenizer.from_pretrained(self.fine_tuned_model_dir)
                    self.logger.info(f"Successfully loaded tokenizer from {self.fine_tuned_model_dir}")
                else:
                    self.logger.warning(f"Fine-tuned model directory not found: {self.fine_tuned_model_dir}")
                    return
            except Exception as e:
                self.logger.error(f"Error loading tokenizer: {e}")
                self.onnx_session = None  # Reset session since we need both
                return
            
            # Load the label map
            try:
                if os.path.exists(self.label_map_path):
                    with open(self.label_map_path, 'r') as f:
                        self.label_map = json.load(f)
                    self.logger.info(f"Successfully loaded label map: {self.label_map}")
                    
                    # Create ID to ParaRole enum mapping
                    self.id_to_role_map = {}
                    for id_str, role_str in self.label_map.items():
                        try:
                            # Convert string ID to int
                            id_int = int(id_str)
                            # Convert string role to ParaRole enum
                            role_enum = getattr(ParaRole, role_str.upper())
                            self.id_to_role_map[id_int] = role_enum
                        except (ValueError, AttributeError) as e:
                            self.logger.warning(f"Error in label map entry {id_str}:{role_str} - {e}")
                    
                    self.logger.info(f"Created ID to role mapping: {self.id_to_role_map}")
                else:
                    self.logger.warning(f"Label map file not found: {self.label_map_path}")
                    
                    # Create a default mapping based on convention
                    self.logger.info("Creating default ID to role mapping")
                    self.id_to_role_map = {
                        0: ParaRole.ANSWER,
                        1: ParaRole.IGNORE,
                        2: ParaRole.QUESTION
                    }
                    self.logger.info(f"Created default ID to role mapping: {self.id_to_role_map}")
            except Exception as e:
                self.logger.error(f"Error loading label map: {e}")
                self.onnx_session = None  # Reset session since we need all components
                self.tokenizer = None
                return
                
            self.logger.info("AI model, tokenizer, and label map successfully initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing AI model: {e}", exc_info=True)
            self.onnx_session = None
            self.tokenizer = None
            self.label_map = None
            self.id_to_role_map = None
    
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
        if not (TRANSFORMERS_AVAILABLE and ONNX_AVAILABLE) or self.onnx_session is None or self.tokenizer is None:
            self.logger.warning("ONNX model not available - using fallback analyzer")
            status_callback("AI model not available. Falling back to heuristic analysis...")
            return self.fallback_analyzer.analyze(paragraphs, status_callback)
        
        self.logger.info(f"Running transformer-based analysis on {len(paragraphs)} paragraphs")
        status_callback("Running transformer-based analysis...")
        
        # Get estimated count (using heuristic method)
        estimated_count = self.fallback_analyzer._estimate_question_count(paragraphs, status_callback)
        self.logger.info(f"Estimated question count: {estimated_count}")
        status_callback(f"Estimated question count from document structure: {estimated_count}")
        
        # Run AI model to classify each paragraph
        question_indices = self._classify_paragraphs(paragraphs, status_callback)
        self.logger.info(f"Transformer model identified {len(question_indices)} questions, expected ~{estimated_count}")
        
        # If we got too few questions, fall back to heuristics
        if len(question_indices) < estimated_count * 0.5:
            self.logger.warning(f"AI model found too few questions ({len(question_indices)}) compared to expected ({estimated_count})")
            status_callback(f"AI model found too few questions. Falling back to heuristic analysis...")
            return self.fallback_analyzer.analyze(paragraphs, status_callback)
        
        return question_indices, estimated_count
    
    def analyze_async(self, paragraphs: List[str], status_callback: Callable[[str], None], 
                      completion_callback: Callable[[Set[int], int, Optional[Exception]], None]) -> threading.Thread:
        """
        Analyze paragraphs using AI asynchronously.
        
        Args:
            paragraphs: List of paragraph texts
            status_callback: Callback function for status updates
            completion_callback: Callback function receiving (indices, count, exception) upon completion
            
        Returns:
            Thread object
        """
        def _analyze_thread():
            try:
                # Check if model is available
                if not (TRANSFORMERS_AVAILABLE and ONNX_AVAILABLE) or self.onnx_session is None or self.tokenizer is None:
                    self.logger.warning("ONNX model not available - using fallback analyzer")
                    status_callback("AI model not available. Falling back to heuristic analysis...")
                    # Run fallback analyzer but still in this thread
                    question_indices, estimated_count = self.fallback_analyzer.analyze(paragraphs, status_callback)
                    completion_callback(question_indices, estimated_count, None)
                    return
                
                self.logger.info(f"Running transformer-based analysis on {len(paragraphs)} paragraphs")
                status_callback("Running transformer-based analysis...")
                
                # Get estimated count (using heuristic method)
                estimated_count = self.fallback_analyzer._estimate_question_count(paragraphs, status_callback)
                self.logger.info(f"Estimated question count: {estimated_count}")
                status_callback(f"Estimated question count from document structure: {estimated_count}")
                
                # Run classification asynchronously
                def on_classification_complete(question_indices, exception):
                    if exception:
                        self.logger.error(f"Error in AI classification: {exception}")
                        status_callback("Error in AI classification. Falling back to heuristic analysis...")
                        try:
                            # Fall back to heuristic analyzer
                            q_indices, est_count = self.fallback_analyzer.analyze(paragraphs, status_callback)
                            completion_callback(q_indices, est_count, None)
                        except Exception as e:
                            completion_callback(None, 0, e)
                        return
                        
                    self.logger.info(f"Transformer model identified {len(question_indices)} questions, expected ~{estimated_count}")
                    
                    # If we got too few questions, fall back to heuristics
                    if len(question_indices) < estimated_count * 0.5:
                        self.logger.warning(f"AI model found too few questions ({len(question_indices)}) compared to expected ({estimated_count})")
                        status_callback(f"AI model found too few questions. Falling back to heuristic analysis...")
                        try:
                            # Fall back to heuristic analyzer
                            q_indices, est_count = self.fallback_analyzer.analyze(paragraphs, status_callback)
                            completion_callback(q_indices, est_count, None)
                        except Exception as e:
                            completion_callback(None, 0, e)
                    else:
                        # Use AI results
                        completion_callback(question_indices, estimated_count, None)
                
                # Start classification in this thread (it's already in a background thread)
                self._classify_paragraphs_async(paragraphs, status_callback, on_classification_complete)
                
            except Exception as e:
                self.logger.error(f"Error in async analysis: {e}", exc_info=True)
                completion_callback(None, 0, e)
        
        # Create and start thread
        thread = threading.Thread(target=_analyze_thread)
        thread.daemon = True
        thread.start()
        
        return thread
    
    def _classify_paragraphs_async(self, paragraphs: List[str], status_callback: Callable[[str], None],
                                  completion_callback: Callable[[Set[int], Optional[Exception]], None]) -> None:
        """
        Classify paragraphs using the ONNX model asynchronously.
        
        Args:
            paragraphs: List of paragraph texts
            status_callback: Callback function for status updates
            completion_callback: Callback function receiving (question_indices, exception) upon completion
        """
        try:
            # This method is expected to be called from an already-running background thread
            # so we perform the work directly instead of creating another thread
            question_indices = self._classify_paragraphs(paragraphs, status_callback)
            completion_callback(question_indices, None)
        except Exception as e:
            self.logger.error(f"Error in classification: {e}", exc_info=True)
            completion_callback(None, e)
    
    def _classify_paragraphs(self, paragraphs: List[str], status_callback: Callable[[str], None]) -> Set[int]:
        """
        Classify paragraphs using the ONNX model.
        
        Args:
            paragraphs: List of paragraph texts
            status_callback: Callback function for status updates
            
        Returns:
            Set of paragraph indices classified as questions
        """
        question_indices = set()
        
        # Double-check model is loaded
        if self.onnx_session is None or self.tokenizer is None or self.id_to_role_map is None:
            self.logger.warning("ONNX session, tokenizer, or ID-to-role map not available for classification")
            return self.fallback_analyzer._identify_questions(
                paragraphs, 
                self.fallback_analyzer._estimate_question_count(paragraphs, status_callback),
                status_callback
            )
        
        try:
            self.logger.info(f"Starting transformer-based classification of {len(paragraphs)} paragraphs")
            
            # Process in batches to avoid memory issues
            batch_size = 16
            num_paragraphs = len(paragraphs)
            
            # Find the question class
            question_role_enum = ParaRole.QUESTION
            
            # Log debug samples
            debug_samples = []
            
            for start_idx in range(0, num_paragraphs, batch_size):
                end_idx = min(start_idx + batch_size, num_paragraphs)
                batch = paragraphs[start_idx:end_idx]
                status_callback(f"Analyzing paragraphs {start_idx+1}-{end_idx} of {num_paragraphs}...")
                
                # Tokenize the batch
                inputs = self.tokenizer(batch, padding=True, truncation=True, return_tensors="np")
                
                # Prepare inputs for ONNX session
                ort_inputs = {}
                for input_name in [i.name for i in self.onnx_session.get_inputs()]:
                    if input_name in inputs:
                        ort_inputs[input_name] = inputs[input_name]
                
                # Run inference
                ort_outputs = self.onnx_session.run(None, ort_inputs)
                
                # Process outputs - typically logits are the first output
                logits = ort_outputs[0]
                predictions = np.argmax(logits, axis=1)
                
                # Optional: Calculate probabilities for confidence scoring
                probabilities = self._softmax(logits)
                
                # Collect debug samples for logging
                if start_idx == 0:
                    for i in range(min(5, len(batch))):
                        pred_id = predictions[i]
                        pred_role = self.id_to_role_map.get(pred_id, "UNKNOWN")
                        confidence = round(float(probabilities[i][pred_id]) * 100, 2)
                        sample_text = batch[i][:50] + "..." if len(batch[i]) > 50 else batch[i]
                        debug_samples.append(f"Para {i}: '{sample_text}' - Class: {pred_role.name}, Confidence: {confidence}%")
                
                # Identify question paragraphs
                for i, pred_id in enumerate(predictions):
                    predicted_role = self.id_to_role_map.get(pred_id)
                    if predicted_role == question_role_enum:
                        global_idx = start_idx + i
                        question_indices.add(global_idx)
                        
                        # Optionally log high-confidence questions for debugging
                        if probabilities[i][pred_id] > 0.9:
                            self.logger.debug(f"High confidence question at idx {global_idx}: {paragraphs[global_idx][:50]}...")
            
            # Log sample predictions
            for sample in debug_samples:
                self.logger.info(sample)
                
            self.logger.info(f"Transformer model identified {len(question_indices)} questions")
            status_callback(f"Transformer model identified {len(question_indices)} questions.")
            
        except Exception as e:
            self.logger.error(f"Error in transformer classification: {e}", exc_info=True)
            status_callback("Error in AI analysis. Falling back to heuristic method...")
            return self.fallback_analyzer._identify_questions(
                paragraphs, 
                self.fallback_analyzer._estimate_question_count(paragraphs, status_callback),
                status_callback
            )
        
        return question_indices
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """
        Calculate softmax probabilities from logits.
        
        Args:
            x: Input array of logits
            
        Returns:
            Array of probabilities
        """
        # Subtract max for numerical stability
        exp_x = np.exp(x - np.max(x, axis=1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=1, keepdims=True)