"""
Monkey patch transformers library to handle emoji characters in Windows environments.
"""
import logging
import os
import sys

def apply_transformers_patch():
    """Apply patches to make transformers work better in Windows environments."""
    # Only apply on Windows
    if sys.platform != 'win32':
        return
        
    try:
        # Try to apply transformers logging patch - must happen before importing transformers
        from transformers.utils import logging as transformers_logging
        
        # Keep reference to the original _log method
        original_log = transformers_logging._log
        
        # Create a patched version that sanitizes emojis
        def patched_log(self, level, msg, *args, **kwargs):
            # Sanitize emojis from the message
            if isinstance(msg, str):
                # Replace the hugging face emoji specifically
                msg = msg.replace('\U0001f917', ':)')  # Replace 🤗 with :)
                
                # Or use encoding/decoding to remove all problematic chars
                try:
                    msg = msg.encode('cp1252', errors='ignore').decode('cp1252')
                except:
                    pass
                    
            # Call the original method with sanitized message
            return original_log(self, level, msg, *args, **kwargs)
            
        # Apply the monkey patch
        transformers_logging._log = patched_log
        
        # Also disable the Transformers welcome message
        # This sets logging level to ERROR for the transformers logger
        os.environ["TRANSFORMERS_VERBOSITY"] = "error"
        
        return True
    except Exception as e:
        print(f"Warning: Could not apply transformers patch: {e}")
        return False