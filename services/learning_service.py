"""
Learning service for managing AI model training and improvement.
"""
import logging
import os
import sys
import json
import pickle
import numpy as np
import shutil
import platform
import subprocess
from datetime import datetime
from typing import Callable, List, Dict, Any, Optional, Tuple

from models.paragraph import Paragraph, ParaRole

logger = logging.getLogger(__name__)

# Try to import sklearn, but handle gracefully if not available
try:
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import LabelEncoder
    SKLEARN_AVAILABLE = True
except ImportError:
    logger.warning("scikit-learn not available. AI learning features will be disabled.")
    SKLEARN_AVAILABLE = False

class LearningService:
    """Service for collecting training data and improving the AI model."""
    
    def __init__(self):
        """Initialize the learning service."""
        # Set up persistent data directory
        self.app_name = "QA_Verifier"
        
        # Get user data directory (platform-specific)
        if platform.system() == "Windows":
            self.user_data_dir = os.path.join(os.environ["APPDATA"], self.app_name)
        elif platform.system() == "Darwin":  # macOS
            self.user_data_dir = os.path.join(os.path.expanduser("~/Library/Application Support"), self.app_name)
        else:  # Linux and others
            self.user_data_dir = os.path.join(os.path.expanduser("~/.local/share"), self.app_name)
        
        # Create directory if it doesn't exist
        os.makedirs(self.user_data_dir, exist_ok=True)
        
        # Create a debug log file
        self.debug_log_path = os.path.join(self.user_data_dir, "ai_debug.log")
        self._log_debug(f"Initializing LearningService at {datetime.now()}")
        self._log_debug(f"User data directory: {self.user_data_dir}")
        
        # Get bundled resources directory for initial model/data
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # Running as PyInstaller bundle
            self.resources_dir = os.path.join(sys._MEIPASS, "resources")
            self._log_debug(f"Running as PyInstaller bundle, resources dir: {self.resources_dir}")
        else:
            # Running in normal Python environment
            self.resources_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources")
            self._log_debug(f"Running in normal Python environment, resources dir: {self.resources_dir}")
        
        # Define paths for user data
        self.training_data_path = os.path.join(self.user_data_dir, "training_data.json")
        self.model_path = os.path.join(self.user_data_dir, "qa_classifier.pkl")
        self.vocab_path = os.path.join(self.user_data_dir, "vocabulary.npy")
        
        self._log_debug(f"Training data path: {self.training_data_path}")
        self._log_debug(f"Model path: {self.model_path}")
        self._log_debug(f"Vocabulary path: {self.vocab_path}")
        
        # Initialize or load training data
        self.training_data = self._load_training_data()
        
        # Track whether the training data has changed
        self.data_changed = False
        
        # Copy initial resources if needed
        self._init_resources()
        
        # Force training if we have data but no model
        total_examples = sum(len(examples) for role, examples in self.training_data.items())
        if total_examples >= 10 and not os.path.exists(self.model_path) and SKLEARN_AVAILABLE:
            self._log_debug(f"Found {total_examples} training examples but no model file. Forcing training on startup.")
            self.data_changed = True
            self.train_model(force=True)
    
    def _log_debug(self, message: str) -> None:
        """Write a debug message to the log file."""
        try:
            with open(self.debug_log_path, 'a', encoding='utf-8') as f:
                f.write(f"{message}\n")
        except Exception as e:
            logger.error(f"Error writing to debug log: {e}")

    def is_manual_training_mode(self) -> bool:
        """
        Check if manual training mode is enabled.
        
        Returns:
            bool: True if manual training mode is enabled
        """
        return getattr(self, '_manual_training_mode', True)  # Default to True

    def set_manual_training_mode(self, enabled: bool) -> None:
        """
        Set manual training mode.
        
        Args:
            enabled: Whether to enable manual training mode
        """
        self._manual_training_mode = enabled
        self._log_debug(f"Manual training mode set to: {enabled}")
    
    def _init_resources(self) -> None:
        """Initialize resources, copying bundled files if needed."""
        self._log_debug(f"Initializing resources at {datetime.now()}")
        
        # Check if we need to copy initial model
        if not os.path.exists(self.model_path):
            self._log_debug(f"Model doesn't exist at {self.model_path}")
            
            initial_model_path = os.path.join(self.resources_dir, "qa_classifier.pkl")
            self._log_debug(f"Checking for initial model at {initial_model_path}")
            
            if os.path.exists(initial_model_path):
                self._log_debug(f"Initial model exists, copying...")
                try:
                    shutil.copy2(initial_model_path, self.model_path)
                    self._log_debug(f"Copied initial model to {self.model_path}")
                except Exception as e:
                    self._log_debug(f"Error copying initial model: {e}")
            else:
                self._log_debug(f"Initial model not found")
        
        # Check if we need to copy initial vocabulary
        if not os.path.exists(self.vocab_path):
            self._log_debug(f"Vocabulary doesn't exist at {self.vocab_path}")
            
            initial_vocab_path = os.path.join(self.resources_dir, "vocabulary.npy")
            self._log_debug(f"Checking for initial vocabulary at {initial_vocab_path}")
            
            if os.path.exists(initial_vocab_path):
                self._log_debug(f"Initial vocabulary exists, copying...")
                try:
                    shutil.copy2(initial_vocab_path, self.vocab_path)
                    self._log_debug(f"Copied initial vocabulary to {self.vocab_path}")
                except Exception as e:
                    self._log_debug(f"Error copying initial vocabulary: {e}")
            else:
                self._log_debug(f"Initial vocabulary not found")
    
    def _load_training_data(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Load training data from file or initialize if not exists.
        
        Returns:
            Dict with training data
        """
        self._log_debug(f"Loading training data at {datetime.now()}")
        
        if os.path.exists(self.training_data_path):
            self._log_debug(f"Training data file exists at {self.training_data_path}")
            try:
                with open(self.training_data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._log_debug(f"Loaded {sum(len(v) for v in data.values())} training examples")
                return data
            except Exception as e:
                self._log_debug(f"Error loading training data: {e}")
                logger.error(f"Error loading training data: {e}")
        else:
            self._log_debug(f"Training data file doesn't exist")
        
        # If user data doesn't exist but bundled data does, copy it
        bundled_data_path = os.path.join(self.resources_dir, "training_data.json")
        self._log_debug(f"Checking for bundled data at {bundled_data_path}")
        
        if os.path.exists(bundled_data_path):
            self._log_debug(f"Bundled data exists, loading...")
            try:
                with open(bundled_data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._log_debug(f"Loaded {sum(len(v) for v in data.values())} initial training examples")
                # Save to user directory
                with open(self.training_data_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                self._log_debug(f"Saved initial training data to {self.training_data_path}")
                return data
            except Exception as e:
                self._log_debug(f"Error loading initial training data: {e}")
                logger.error(f"Error loading initial training data: {e}")
        else:
            self._log_debug(f"Bundled data not found, initializing empty training data")
        
        # Initialize empty training data structure
        empty_data = {
            'question': [],
            'answer': [],
            'ignore': []
        }
        self._log_debug(f"Created empty training data structure")
        return empty_data
    
    def _save_training_data(self) -> bool:
        """
        Save training data to file.
        
        Returns:
            bool: Success flag
        """
        self._log_debug(f"Saving training data at {datetime.now()}")
        try:
            # Make sure the directory exists
            os.makedirs(os.path.dirname(self.training_data_path), exist_ok=True)
            
            # Log current state
            total_examples = sum(len(examples) for role, examples in self.training_data.items())
            self._log_debug(f"Saving {total_examples} training examples")
            
            # First write to a temporary file to avoid corruption
            temp_path = f"{self.training_data_path}.tmp"
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(self.training_data, f, indent=2)
                f.flush()  # Force flush to disk
                os.fsync(f.fileno())  # Ensure data is written to disk
            
            self._log_debug(f"Wrote temporary file: {os.path.getsize(temp_path)} bytes")
            
            # Then rename the temporary file to the actual file
            if os.path.exists(temp_path):
                # Add a backup copy just in case
                if os.path.exists(self.training_data_path):
                    backup_path = f"{self.training_data_path}.bak"
                    try:
                        shutil.copy2(self.training_data_path, backup_path)
                        self._log_debug(f"Created backup at {backup_path}")
                    except Exception as e:
                        self._log_debug(f"Warning: Failed to create backup: {e}")
                    
                    try:
                        os.remove(self.training_data_path)
                        self._log_debug(f"Removed existing file")
                    except Exception as e:
                        self._log_debug(f"Warning: Failed to remove existing file: {e}")
                
                try:
                    os.rename(temp_path, self.training_data_path)
                    self._log_debug(f"Renamed temporary file to {self.training_data_path}")
                except Exception as e:
                    self._log_debug(f"Error renaming temporary file: {e}")
                    # Try direct copy as fallback
                    try:
                        shutil.copy2(temp_path, self.training_data_path)
                        os.remove(temp_path)
                        self._log_debug(f"Used copy as fallback")
                    except Exception as e2:
                        self._log_debug(f"Error in copy fallback: {e2}")
                        return False
            else:
                self._log_debug(f"Error: Temporary file was not created")
                return False
            
            # Verify the file exists and has content
            if os.path.exists(self.training_data_path):
                file_size = os.path.getsize(self.training_data_path)
                self._log_debug(f"Final file exists: {file_size} bytes")
                if file_size == 0:
                    self._log_debug(f"Warning: Final file is empty!")
            else:
                self._log_debug(f"Error: Final file doesn't exist after save!")
                return False
            
            examples_count = sum(len(v) for v in self.training_data.values())
            self._log_debug(f"Saved {examples_count} training examples to {self.training_data_path}")
            logger.info(f"Saved {examples_count} training examples")
            return True
        except Exception as e:
            self._log_debug(f"Error saving training data: {e}")
            logger.error(f"Error saving training data: {e}")
            return False
        
    def get_sample_training_examples(self, count_per_role: int = 5) -> Dict[str, List[str]]:
        """
        Get a sample of training examples for each role.
        
        Args:
            count_per_role: Maximum number of examples per role
            
        Returns:
            Dictionary of role -> list of example texts
        """
        result = {}
        
        for role, examples in self.training_data.items():
            result[role] = []
            for example in examples[:count_per_role]:
                result[role].append(example.get('text', ''))
        
        return result
    
    def add_training_example(self, text: str, role: ParaRole) -> bool:
        """
        Add a training example from user correction.
        
        Args:
            text: Paragraph text
            role: Assigned role
            
        Returns:
            bool: True if a new example was added, False otherwise
        """
        # Skip if scikit-learn is not available
        if not SKLEARN_AVAILABLE:
            self._log_debug(f"Scikit-learn not available, skipping add_training_example")
            return False
        
        # Skip if the example is too short
        if len(text) < 10:
            self._log_debug(f"Example too short, skipping: {text[:20]}...")
            return False
        
        self._log_debug(f"Adding training example: {text[:50]}... as {role.name.lower()}")
            
        # Convert ParaRole enum to string
        role_str = role.name.lower()
        
        # Check if this exact example already exists
        is_duplicate = False
        for example in self.training_data[role_str]:
            if example.get('text', '') == text:
                is_duplicate = True
                self._log_debug(f"Example already exists as {role_str}, skipping")
                break
        
        if is_duplicate:
            return False
        
        # Check if this example exists with a different role (replace it)
        for other_role, examples in self.training_data.items():
            if other_role == role_str:
                continue
            
            for i, example in enumerate(examples[:]):  # Make a copy to avoid modifying during iteration
                if example.get('text', '') == text:
                    self._log_debug(f"Example exists with different role {other_role}, removing")
                    self.training_data[other_role].remove(example)
        
        # Add the example
        self.training_data[role_str].append({
            'text': text,
            'source': 'user_correction',
            'timestamp': datetime.now().isoformat()
        })
        
        # Mark data as changed
        self.data_changed = True
        
        self._log_debug(f"Added training example as {role_str}")
        
        # Save training data immediately
        self._save_training_data()
        
        return True
    
    def has_enough_data_to_train(self) -> bool:
        """
        Check if there's enough data to train a model.
        
        Returns:
            bool: True if there's enough data
        """
        # Log the current state of training data
        self._log_debug(f"Checking if enough data to train:")
        for role, examples in self.training_data.items():
            self._log_debug(f"  - {role}: {len(examples)} examples")
        
        # Calculate total examples
        total_examples = sum(len(examples) for role, examples in self.training_data.items())
        self._log_debug(f"Total examples: {total_examples}")
        
        # Make sure we have at least some examples of each class
        min_examples_per_class = 1  # Reduced from 5
        has_all_classes = all(len(examples) >= min_examples_per_class for role, examples in self.training_data.items())
        
        # Make sure we have a reasonable total (at least 10 examples overall)
        has_enough_total = total_examples >= 10
        
        # Final decision
        result = has_all_classes and has_enough_total
        self._log_debug(f"Has enough data to train: {result} (has_all_classes={has_all_classes}, has_enough_total={has_enough_total})")
        
        return result
    
    def train_model(self, force: bool = False) -> bool:
        """
        Train a new model if data has changed.
        
        Args:
            force: Force training even if data hasn't changed
            
        Returns:
            bool: Success flag
        """
        # Skip if scikit-learn is not available
        if not SKLEARN_AVAILABLE:
            self._log_debug(f"Scikit-learn not available. Cannot train model.")
            logger.warning("scikit-learn not available. Cannot train model.")
            return False
        
        self._log_debug(f"Train model called with force={force}, data_changed={self.data_changed}")
        
        # Skip if no data has changed and not forcing
        if not self.data_changed and not force:
            self._log_debug(f"No new training data. Skipping model training.")
            logger.info("No new training data. Skipping model training.")
            return False
        
        # Check if we have enough data
        if not self.has_enough_data_to_train():
            self._log_debug(f"Not enough training data to train a reliable model.")
            logger.info("Not enough training data to train a reliable model.")
            return False
        
        self._log_debug(f"Training AI model from collected data at {datetime.now()}...")
        logger.info("Training AI model from collected data...")
        
        try:
            # Prepare training data
            texts = []
            labels = []
            
            for role, examples in self.training_data.items():
                for example in examples:
                    texts.append(example['text'])
                    labels.append(role)
            
            self._log_debug(f"Prepared {len(texts)} examples for training")
            
            # Create vectorizer
            vectorizer = CountVectorizer(
                max_features=5000,
                ngram_range=(1, 2),
                stop_words='english'
            )
            
            # Fit vectorizer and transform texts
            X = vectorizer.fit_transform(texts).toarray()
            self._log_debug(f"Created feature matrix with shape {X.shape}")
            
            # Save vocabulary with improved error checking
            vocab_tmp = f"{self.vocab_path}.tmp"
            np.save(vocab_tmp, vectorizer.vocabulary_)
            if os.path.exists(vocab_tmp) and os.path.getsize(vocab_tmp) > 0:
                self._log_debug(f"Vocabulary file created successfully: {os.path.getsize(vocab_tmp)} bytes")
                if os.path.exists(self.vocab_path):
                    os.remove(self.vocab_path)
                    self._log_debug(f"Removed existing vocabulary file")
                os.rename(vocab_tmp, self.vocab_path)
                self._log_debug(f"Renamed vocabulary file to final path")
            else:
                self._log_debug(f"Error: Vocabulary file creation failed or is empty!")
                
            self._log_debug(f"Saved vocabulary with {len(vectorizer.vocabulary_)} features")
            
            # Encode labels
            le = LabelEncoder()
            y = le.fit_transform(labels)
            self._log_debug(f"Encoded labels: {list(le.classes_)}")
            
            # Train model
            model = LogisticRegression(max_iter=1000)
            model.fit(X, y)
            self._log_debug(f"Trained LogisticRegression model")
            
            # Save model with robust error handling
            model_tmp = f"{self.model_path}.tmp"
            try:
                with open(model_tmp, "wb") as f:
                    pickle.dump(model, f)
                self._log_debug(f"Wrote model to temporary file: {model_tmp}")
                
                # Verify the file was created and has content
                if os.path.exists(model_tmp) and os.path.getsize(model_tmp) > 0:
                    self._log_debug(f"Model file created successfully: {os.path.getsize(model_tmp)} bytes")
                    
                    if os.path.exists(self.model_path):
                        try:
                            os.remove(self.model_path)
                            self._log_debug(f"Removed existing model file")
                        except Exception as e:
                            self._log_debug(f"Warning: Error removing existing model file: {e}")
                    
                    try:
                        os.rename(model_tmp, self.model_path)
                        self._log_debug(f"Renamed model file to final path: {self.model_path}")
                        
                        if not os.path.exists(self.model_path):
                            self._log_debug(f"ERROR: Final model file doesn't exist after renaming!")
                            return False
                    except Exception as e:
                        self._log_debug(f"ERROR: Failed to rename model file: {e}")
                        return False
                else:
                    self._log_debug(f"ERROR: Model file was not created or is empty!")
                    return False
            except Exception as e:
                self._log_debug(f"ERROR: Failed to save model: {e}")
                return False
            
            # Reset change flag
            self.data_changed = False
            
            self._log_debug(f"Successfully trained and saved model with {len(texts)} examples")
            logger.info(f"Successfully trained and saved model with {len(texts)} examples")
            return True
            
        except Exception as e:
            self._log_debug(f"Error training model: {e}")
            logger.error(f"Error training model: {e}", exc_info=True)
            return False
    
    def collect_training_data_from_document(self, paragraphs: List[Paragraph]) -> None:
        """
        Collect training data from a completely processed document.
        
        Args:
            paragraphs: List of paragraphs with assigned roles
        """
        # Skip if scikit-learn is not available
        if not SKLEARN_AVAILABLE:
            self._log_debug(f"Scikit-learn not available, skipping collect_training_data_from_document")
            return
        
        self._log_debug(f"Collecting training data from document with {len(paragraphs)} paragraphs")
        
        # Track if we've added any new examples
        added_count = 0
        
        # Process each paragraph
        for para in paragraphs:
            # Skip undetermined paragraphs
            if para.role == ParaRole.UNDETERMINED:
                continue
            
            # Skip very short paragraphs
            if len(para.text) < 10:
                continue
            
            # Convert role to string
            role_str = para.role.name.lower()
            
            # Check if this exact example already exists
            if any(example['text'] == para.text for example in self.training_data[role_str]):
                continue
            
            # Add the example
            self.training_data[role_str].append({
                'text': para.text,
                'source': 'document',
                'timestamp': datetime.now().isoformat()
            })
            
            added_count += 1
        
        if added_count > 0:
            self._log_debug(f"Added {added_count} new training examples from document")
            logger.info(f"Added {added_count} new training examples from document")
            self.data_changed = True
            
            # Save training data immediately
            self._save_training_data()

    def collect_training_data_from_document_with_feedback(self, paragraphs: List[Paragraph], 
                                                    log_callback: Callable[[str, str], None]) -> bool:
        """
        Collect training data from a document with detailed feedback.
        
        Args:
            paragraphs: List of paragraphs with assigned roles
            log_callback: Callback for logging messages (takes message and level)
            
        Returns:
            bool: Success flag
        """
        # Skip if scikit-learn is not available
        if not SKLEARN_AVAILABLE:
            self._log_debug(f"Scikit-learn not available, skipping collection")
            log_callback("scikit-learn not available, skipping collection", "WARNING")
            return False
        
        self._log_debug(f"Collecting training data from {len(paragraphs)} paragraphs with feedback")
        log_callback(f"Collecting training data from {len(paragraphs)} paragraphs...", "INFO")
        
        # Track if we've added any new examples
        added_count = 0
        skipped_count = 0
        skipped_undetermined = 0
        skipped_short = 0
        skipped_duplicate = 0
        
        # Process each paragraph
        for para in paragraphs:
            # Skip undetermined paragraphs
            if para.role == ParaRole.UNDETERMINED:
                skipped_undetermined += 1
                continue
            
            # Skip very short paragraphs
            if len(para.text) < 10:
                skipped_short += 1
                continue
            
            # Convert role to string
            role_str = para.role.name.lower()
            
            # Check if this exact example already exists
            if any(example.get('text', '') == para.text for example in self.training_data[role_str]):
                skipped_duplicate += 1
                continue
            
            # Check if this example exists with a different role (replace it)
            for other_role, examples in self.training_data.items():
                if other_role == role_str:
                    continue
                
                for i, example in enumerate(examples[:]):  # Make a copy to avoid modifying during iteration
                    if example.get('text', '') == para.text:
                        self._log_debug(f"Example exists with different role {other_role}, removing")
                        self.training_data[other_role].remove(example)
            
            # Add the example
            self.training_data[role_str].append({
                'text': para.text,
                'source': 'document',
                'timestamp': datetime.now().isoformat()
            })
            
            added_count += 1
            
            # Log every 10 examples
            if added_count % 10 == 0:
                log_callback(f"Added {added_count} examples so far...", "INFO")
        
        if added_count > 0:
            self._log_debug(f"Added {added_count} new training examples from document")
            log_callback(f"Added {added_count} new training examples", "INFO")
            self.data_changed = True
            
            # Save training data immediately
            save_success = self._save_training_data()
            if save_success:
                log_callback(f"Training data saved successfully", "INFO")
            else:
                log_callback(f"Failed to save training data", "ERROR")
                return False
        else:
            log_callback(f"No new examples added (skipped: {skipped_undetermined} undetermined, "
                        f"{skipped_short} too short, {skipped_duplicate} duplicates)", "INFO")
        
        # Log the file path for verification
        log_callback(f"Training data file: {self.training_data_path}", "INFO")
        
        return True
    
    def get_training_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the current training data.
        
        Returns:
            Dict with statistics
        """
        stats = {
            'total_examples': sum(len(examples) for examples in self.training_data.values()),
            'by_class': {role: len(examples) for role, examples in self.training_data.items()},
            'has_model': os.path.exists(self.model_path),
            'model_path': self.model_path,
            'ai_available': SKLEARN_AVAILABLE,
            'user_data_dir': self.user_data_dir,
            'data_changed': self.data_changed
        }
        self._log_debug(f"Generated training stats: {stats}")
        return stats
    
    def reset_all_training_data(self) -> bool:
        """
        Reset all training data and remove the model.
        
        Returns:
            bool: Success flag
        """
        try:
            # Reset training data
            self.training_data = {
                'question': [],
                'answer': [],
                'ignore': []
            }
            self.data_changed = True
            
            # Save empty training data
            self._save_training_data()
            
            # Remove model file if it exists
            if os.path.exists(self.model_path):
                os.remove(self.model_path)
                self._log_debug(f"Removed model file: {self.model_path}")
                
            # Remove vocabulary file if it exists
            if os.path.exists(self.vocab_path):
                os.remove(self.vocab_path)
                self._log_debug(f"Removed vocabulary file: {self.vocab_path}")
                
            return True
        except Exception as e:
            self._log_debug(f"Error resetting training data: {e}")
            return False
    
    def _validate_and_fix_training_data(self) -> bool:
        """
        Validate and fix training data if needed.
        
        Returns:
            bool: True if valid data exists after validation
        """
        self._log_debug(f"Validating training data structure")
        
        # Ensure all required classes exist
        required_classes = ['question', 'answer', 'ignore']
        for cls in required_classes:
            if cls not in self.training_data:
                self._log_debug(f"Missing required class '{cls}', adding empty list")
                self.training_data[cls] = []
        
        # Ensure each class has a non-empty list
        for cls, examples in self.training_data.items():
            if examples is None or not isinstance(examples, list):
                self._log_debug(f"Class '{cls}' has invalid data type, fixing")
                self.training_data[cls] = []
        
        # Count examples and ensure we have at least a few
        total_examples = sum(len(examples) for cls, examples in self.training_data.items())
        self._log_debug(f"Total examples after validation: {total_examples}")
        
        # Explicitly add some examples if there are none
        if total_examples == 0:
            self._log_debug(f"No examples found, adding initial examples")
            self.training_data['question'].append({
                'text': "What is jurisdiction?", 
                'source': 'initial', 
                'timestamp': datetime.now().isoformat()
            })
            self.training_data['answer'].append({
                'text': "It's the power of a court to hear a case.", 
                'source': 'initial', 
                'timestamp': datetime.now().isoformat()
            })
            self.training_data['ignore'].append({
                'text': "CIVIL PROCEDURE", 
                'source': 'initial', 
                'timestamp': datetime.now().isoformat()
            })
            total_examples = 3
        
        return total_examples > 0

    def open_data_directory(self) -> None:
        """Open the user data directory in the file explorer."""
        self._log_debug(f"Opening data directory: {self.user_data_dir}")
        try:
            if platform.system() == "Windows":
                os.startfile(self.user_data_dir)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", self.user_data_dir], check=True)
            else:  # Linux and others
                subprocess.run(["xdg-open", self.user_data_dir], check=True)
        except Exception as e:
            self._log_debug(f"Error opening data directory: {e}")
            logger.error(f"Error opening data directory: {e}")