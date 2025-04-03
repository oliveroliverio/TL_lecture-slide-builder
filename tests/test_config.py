import os
import pytest
import shutil
from generate_slides import Config


def test_config_default_values():
    """Test that Config has the expected default values."""
    assert Config.SCREEN_INDEX == 2
    assert Config.CAPTURE_INTERVAL == 2
    assert Config.SSIM_THRESHOLD == 0.95
    assert Config.FACE_AREA_THRESHOLD == 0.25
    assert Config.OUTPUT_DIR == "captured_slides"
    assert Config.MAX_TITLE_LENGTH == 50
    assert Config.OCR_QUEUE_SIZE == 100
    assert Config.DEBUG_MODE is False


def test_initialize_creates_directories():
    """Test that initialize creates the necessary directories."""
    # Set up a test output directory
    test_output_dir = "test_output_dir"
    Config.OUTPUT_DIR = test_output_dir
    
    try:
        # Make sure the directory doesn't exist
        if os.path.exists(test_output_dir):
            shutil.rmtree(test_output_dir)
        
        # Initialize and check directory creation
        Config.initialize()
        assert os.path.exists(test_output_dir)
        
        # Test debug directory creation
        Config.DEBUG_MODE = True
        Config.initialize()
        debug_dir = os.path.join(test_output_dir, "debug")
        assert os.path.exists(debug_dir)
    
    finally:
        # Clean up
        if os.path.exists(test_output_dir):
            shutil.rmtree(test_output_dir)
        
        # Reset config values
        Config.OUTPUT_DIR = "captured_slides"
        Config.DEBUG_MODE = False
