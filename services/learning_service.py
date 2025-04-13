"""
Learning service for managing AI model training and improvement.
"""
import threading
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
from transformers.trainer_callback import TrainerCallback
from transformers import TrainerState, TrainerControl

logger = logging.getLogger(__name__)

# Try to import sklearn for LabelEncoder, still needed for label mapping
try:
    from sklearn.preprocessing import LabelEncoder
    SKLEARN_AVAILABLE = True
except ImportError:
    logger.warning("scikit-learn not available. Some functions may be limited.")
    SKLEARN_AVAILABLE = False

# Try to import transformer libraries, handling gracefully if not available
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    from transformers import TrainingArguments, Trainer
    from transformers.onnx import export, FeaturesManager
    import datasets
    from pathlib import Path
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    logger.warning("transformers or torch not available. AI learning features will be limited.")
    TRANSFORMERS_AVAILABLE = False

# Try to import ONNX, handling gracefully if not available
try:
    import onnx
    import onnxruntime
    ONNX_AVAILABLE = True
except ImportError:
    logger.warning("onnx or onnxruntime not available. ONNX export will be disabled.")
    ONNX_AVAILABLE = False

class LearningService:
    """Service for collecting training data and improving the AI model."""
    
    # Define the transformer model to use
    MODEL_NAME = "distilbert-base-uncased"
    
    # Special return value to indicate graceful stop
    GRACEFUL_STOP = "GRACEFUL_STOP"
    
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
        
        # Define paths for transformer model
        self.fine_tuned_model_dir = os.path.join(self.user_data_dir, "fine_tuned_model")
        self.onnx_model_path = os.path.join(self.user_data_dir, "qa_classifier.onnx")
        self.label_map_path = os.path.join(self.fine_tuned_model_dir, "label_map.json")
        
        # Paths for legacy model (for backwards compatibility)
        self.legacy_model_path = os.path.join(self.user_data_dir, "qa_classifier.pkl")
        self.legacy_vocab_path = os.path.join(self.user_data_dir, "vocabulary.npy")
        
        self._log_debug(f"Training data path: {self.training_data_path}")
        self._log_debug(f"Fine-tuned model dir: {self.fine_tuned_model_dir}")
        self._log_debug(f"ONNX model path: {self.onnx_model_path}")
        
        # Initialize or load training data
        self.training_data = self._load_training_data()
        
        # Track whether the training data has changed
        self.data_changed = False
        
        # Training thread and status tracking
        self.training_thread = None
        self.is_training = False
        self.training_progress = {"status": "idle", "message": "No training in progress"}
        self.training_callback = None

        # Data Journaling for seamless training after shutdown
        self.training_journal_path = os.path.join(self.user_data_dir, "training_journal.json")
        self.checkpoint_dir = os.path.join(self.user_data_dir, "training_checkpoints")
        self.training_should_stop = False
        self.training_completed = threading.Event()
        
        # Copy initial resources if needed
        self._init_resources()

        # Set up training
        self._initialize_training_state()

        # Force training if we have data but no model
        total_examples = sum(len(examples) for role, examples in self.training_data.items())
        if total_examples >= 10 and not os.path.exists(self.onnx_model_path) and TRANSFORMERS_AVAILABLE:
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
        
        # Create fine-tuned model directory if it doesn't exist
        os.makedirs(self.fine_tuned_model_dir, exist_ok=True)
        
        # Check if we need to copy initial model files
        if not os.path.exists(self.onnx_model_path):
            self._log_debug(f"ONNX model doesn't exist at {self.onnx_model_path}")
            
            # Check for bundled ONNX model
            bundled_onnx_path = os.path.join(self.resources_dir, "qa_classifier.onnx")
            if os.path.exists(bundled_onnx_path):
                self._log_debug(f"Bundled ONNX model exists, copying...")
                try:
                    shutil.copy2(bundled_onnx_path, self.onnx_model_path)
                    self._log_debug(f"Copied bundled ONNX model to {self.onnx_model_path}")
                except Exception as e:
                    self._log_debug(f"Error copying bundled ONNX model: {e}")
        
        # Check if we need to copy initial tokenizer and model files
        if not os.path.exists(os.path.join(self.fine_tuned_model_dir, "config.json")):
            self._log_debug(f"Transformer model files don't exist in {self.fine_tuned_model_dir}")
            
            # Check for bundled model directory
            bundled_model_dir = os.path.join(self.resources_dir, "fine_tuned_model")
            if os.path.exists(bundled_model_dir):
                self._log_debug(f"Bundled transformer model exists, copying...")
                try:
                    # Copy all files from bundled model dir to user model dir
                    for item in os.listdir(bundled_model_dir):
                        src_path = os.path.join(bundled_model_dir, item)
                        dst_path = os.path.join(self.fine_tuned_model_dir, item)
                        if os.path.isdir(src_path):
                            shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                        else:
                            shutil.copy2(src_path, dst_path)
                    self._log_debug(f"Copied bundled transformer model files to {self.fine_tuned_model_dir}")
                except Exception as e:
                    self._log_debug(f"Error copying bundled transformer model: {e}")
        
        # Also check for legacy model files (for backwards compatibility)
        if not os.path.exists(self.legacy_model_path) and os.path.exists(self.onnx_model_path):
            self._log_debug(f"Legacy model doesn't exist but ONNX does - creating placeholder")
            try:
                with open(self.legacy_model_path, 'wb') as f:
                    pickle.dump("PLACEHOLDER - Using Transformer Model", f)
                self._log_debug(f"Created placeholder legacy model file")
            except Exception as e:
                self._log_debug(f"Error creating placeholder legacy model: {e}")
    
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
        min_examples_per_class = 1  # Reduced from 5, transformers can work with fewer examples
        has_all_classes = all(len(examples) >= min_examples_per_class for role, examples in self.training_data.items())
        
        # Make sure we have a reasonable total (at least 10 examples overall)
        has_enough_total = total_examples >= 10
        
        # Final decision
        result = has_all_classes and has_enough_total
        self._log_debug(f"Has enough data to train: {result} (has_all_classes={has_all_classes}, has_enough_total={has_enough_total})")
        
        return result
    
    def _initialize_training_state(self):
        """Initialize training state and check for recovery."""
        # Create checkpoint directory if it doesn't exist
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        
        # Check if there's a journal file indicating incomplete training
        if os.path.exists(self.training_journal_path):
            try:
                with open(self.training_journal_path, 'r') as f:
                    journal = json.load(f)
                
                self._log_debug(f"Found training journal: {journal}")
                
                if journal.get('status') in ['in_progress', 'interrupted']:
                    self._log_debug(f"Found incomplete training session in journal: {journal}")
                    
                    # If it's been less than 24 hours, we might want to recover
                    last_update = datetime.fromisoformat(journal.get('last_update', '2000-01-01T00:00:00'))
                    now = datetime.now()
                    hours_since_update = (now - last_update).total_seconds() / 3600
                    
                    # Check if we have a valid checkpoint path
                    checkpoint_path = journal.get('last_checkpoint')
                    
                    if hours_since_update < 24 and checkpoint_path:
                        # Verify checkpoint exists
                        if os.path.isdir(checkpoint_path):
                            self._log_debug(f"Valid checkpoint found at {checkpoint_path}, will attempt recovery")
                            # Set flag to attempt recovery on next training request
                            self.recovery_needed = True
                            self.recovery_checkpoint = checkpoint_path
                            
                            # Auto-resume training if data hasn't changed significantly
                            if TRANSFORMERS_AVAILABLE and self.has_enough_data_to_train():
                                self._log_debug("Auto-resuming training from checkpoint")
                                # Start training in background - will use recovery checkpoint
                                self.train_model(force=True, background=True)
                            return
                        else:
                            self._log_debug(f"Checkpoint directory doesn't exist: {checkpoint_path}")
                            
                            # Try to find the latest checkpoint as fallback
                            latest_checkpoint = self._find_latest_checkpoint(self.checkpoint_dir)
                            if latest_checkpoint:
                                self._log_debug(f"Found latest checkpoint as fallback: {latest_checkpoint}")
                                self.recovery_needed = True
                                self.recovery_checkpoint = latest_checkpoint
                                
                                # Auto-resume with fallback checkpoint
                                if TRANSFORMERS_AVAILABLE and self.has_enough_data_to_train():
                                    self._log_debug("Auto-resuming training from fallback checkpoint")
                                    self.train_model(force=True, background=True)
                                return
                    else:
                        self._log_debug(f"Training session is too old or has no checkpoint")
                
                # If we got here, either status isn't recoverable or it's too old
                self._log_debug("Cleaning up old training journal")
                self._clear_training_journal()
                self.recovery_needed = False
                
            except Exception as e:
                self._log_debug(f"Error reading training journal: {e}")
                self._clear_training_journal()
                self.recovery_needed = False
        else:
            self._log_debug("No training journal found")
            self.recovery_needed = False
    
    def _find_latest_checkpoint(self, output_dir):
        """
        Helper to find the latest checkpoint directory.
        Returns the full path to the latest checkpoint directory or None if no checkpoints exist.
        """
        latest_checkpoint = None
        latest_step = -1
        
        if os.path.isdir(output_dir):
            checkpoints = [d for d in os.listdir(output_dir) if d.startswith("checkpoint-")]
            if checkpoints:
                # Sort by step number
                for checkpoint in checkpoints:
                    try:
                        step = int(checkpoint.split('-')[-1])
                        if step > latest_step:
                            latest_step = step
                            latest_checkpoint = os.path.join(output_dir, checkpoint)
                    except ValueError:
                        continue
        
        if latest_checkpoint:
            self._log_debug(f"Found latest checkpoint: {latest_checkpoint} (step {latest_step})")
        else:
            self._log_debug(f"No checkpoints found in {output_dir}")
            
        return latest_checkpoint

    def _clear_training_journal(self):
        """Clear the training journal file."""
        try:
            if os.path.exists(self.training_journal_path):
                os.remove(self.training_journal_path)
            self._log_debug("Training journal cleared")
        except Exception as e:
            self._log_debug(f"Error clearing training journal: {e}")

    def _update_training_journal(self, status, checkpoint=None, epoch=None, batch=None):
        """
        Update the training journal with current status.
        
        Args:
            status: Current training status (starting, in_progress, completed, failed)
            checkpoint: Path to the latest checkpoint
            epoch: Current epoch number
            batch: Current batch number
        """
        try:
            # Don't clear the checkpoint path if status is 'interrupted' and no checkpoint is provided
            if status == 'interrupted' and checkpoint is None:
                # Read the current journal to get the existing checkpoint
                if os.path.exists(self.training_journal_path):
                    try:
                        with open(self.training_journal_path, 'r') as f:
                            current_journal = json.load(f)
                            if current_journal.get('last_checkpoint'):
                                checkpoint = current_journal.get('last_checkpoint')
                                self._log_debug(f"Preserving existing checkpoint path during interruption: {checkpoint}")
                    except Exception as e:
                        self._log_debug(f"Error reading current journal during interruption: {e}")
            
            journal = {
                'status': status,
                'last_update': datetime.now().isoformat(),
                'last_checkpoint': checkpoint,
                'epoch': epoch,
                'batch': batch
            }
            
            # Write to a temporary file first
            temp_path = f"{self.training_journal_path}.tmp"
            with open(temp_path, 'w') as f:
                json.dump(journal, f, indent=2)
                f.flush()
                os.fsync(f.fileno())  # Ensure data is written to disk
            
            # Then rename to the actual file
            os.replace(temp_path, self.training_journal_path)
            
            self._log_debug(f"Updated training journal: {journal}")
        except Exception as e:
            self._log_debug(f"Error updating training journal: {e}")

    def gracefully_stop_training(self):
        """
        Signal the training thread to stop gracefully.
        Returns True when training is confirmed stopped or wasn't running.
        """
        if self.is_training and hasattr(self, 'training_thread') and self.training_thread and self.training_thread.is_alive():
            self._log_debug("Signaling training thread to stop gracefully")
            
            # Set the stop flag
            self.training_should_stop = True
            
            # Wait for a short time to see if training stops normally
            if not self.training_completed.wait(timeout=2.0):
                # If not completed after timeout, take more aggressive action
                self._log_debug("Training didn't stop gracefully, forcing stop")
                
                # Force is_training to False to prevent hanging
                self.is_training = False
                
                # Update journal to record interruption
                self._update_training_journal("interrupted")
                
                # Set completed event to unblock any waiting code
                self.training_completed.set()
                
                # No need to join thread - we'll let it conclude naturally
                return True
            
            self._log_debug("Training stopped gracefully")
            return True
        
        # No training in progress or already stopped
        self._log_debug("No active training to stop")
        return True

    def train_model(self, force: bool = False, background: bool = True, callback: Optional[Callable[[str, str], None]] = None) -> bool:
        """
        Train a new model if data has changed.
        
        Args:
            force: Force training even if data hasn't changed
            background: Run training in a background thread
            callback: Optional callback function for training status updates
            
        Returns:
            bool: Success flag (or True if started in background)
        """
        # Skip if transformers is not available
        if not TRANSFORMERS_AVAILABLE:
            self._log_debug(f"Transformers not available. Cannot train model.")
            logger.warning("transformers not available. Cannot train model.")
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
            
        # Check if training is already in progress
        if self.is_training:
            self._log_debug(f"Training already in progress. Skipping new training request.")
            logger.info("Training already in progress. Skipping new training request.")
            if callback:
                callback("Training already in progress", "INFO")
            return False
            
        # Set callback if provided
        self.training_callback = callback
        
        # Reset the stop flag
        self.training_should_stop = False
        self.training_completed.clear()
        
        # Check for recovery - log more verbosely when forcing training
        if self.recovery_needed and hasattr(self, 'recovery_checkpoint'):
            if os.path.isdir(self.recovery_checkpoint):
                self._log_debug(f"Recovery checkpoint found at: {self.recovery_checkpoint}")
                if callback:
                    callback(f"Will resume training from checkpoint", "INFO")
                logger.info(f"Will resume training from checkpoint: {self.recovery_checkpoint}")
            else:
                self._log_debug(f"Recovery checkpoint not found: {self.recovery_checkpoint}")
                if callback:
                    callback("Recovery checkpoint not found, starting fresh training", "WARNING")
                # Reset recovery if checkpoint not found
                self.recovery_needed = False
                self.recovery_checkpoint = None
        
        # If running in background
        if background:
            self._log_debug(f"Starting training in background thread")
            # Mark as training
            self.is_training = True
            self.training_progress = {"status": "starting", "message": "Starting training process"}
            
            # Update journal to indicate we're starting
            status = "in_progress"
            if self.recovery_needed and hasattr(self, 'recovery_checkpoint'):
                # If we're resuming, make sure to keep the checkpoint path in the journal
                self._update_training_journal(status, self.recovery_checkpoint)
            else:
                self._update_training_journal(status)
            
            # Create and start training thread - note the daemon=False setting
            self.training_thread = threading.Thread(
                target=self._train_model_thread, 
                args=(force,),
                daemon=False  # Non-daemon thread to allow completion
            )
            self.training_thread.start()
            
            if callback:
                if self.recovery_needed and hasattr(self, 'recovery_checkpoint'):
                    callback(f"Resuming training from checkpoint", "INFO")
                else:
                    callback("Training started in background", "INFO")
            return True
        else:
            # Run training synchronously
            self._log_debug(f"Running training synchronously")
            return self._train_model_internal(force)
            
    def _train_model_thread(self, force: bool) -> None:
        """
        Thread function for background training.
        
        Args:
            force: Force training even if data hasn't changed
        """
        try:
            result = self._train_model_internal(force)
            
            # Check if this was a graceful stop (rather than a true failure)
            if result == self.GRACEFUL_STOP:
                self._log_debug("Training thread detected graceful stop")
                # Don't update journal here - it was already updated by the StoppableCheckpointCallback
                self.training_progress = {"status": "interrupted", "message": "Training interrupted"}
                if self.training_callback:
                    self.training_callback("Training was interrupted", "INFO")
            elif result:
                self.training_progress = {"status": "completed", "message": "Training completed successfully"}
                self._update_training_journal("completed")
                if self.training_callback:
                    self.training_callback("Training completed successfully", "INFO")
            else:
                self.training_progress = {"status": "failed", "message": "Training failed"}
                # Don't update the journal here if this was a graceful stop
                self._update_training_journal("failed")
                if self.training_callback:
                    self.training_callback("Training failed", "ERROR")
        except Exception as e:
            self._log_debug(f"Error in training thread: {e}")
            logger.error(f"Error in training thread: {e}", exc_info=True)
            self.training_progress = {"status": "error", "message": f"Training error: {str(e)}"}
            self._update_training_journal("failed", epoch=None, batch=None)
            if self.training_callback:
                self.training_callback(f"Training error: {str(e)}", "ERROR")
        finally:
            # Mark as no longer training
            self.is_training = False
            # Signal that training is complete
            self.training_completed.set()

    def _modify_checkpoint_state(self, checkpoint_path):
        """
        Modify the trainer_state.json in a checkpoint to force continued training.
        
        Args:
            checkpoint_path: Path to the checkpoint directory
            
        Returns:
            bool: True if successfully modified, False otherwise
        """
        try:
            state_path = os.path.join(checkpoint_path, "trainer_state.json")
            if os.path.exists(state_path):
                # Read the current state
                with open(state_path, 'r') as f:
                    state = json.load(f)
                
                self._log_debug(f"Original trainer state: {state}")
                
                # Modify the epoch/steps to continue training
                if 'epoch' in state:
                    # Reduce epoch to make sure training continues
                    # Set to 1.0 to ensure we get enough additional training
                    original_epoch = state['epoch']
                    state['epoch'] = min(1.0, original_epoch)
                    self._log_debug(f"Modified epoch from {original_epoch} to {state['epoch']}")
                
                # Make a backup of the original state
                backup_path = f"{state_path}.bak"
                with open(backup_path, 'w') as f:
                    json.dump(state, f, indent=2)
                
                # Write the modified state
                with open(state_path, 'w') as f:
                    json.dump(state, f, indent=2)
                
                self._log_debug(f"Successfully modified checkpoint state to force continued training")
                return True
            else:
                self._log_debug(f"trainer_state.json not found in checkpoint {checkpoint_path}")
                return False
        except Exception as e:
            self._log_debug(f"Error modifying checkpoint state: {e}")
            return False

    def _train_model_internal(self, force: bool) -> bool:
        """
        Internal implementation of model training.

        Args:
            force: Force training even if data hasn't changed

        Returns:
            bool: Success flag or self.GRACEFUL_STOP for graceful interruptions
        """
        self._log_debug(f"Training transformer model from collected data at {datetime.now()}...")
        logger.info("Training transformer model from collected data...")

        try:
            # Update training progress
            self.training_progress = {"status": "preparing", "message": "Preparing training data"}
            self._update_training_journal("in_progress", epoch=0, batch=0)
            if self.training_callback:
                self.training_callback("Preparing training data", "INFO")

            # Prepare training data
            texts = []
            labels = []

            for role, examples in self.training_data.items():
                for example in examples:
                    texts.append(example['text'])
                    labels.append(role)

            self._log_debug(f"Prepared {len(texts)} examples for training")

            # Check for stop request
            if self.training_should_stop:
                self._log_debug("Training stopped by request during data preparation")
                return self.GRACEFUL_STOP

            # Update progress
            self.training_progress = {"status": "tokenizing", "message": "Tokenizing data"}
            if self.training_callback:
                self.training_callback("Tokenizing training data", "INFO")

            # Create label encoder
            if not SKLEARN_AVAILABLE:
                self._log_debug("sklearn not available for LabelEncoder, using manual mapping")
                unique_labels = list(set(labels))
                label_map = {label: i for i, label in enumerate(unique_labels)}
                int_labels = [label_map[label] for label in labels]
                inverse_label_map = {i: label for label, i in label_map.items()}
            else:
                le = LabelEncoder()
                int_labels = le.fit_transform(labels)
                inverse_label_map = {i: label for i, label in enumerate(le.classes_)}

            self._log_debug(f"Label mapping: {inverse_label_map}")
            num_labels = len(inverse_label_map)

            # Create Dataset object
            data_dict = {'text': texts, 'label': int_labels}
            hf_dataset = datasets.Dataset.from_dict(data_dict)

            # Load pre-trained tokenizer
            tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)

            # Tokenize dataset
            def tokenize_function(examples):
                return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=128)

            tokenized_dataset = hf_dataset.map(tokenize_function, batched=True)
            self._log_debug(f"Tokenized dataset successfully")

            # Check for stop request
            if self.training_should_stop:
                self._log_debug("Training stopped by request after tokenization")
                return self.GRACEFUL_STOP

            # Update progress
            self.training_progress = {"status": "training", "message": "Training model"}
            if self.training_callback:
                self.training_callback("Training model", "INFO")

            # Load pre-trained model
            model = AutoModelForSequenceClassification.from_pretrained(
                self.MODEL_NAME,
                num_labels=num_labels
            )

            # Define custom checkpoint saving callback that respects stop flag
            class StoppableCheckpointCallback(TrainerCallback):
                def __init__(self, outer_instance):
                    self.outer = outer_instance
                    self.last_saved_step = -1  # Track the last step a checkpoint was saved
                    self.last_checkpoint_path = None  # Store the path to the latest checkpoint

                def _find_latest_checkpoint(self, output_dir):
                    """
                    Helper to find the latest checkpoint directory.
                    Returns the full path to the latest checkpoint directory or None if no checkpoints exist.
                    """
                    latest_checkpoint = None
                    latest_step = -1
                    
                    if os.path.isdir(output_dir):
                        checkpoints = [d for d in os.listdir(output_dir) if d.startswith("checkpoint-")]
                        if checkpoints:
                            # Sort by step number
                            for checkpoint in checkpoints:
                                try:
                                    step = int(checkpoint.split('-')[-1])
                                    if step > latest_step:
                                        latest_step = step
                                        latest_checkpoint = os.path.join(output_dir, checkpoint)
                                except ValueError:
                                    continue
                    
                    if latest_checkpoint:
                        self.outer._log_debug(f"Found latest checkpoint: {latest_checkpoint} (step {latest_step})")
                    else:
                        self.outer._log_debug(f"No checkpoints found in {output_dir}")
                        
                    return latest_checkpoint

                def on_save(self, args, state, control, **kwargs):
                    """
                    Called after a checkpoint save operation.
                    Updates the journal with the path to the checkpoint that was just saved.
                    """
                    # Find the latest checkpoint directory
                    latest_checkpoint = self._find_latest_checkpoint(args.output_dir)
                    
                    if latest_checkpoint:
                        # Update our internal tracking of the last checkpoint
                        self.last_checkpoint_path = latest_checkpoint
                        self.last_saved_step = state.global_step
                        
                        # Log the checkpoint save
                        self.outer._log_debug(f"Checkpoint saved at step {state.global_step}. Path: {latest_checkpoint}")
                        
                        # Update the training journal with this checkpoint path
                        self.outer._update_training_journal(
                            "in_progress",
                            checkpoint=latest_checkpoint,
                            epoch=state.epoch,
                            batch=state.global_step
                        )
                    else:
                        self.outer._log_debug(f"on_save called at step {state.global_step}, but couldn't find checkpoint directory.")
                    
                    return control

                def on_epoch_end(self, args, state, control, **kwargs):
                    """Called at the end of an epoch."""
                    self.outer._log_debug(f"Epoch {state.epoch:.1f} completed. Step {state.global_step}")
                    
                    self.outer.training_progress = {
                        "status": "training",
                        "message": f"Epoch {state.epoch:.1f} completed. Step {state.global_step}"
                    }
                    
                    # Check for stop request
                    if self.outer.training_should_stop:
                        self.outer._log_debug(f"Stop request detected at end of epoch {state.epoch}")
                        
                        # Make sure we update the journal with the latest checkpoint path before stopping
                        if self.last_checkpoint_path:
                            self.outer._log_debug(f"Ensuring latest checkpoint path is saved to journal: {self.last_checkpoint_path}")
                            self.outer._update_training_journal(
                                "interrupted",
                                checkpoint=self.last_checkpoint_path,
                                epoch=state.epoch,
                                batch=state.global_step
                            )
                        
                        # Signal the trainer to stop
                        control.should_training_stop = True
                    
                    return control

                def on_step_end(self, args, state, control, **kwargs):
                    """Called at the end of a training step."""
                    # Periodically update progress (not too frequently)
                    if state.global_step % 10 == 0:
                        self.outer.training_progress = {
                            "status": "training",
                            "message": f"Training in progress - Epoch {state.epoch:.1f}, Step {state.global_step}"
                        }

                    # Check for stop request
                    if self.outer.training_should_stop:
                        self.outer._log_debug(f"Stop request detected at step {state.global_step}")
                        
                        # Make sure we update the journal with the latest checkpoint path before stopping
                        if self.last_checkpoint_path:
                            self.outer._log_debug(f"Ensuring latest checkpoint path is saved to journal: {self.last_checkpoint_path}")
                            self.outer._update_training_journal(
                                "interrupted",
                                checkpoint=self.last_checkpoint_path,
                                epoch=state.epoch,
                                batch=state.global_step
                            )
                        
                        # Signal the trainer to stop
                        control.should_training_stop = True
                    
                    return control

            # Define training arguments
            training_args = TrainingArguments(
                output_dir=self.checkpoint_dir,
                num_train_epochs=5,  # Increased from 3 to ensure we continue training
                per_device_train_batch_size=8,
                learning_rate=5e-5,
                logging_dir=os.path.join(self.user_data_dir, "training_logs"),
                logging_steps=10,
                save_strategy="steps",
                save_steps=10,
                save_total_limit=3,
                load_best_model_at_end=False,
                report_to="none",
                # Important: Disable past metrics tracking to avoid epoch confusion
                disable_tqdm=False,  # Show progress bars
                remove_unused_columns=True,
            )

            # Create Trainer with our stoppable callback
            callback_instance = StoppableCheckpointCallback(self)
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=tokenized_dataset,
                callbacks=[callback_instance]
            )

            # Determine if resuming from checkpoint
            resume_checkpoint_path = None
            if self.recovery_needed and hasattr(self, 'recovery_checkpoint') and self.recovery_checkpoint:
                if os.path.isdir(self.recovery_checkpoint):
                    self._log_debug(f"Attempting to resume training from checkpoint: {self.recovery_checkpoint}")
                    
                    # Modify the checkpoint state to force continued training
                    if self._modify_checkpoint_state(self.recovery_checkpoint):
                        self._log_debug("Modified checkpoint state to force continued training")
                    else:
                        self._log_debug("Failed to modify checkpoint state - may complete instantly")
                    
                    resume_checkpoint_path = self.recovery_checkpoint
                    if self.training_callback:
                        self.training_callback(f"Resuming training from checkpoint", "INFO")
                else:
                    self._log_debug(f"Recovery checkpoint path is invalid: {self.recovery_checkpoint}")
                    
                    # Try to find the latest checkpoint in the checkpoint directory as fallback
                    latest_checkpoint = self._find_latest_checkpoint(self.checkpoint_dir)
                    if latest_checkpoint:
                        self._log_debug(f"Found latest checkpoint as fallback: {latest_checkpoint}")
                        
                        # Modify the checkpoint state
                        if self._modify_checkpoint_state(latest_checkpoint):
                            self._log_debug("Modified fallback checkpoint state to force continued training")
                        else:
                            self._log_debug("Failed to modify fallback checkpoint state")
                            
                        resume_checkpoint_path = latest_checkpoint
                        if self.training_callback:
                            self.training_callback(f"Resuming from fallback checkpoint", "INFO")
            
            # Log the resume path for debugging
            resume_path_for_log = resume_checkpoint_path if resume_checkpoint_path else "None (Starting Fresh)"
            self._log_debug(f"Calling trainer.train() with resume_from_checkpoint='{resume_path_for_log}'")
            
            # Train the model, potentially resuming
            trainer.train(resume_from_checkpoint=resume_checkpoint_path)

            # Check if we stopped early
            if self.training_should_stop:
                self._log_debug("Training was stopped by request, not saving final model")
                # Important: Return special value to indicate graceful stop
                return self.GRACEFUL_STOP

            self._log_debug("Completed trainer.train()")

            # Update progress
            self.training_progress = {"status": "saving", "message": "Saving trained model"}
            if self.training_callback:
                self.training_callback("Saving trained model", "INFO")

            # Create fine-tuned model directory if it doesn't exist
            os.makedirs(self.fine_tuned_model_dir, exist_ok=True)

            # Save the fine-tuned model and tokenizer
            self._log_debug(f"Saving fine-tuned model to {self.fine_tuned_model_dir}")
            trainer.save_model(self.fine_tuned_model_dir)
            tokenizer.save_pretrained(self.fine_tuned_model_dir)

            # Save the label map
            with open(self.label_map_path, 'w') as f:
                json.dump(inverse_label_map, f)

            self._log_debug(f"Saved label map to {self.label_map_path}")

            # Check for stop request before ONNX export
            if self.training_should_stop:
                self._log_debug("Training stopped by request before ONNX export")
                # Return special value to indicate graceful stop
                return self.GRACEFUL_STOP

            # Export to ONNX if available
            if ONNX_AVAILABLE:
                self._log_debug("ONNX is available, starting export")
                self.training_progress = {"status": "exporting", "message": "Exporting to ONNX format"}
                if self.training_callback:
                    self.training_callback("Exporting to ONNX format", "INFO")

                success = self._export_to_onnx(model, tokenizer)
                if not success:
                    self._log_debug("ONNX export failed but model training succeeded")
                    # Mark as incomplete for journal
                    self._update_training_journal("completed_no_onnx")
            else:
                self._log_debug("ONNX is not available, skipping export")
                # Mark as complete without ONNX in journal
                self._update_training_journal("completed_no_onnx")

            # If we made it here, training was successful
            self.data_changed = False
            self.recovery_needed = False  # Reset recovery flag after successful completion

            # Clean up journal only on successful completion
            self._clear_training_journal()
            
            # Clean up legacy files if they exist
            if os.path.exists(self.legacy_model_path):
                try:
                    with open(self.legacy_model_path, 'wb') as f:
                        pickle.dump("PLACEHOLDER - Using Transformer Model", f)
                    self._log_debug(f"Replaced legacy model with placeholder")
                except Exception as e:
                    self._log_debug(f"Error replacing legacy model: {e}")
            
            if os.path.exists(self.legacy_vocab_path):
                try:
                    os.remove(self.legacy_vocab_path)
                    self._log_debug(f"Removed legacy vocabulary file")
                except Exception as e:
                    self._log_debug(f"Error removing legacy vocabulary file: {e}")
            
            self._log_debug(f"Successfully trained and saved transformer model with {len(texts)} examples")
            logger.info(f"Successfully trained and saved transformer model with {len(texts)} examples")
            return True
            
        except Exception as e:
            self._log_debug(f"Error training transformer model: {e}")
            logger.error(f"Error training transformer model: {e}", exc_info=True)
            self._update_training_journal("failed")
            return False
    
    def _export_to_onnx(self, model, tokenizer) -> bool:
        """
        Export model to ONNX format for efficient inference.
        
        Args:
            model: The PyTorch model to export
            tokenizer: The tokenizer to use with the model
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self._log_debug(f"Exporting model to ONNX format at {self.onnx_model_path}")
            
            # Create parent directory if needed
            os.makedirs(os.path.dirname(self.onnx_model_path), exist_ok=True)
            
            # Define paths
            onnx_path = Path(self.onnx_model_path)
            
            # Use transformers ONNX export utility
            model_kind, model_onnx_config = FeaturesManager.check_supported_model_or_raise(model)
            onnx_config = model_onnx_config(model.config)
            
            # Export the model
            export(
                preprocessor=tokenizer,
                model=model,
                config=onnx_config,
                # Force opset 14 for scaled_dot_product_attention operator
                opset=14,
                output=onnx_path
            )
            
            self._log_debug(f"Successfully exported model to ONNX format at {self.onnx_model_path}")
            return True
            
        except Exception as e:
            self._log_debug(f"Error exporting to ONNX: {e}")
            logger.error(f"Error exporting to ONNX: {e}", exc_info=True)
            return False
    
    def collect_training_data_from_document(self, paragraphs: List[Paragraph]) -> None:
        """
        Collect training data from a completely processed document.
        
        Args:
            paragraphs: List of paragraphs with assigned roles
        """
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
    
    def get_training_status(self) -> Dict[str, Any]:
        """
        Get the current training status.
        
        Returns:
            Dict with training status information
        """
        status = {
            "is_training": self.is_training,
            "progress": self.training_progress,
            "thread_alive": self.training_thread.is_alive() if self.training_thread else False
        }
        return status
        
    def get_training_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the current training data.
        
        Returns:
            Dict with statistics
        """
        try:
            # Ensure training data is valid
            if not hasattr(self, 'training_data') or self.training_data is None:
                self._log_debug("Training data not initialized, creating empty structure")
                self.training_data = {
                    'question': [],
                    'answer': [],
                    'ignore': []
                }
            
            # Basic stats
            total_examples = sum(len(examples) for role, examples in self.training_data.items())
            by_class = {role: len(examples) for role, examples in self.training_data.items()}
            
            # Model existence checks
            onnx_exists = os.path.exists(self.onnx_model_path)
            pytorch_model_exists = os.path.exists(os.path.join(self.fine_tuned_model_dir, "pytorch_model.bin"))
            has_model = onnx_exists or pytorch_model_exists
            
            # Additional model details
            model_details = {}
            if onnx_exists:
                try:
                    model_details['onnx_size'] = os.path.getsize(self.onnx_model_path)
                    model_details['onnx_modified'] = os.path.getmtime(self.onnx_model_path)
                except Exception as e:
                    self._log_debug(f"Error getting ONNX model details: {e}")
            
            if pytorch_model_exists:
                try:
                    model_details['pytorch_size'] = os.path.getsize(os.path.join(self.fine_tuned_model_dir, "pytorch_model.bin"))
                    model_details['pytorch_modified'] = os.path.getmtime(os.path.join(self.fine_tuned_model_dir, "pytorch_model.bin"))
                except Exception as e:
                    self._log_debug(f"Error getting PyTorch model details: {e}")
            
            # Training state details
            training_thread_alive = False
            if hasattr(self, 'training_thread') and self.training_thread is not None:
                training_thread_alive = self.training_thread.is_alive()
            
            # Validate AI availability
            ai_available = False
            if hasattr(self, 'TRANSFORMERS_AVAILABLE') and hasattr(self, 'ONNX_AVAILABLE'):
                ai_available = TRANSFORMERS_AVAILABLE and ONNX_AVAILABLE
            elif 'TRANSFORMERS_AVAILABLE' in globals() and 'ONNX_AVAILABLE' in globals():
                ai_available = TRANSFORMERS_AVAILABLE and ONNX_AVAILABLE
            
            # Training mode
            manual_training_mode = True
            if hasattr(self, 'is_manual_training_mode') and callable(self.is_manual_training_mode):
                try:
                    manual_training_mode = self.is_manual_training_mode()
                except Exception as e:
                    self._log_debug(f"Error getting manual training mode: {e}")
            
            # Create stats dictionary
            stats = {
                'total_examples': total_examples,
                'by_class': by_class,
                'has_model': has_model,
                'model_path': self.fine_tuned_model_dir,
                'onnx_path': self.onnx_model_path,
                'transformers_available': TRANSFORMERS_AVAILABLE if 'TRANSFORMERS_AVAILABLE' in globals() else False,
                'onnx_available': ONNX_AVAILABLE if 'ONNX_AVAILABLE' in globals() else False,
                'user_data_dir': self.user_data_dir,
                'data_changed': self.data_changed if hasattr(self, 'data_changed') else False,
                'is_training': self.is_training if hasattr(self, 'is_training') else False,
                'training_thread_alive': training_thread_alive,
                'training_progress': getattr(self, 'training_progress', {'status': 'unknown', 'message': 'No information available'}),
                'model_details': model_details,
                'ai_available': ai_available,
                'manual_training_mode': manual_training_mode
            }
            
            self._log_debug(f"Generated training stats: {stats}")
            return stats
            
        except Exception as e:
            self._log_debug(f"Error generating training stats: {e}")
            logger.error(f"Error generating training stats: {e}", exc_info=True)
            
            # Return minimal stats to avoid crashing
            return {
                'total_examples': 0,
                'by_class': {'question': 0, 'answer': 0, 'ignore': 0},
                'has_model': False,
                'error': str(e),
                'transformers_available': False,
                'onnx_available': False,
                'ai_available': False,
                'manual_training_mode': True
            }
    
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
            
            # Remove model files
            if os.path.exists(self.onnx_model_path):
                os.remove(self.onnx_model_path)
                self._log_debug(f"Removed ONNX model file: {self.onnx_model_path}")
            
            if os.path.exists(self.fine_tuned_model_dir):
                try:
                    shutil.rmtree(self.fine_tuned_model_dir)
                    self._log_debug(f"Removed fine-tuned model directory: {self.fine_tuned_model_dir}")
                    # Recreate an empty directory
                    os.makedirs(self.fine_tuned_model_dir, exist_ok=True)
                except Exception as e:
                    self._log_debug(f"Error removing fine-tuned model directory: {e}")
            
            # Remove legacy files
            if os.path.exists(self.legacy_model_path):
                os.remove(self.legacy_model_path)
                self._log_debug(f"Removed legacy model file: {self.legacy_model_path}")
                
            if os.path.exists(self.legacy_vocab_path):
                os.remove(self.legacy_vocab_path)
                self._log_debug(f"Removed legacy vocabulary file: {self.legacy_vocab_path}")
                
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