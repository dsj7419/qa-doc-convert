"""
Script to train and export a transformer-based Q&A classifier model.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    import torch
    import numpy as np
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    from transformers import TrainingArguments, Trainer
    from transformers.onnx import export, FeaturesManager
    import datasets
    from sklearn.preprocessing import LabelEncoder
except ImportError as e:
    logger.error(f"Required dependencies not installed. Please install transformers, torch, and datasets: {e}")
    sys.exit(1)

def train_and_export_model(data_path=None, output_dir=None, epochs=3, batch_size=8):
    """Train and export a transformer-based Q&A classifier model."""
    logger.info("Training transformer-based Q&A classifier model...")
    
    # Set model name
    MODEL_NAME = "distilbert-base-uncased"
    
    # Determine paths
    resources_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources")
    
    if data_path is None:
        data_path = os.path.join(resources_dir, "training_data.json")
    
    if output_dir is None:
        output_dir = os.path.join(resources_dir, "fine_tuned_model")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Load training data
    logger.info(f"Loading training data from: {data_path}")
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            training_data = json.load(f)
    except Exception as e:
        logger.error(f"Error loading training data: {e}")
        return False
    
    # Prepare data for training
    texts = []
    labels = []
    
    for role, examples in training_data.items():
        for example in examples:
            texts.append(example['text'])
            labels.append(role)
    
    logger.info(f"Loaded {len(texts)} training examples")
    
    # Create label encoder
    le = LabelEncoder()
    int_labels = le.fit_transform(labels)
    label_map = {i: cls for i, cls in enumerate(le.classes_)}
    num_labels = len(label_map)
    
    logger.info(f"Label mapping: {label_map}")
    
    # Create Dataset object
    data_dict = {'text': texts, 'label': int_labels}
    hf_dataset = datasets.Dataset.from_dict(data_dict)
    
    # Load pre-trained tokenizer
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    
    # Tokenize dataset
    def tokenize_function(examples):
        return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=128)
    
    tokenized_dataset = hf_dataset.map(tokenize_function, batched=True)
    logger.info(f"Tokenized dataset successfully")
    
    # Load pre-trained model
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME, 
        num_labels=num_labels
    )
    
    # Define training arguments
    training_args = TrainingArguments(
        output_dir=os.path.join(output_dir, "checkpoints"),
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        learning_rate=5e-5,
        logging_dir=os.path.join(output_dir, "logs"),
        logging_steps=10,
        save_strategy="epoch",
        load_best_model_at_end=False,
        report_to="none",
    )
    
    # Create Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
    )
    
    # Train the model
    logger.info("Starting model training...")
    trainer.train()
    logger.info("Model training complete")
    
    # Save the fine-tuned model and tokenizer
    logger.info(f"Saving fine-tuned model to {output_dir}")
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    
    # Save the label map
    label_map_path = os.path.join(output_dir, "label_map.json")
    with open(label_map_path, 'w') as f:
        json.dump(label_map, f)
    
    logger.info(f"Saved label map to {label_map_path}")
    
    # Export to ONNX
    logger.info("Exporting model to ONNX format...")
    try:
        # Define paths
        onnx_path = Path(os.path.join(os.path.dirname(output_dir), "qa_classifier.onnx"))
        
        # Use transformers ONNX export utility
        model_kind, model_onnx_config = FeaturesManager.check_supported_model_or_raise(model)
        onnx_config = model_onnx_config(model.config)
        
        # Export the model
        export(
            preprocessor=tokenizer,
            model=model,
            config=onnx_config,
            opset=onnx_config.default_onnx_opset,
            output=onnx_path
        )
        
        logger.info(f"Successfully exported model to ONNX format at {onnx_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error exporting to ONNX: {e}", exc_info=True)
        logger.warning("Training succeeded but ONNX export failed")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train a transformer-based Q&A classifier model")
    parser.add_argument('--data', type=str, help="Path to training_data.json")
    parser.add_argument('--output', type=str, help="Output directory for the fine-tuned model")
    parser.add_argument('--epochs', type=int, default=3, help="Number of training epochs")
    parser.add_argument('--batch-size', type=int, default=8, help="Training batch size")
    args = parser.parse_args()
    
    success = train_and_export_model(
        data_path=args.data, 
        output_dir=args.output,
        epochs=args.epochs,
        batch_size=args.batch_size
    )
    
    if success:
        logger.info("Model training and export completed successfully")
        sys.exit(0)
    else:
        logger.error("Model training or export failed")
        sys.exit(1)