import pytest
import os
import cv2
import numpy as np
from unittest.mock import patch, MagicMock
from datetime import datetime
from generate_slides import FileManager, Config


@pytest.fixture
def sample_image():
    """Create a sample image for testing."""
    return np.zeros((100, 100, 3), dtype=np.uint8)


@pytest.fixture
def setup_test_dir():
    """Set up a test directory for file operations."""
    test_dir = "test_output"
    os.makedirs(test_dir, exist_ok=True)
    yield test_dir
    # Clean up
    import shutil
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)


def test_save_image_uses_config_dir(sample_image):
    """Test that save_image uses the directory from Config by default."""
    # Set a specific output directory in Config
    original_dir = Config.OUTPUT_DIR
    Config.OUTPUT_DIR = "test_dir"
    
    try:
        # Mock datetime and cv2.imwrite
        mock_timestamp = "230401-120000"
        with patch('generate_slides.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = mock_timestamp
            with patch('generate_slides.cv2.imwrite') as mock_imwrite:
                # Call the method
                filepath = FileManager.save_image(sample_image)
                
                # Check the filepath
                expected_path = os.path.join("test_dir", f"{mock_timestamp}.png")
                assert filepath == expected_path
                
                # Check that imwrite was called with the correct arguments
                mock_imwrite.assert_called_once_with(expected_path, sample_image)
    finally:
        # Reset the output directory
        Config.OUTPUT_DIR = original_dir


def test_save_image_with_custom_dir(sample_image, setup_test_dir):
    """Test that save_image uses a custom directory when provided."""
    # Mock datetime
    mock_timestamp = "230401-120000"
    with patch('generate_slides.datetime') as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = mock_timestamp
        
        # Call the method with a custom directory
        filepath = FileManager.save_image(sample_image, output_dir=setup_test_dir)
        
        # Check the filepath
        expected_path = os.path.join(setup_test_dir, f"{mock_timestamp}.png")
        assert filepath == expected_path
        
        # Check that the file was created (this actually writes the file)
        assert os.path.exists(expected_path)


def test_rename_file_with_title_no_title(setup_test_dir):
    """Test rename_file_with_title when no title is provided."""
    # Create a test file
    test_file = os.path.join(setup_test_dir, "test.png")
    with open(test_file, 'w') as f:
        f.write("test")
    
    # Call the method with no title
    result = FileManager.rename_file_with_title(test_file, None)
    
    # Check that the file was not renamed
    assert result == test_file
    assert os.path.exists(test_file)


def test_rename_file_with_title_success(setup_test_dir):
    """Test rename_file_with_title when a title is provided."""
    # Create a test file
    test_file = os.path.join(setup_test_dir, "test.png")
    with open(test_file, 'w') as f:
        f.write("test")
    
    # Call the method with a title
    result = FileManager.rename_file_with_title(test_file, "sample_title")
    
    # Check that the file was renamed
    expected_path = os.path.join(setup_test_dir, "test_sample_title.png")
    assert result == expected_path
    assert os.path.exists(expected_path)
    assert not os.path.exists(test_file)


def test_rename_file_with_title_error(setup_test_dir):
    """Test rename_file_with_title when an error occurs."""
    # Create a test file
    test_file = os.path.join(setup_test_dir, "test.png")
    with open(test_file, 'w') as f:
        f.write("test")
    
    # Mock os.rename to raise an exception
    with patch('generate_slides.os.rename', side_effect=Exception("Test error")):
        # Call the method
        result = FileManager.rename_file_with_title(test_file, "sample_title")
        
        # Check that the original filepath is returned
        assert result == test_file
        # Check that the file still exists
        assert os.path.exists(test_file)
