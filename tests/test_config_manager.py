"""
Tests for the ConfigManager.
"""
import os
import json
import pytest
from unittest.mock import patch, mock_open

from utils.config_manager import ConfigManager

class TestConfigManager:
    """Tests for the ConfigManager."""
    
    @pytest.fixture
    def temp_config_path(self, tmp_path):
        """Create a temporary config path."""
        return tmp_path / "test_config.json"
    
    def test_default_config(self, temp_config_path):
        """Test that default config is used when no file exists."""
        with patch('os.path.exists', return_value=False):
            with patch('utils.config_manager.open', mock_open()) as m:
                cm = ConfigManager(str(temp_config_path))
                
                # Should have default config
                config = cm.get_config()
                assert 'analysis' in config
                assert 'ui' in config
                assert 'export' in config
                
                # Default analyzer type should be 'auto'
                assert config['analysis']['analyzer_type'] == 'auto'
    
    def test_load_existing_config(self, temp_config_path):
        """Test loading an existing config file."""
        test_config = {
            'analysis': {
                'analyzer_type': 'ai'
            }
        }
        
        # Create a test config file
        with open(temp_config_path, 'w') as f:
            json.dump(test_config, f)
        
        # Load the config
        cm = ConfigManager(str(temp_config_path))
        config = cm.get_config()
        
        # Should have loaded the custom analyzer type
        assert config['analysis']['analyzer_type'] == 'ai'
        
        # Should still have other default values
        assert 'ui' in config
        assert 'export' in config
    
    def test_update_config(self, temp_config_path):
        """Test updating config values."""
        # Create config manager
        with patch('os.path.exists', return_value=False):
            with patch('utils.config_manager.open', mock_open()) as m:
                cm = ConfigManager(str(temp_config_path))
                
                # Update a value
                cm.update_config({'analysis': {'analyzer_type': 'heuristic'}}, save=False)
                
                # Check that it was updated
                config = cm.get_config()
                assert config['analysis']['analyzer_type'] == 'heuristic'
    
    def test_get_section(self, temp_config_path):
        """Test getting a specific config section."""
        with patch('os.path.exists', return_value=False):
            with patch('utils.config_manager.open', mock_open()) as m:
                cm = ConfigManager(str(temp_config_path))
                
                # Get analysis section
                analysis_config = cm.get_config('analysis')
                
                # Should only have analysis settings
                assert 'analyzer_type' in analysis_config
                assert len(analysis_config) == 1