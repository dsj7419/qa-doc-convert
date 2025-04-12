"""
Configuration management for the application.
"""
import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manager for application configuration."""
    
    DEFAULT_CONFIG = {
        'analysis': {
            'analyzer_type': 'ai',  # Changed from 'auto' to 'ai'
        },
        'ui': {
            'theme': 'default',
        },
        'export': {
            'default_format': 'csv',
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config.json'
        )
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file.
        
        Returns:
            Dict containing configuration
        """
        config = self.DEFAULT_CONFIG.copy()
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    file_config = json.load(f)
                
                # Update default config with file config
                self._update_dict(config, file_config)
                logger.info(f"Loaded configuration from {self.config_path}")
            else:
                # Save default config
                self._save_config(config)
                logger.info(f"Created default configuration at {self.config_path}")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}", exc_info=True)
        
        return config
    
    def _save_config(self, config: Dict[str, Any]) -> bool:
        """
        Save configuration to file.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {e}", exc_info=True)
            return False
    
    def _update_dict(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        Recursively update a dictionary.
        
        Args:
            target: Target dictionary to update
            source: Source dictionary with updates
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._update_dict(target[key], value)
            else:
                target[key] = value
    
    def get_config(self, section: Optional[str] = None) -> Dict[str, Any]:
        """
        Get configuration.
        
        Args:
            section: Configuration section (optional)
            
        Returns:
            Dict containing configuration
        """
        if section:
            return self.config.get(section, {})
        return self.config
    
    def update_config(self, updates: Dict[str, Any], save: bool = True) -> bool:
        """
        Update configuration.
        
        Args:
            updates: Updates to apply
            save: Whether to save to file
            
        Returns:
            bool: True if successful, False otherwise
        """
        self._update_dict(self.config, updates)
        
        if save:
            return self._save_config(self.config)
        return True