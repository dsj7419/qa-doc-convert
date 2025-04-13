"""
Direct PyTorch to ONNX export script - alternative approach.
"""
import os
import sys
import json
import logging
import argparse
import torch
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
except ImportError as e:
    logger.error(f"Required dependencies not installed: {e}")
    sys.exit(1)

def export_to_onnx_direct(model_dir, output_path=None):
    """
    Export a trained transformer model to ONNX format using direct PyTorch export.
    
    Args:
        model_dir: Directory containing the trained model
        output_path: Path where the ONNX model should be saved
    """
    logger.info(f"Exporting model from {model_dir} to ONNX using direct PyTorch export")
    
    if output_path is None:
        output_path = os.path.join(os.path.dirname(model_dir), "qa_classifier.onnx")
    
    # Create output directory if needed
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        # Load the tokenizer and model
        tokenizer = AutoTokenizer.from_pretrained(model_dir)
        model = AutoModelForSequenceClassification.from_pretrained(model_dir)
        
        # Set model to evaluation mode
        model.eval()
        
        logger.info("Model and tokenizer loaded successfully")
        
        # Create dummy inputs
        batch_size = 1
        seq_length = 128
        
        # Create a simple text input to tokenize
        sample_text = ["This is a test question?"]
        encoded_input = tokenizer(sample_text, padding="max_length", truncation=True, 
                                 max_length=seq_length, return_tensors="pt")
        
        # Extract input tensors
        input_ids = encoded_input["input_ids"]
        attention_mask = encoded_input["attention_mask"]
        
        # Get the input names
        input_names = ["input_ids", "attention_mask"]
        output_names = ["logits"]
        
        # Dynamic axes for variable batch size and sequence length
        dynamic_axes = {
            'input_ids': {0: 'batch_size', 1: 'sequence'},
            'attention_mask': {0: 'batch_size', 1: 'sequence'},
            'logits': {0: 'batch_size'}
        }
        
        logger.info(f"Using ONNX opset version: 14")
        
        # Export the model directly with torch.onnx
        with torch.no_grad():
            torch.onnx.export(
                model,
                (input_ids, attention_mask),
                output_path,
                export_params=True,
                opset_version=14,  # Use higher opset version
                do_constant_folding=True,
                input_names=input_names,
                output_names=output_names,
                dynamic_axes=dynamic_axes,
                verbose=False
            )
        
        logger.info(f"Successfully exported model to ONNX format at {output_path}")
        
        # Test loading the ONNX model to verify it works
        try:
            import onnx
            import onnxruntime
            
            # Load and check ONNX model
            onnx_model = onnx.load(output_path)
            onnx.checker.check_model(onnx_model)
            logger.info("ONNX model verified successfully")
            
            # Test with ONNX Runtime
            session = onnxruntime.InferenceSession(output_path)
            logger.info("ONNX Runtime session created successfully")
            
            # Get input names from the model
            input_names = [input.name for input in session.get_inputs()]
            logger.info(f"ONNX model input names: {input_names}")
            
            # Create input dictionary for session
            ort_inputs = {}
            for name in input_names:
                if name == 'input_ids':
                    ort_inputs[name] = input_ids.numpy()
                elif name == 'attention_mask':
                    ort_inputs[name] = attention_mask.numpy()
            
            # Run inference
            ort_outputs = session.run(None, ort_inputs)
            logger.info(f"Test inference successful. Output shape: {ort_outputs[0].shape}")
            
        except ImportError:
            logger.warning("ONNX or ONNX Runtime not available. Skipping model verification.")
        except Exception as e:
            logger.error(f"Error verifying ONNX model: {e}")
            return False
        
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
    
    success = export_to_onnx_direct(args.model_dir, args.output)
    
    if success:
        logger.info("ONNX export completed successfully")
        sys.exit(0)
    else:
        logger.error("ONNX export failed")
        sys.exit(1)