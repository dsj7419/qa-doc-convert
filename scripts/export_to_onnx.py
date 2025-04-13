"""
Script to export a trained transformer model to ONNX format.
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
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    from transformers.onnx import export, FeaturesManager
except ImportError as e:
    logger.error(f"Required dependencies not installed: {e}")
    sys.exit(1)

def export_to_onnx(model_dir, output_path=None):
    """
    Export a trained transformer model to ONNX format.
    
    Args:
        model_dir: Directory containing the trained model
        output_path: Path where the ONNX model should be saved
    """
    logger.info(f"Exporting model from {model_dir} to ONNX")
    
    if output_path is None:
        output_path = os.path.join(os.path.dirname(model_dir), "qa_classifier.onnx")
    
    # Create output directory if needed
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        # Load the tokenizer and model
        tokenizer = AutoTokenizer.from_pretrained(model_dir)
        model = AutoModelForSequenceClassification.from_pretrained(model_dir)
        
        logger.info("Model and tokenizer loaded successfully")
        
        # Configure ONNX export
        model_kind, model_onnx_config = FeaturesManager.check_supported_model_or_raise(model)
        onnx_config = model_onnx_config(model.config)
        
        opset = 14
        logger.info(f"Using ONNX opset version: {opset}")
        
        # Export the model
        export(
            preprocessor=tokenizer,
            model=model,
            config=onnx_config,
            opset=opset,  # Use the explicitly defined opset
            output=Path(output_path)
        )
        
        logger.info(f"Successfully exported model to ONNX format at {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error exporting to ONNX: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export a trained transformer model to ONNX format")
    parser.add_argument('--model-dir', type=str, default="resources/fine_tuned_model", 
                        help="Directory containing the trained model")
    parser.add_argument('--output', type=str, default=None, 
                        help="Path where the ONNX model should be saved")
    args = parser.parse_args()
    
    success = export_to_onnx(args.model_dir, args.output)
    
    if success:
        logger.info("ONNX export completed successfully")
        sys.exit(0)
    else:
        logger.error("ONNX export failed")
        sys.exit(1)