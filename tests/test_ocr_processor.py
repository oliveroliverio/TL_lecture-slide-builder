import pytest
import numpy as np
import cv2
from unittest.mock import patch, MagicMock
from generate_slides import OCRProcessor, Config


@pytest.fixture
def sample_image():
    """Create a sample image for testing."""
    return np.zeros((100, 100, 3), dtype=np.uint8)


def test_extract_text_from_image_success(sample_image):
    """Test extract_text_from_image when OCR succeeds."""
    # Mock the preprocessing and OCR functions
    with patch('generate_slides.cv2.cvtColor', return_value=np.zeros((100, 100), dtype=np.uint8)) as mock_cvtcolor:
        with patch('generate_slides.cv2.adaptiveThreshold', return_value=np.zeros((100, 100), dtype=np.uint8)) as mock_threshold:
            with patch('generate_slides.cv2.medianBlur', return_value=np.zeros((100, 100), dtype=np.uint8)) as mock_blur:
                with patch('generate_slides.pytesseract.image_to_string', return_value="Sample text") as mock_ocr:
                    # Call the method
                    result = OCRProcessor.extract_text_from_image(sample_image)
                    
                    # Check that the result is the text from OCR
                    assert result == "Sample text"
                    
                    # Check that the preprocessing functions were called
                    mock_cvtcolor.assert_called_once()
                    mock_threshold.assert_called_once()
                    mock_blur.assert_called_once()
                    
                    # Check that OCR was called with the processed image
                    mock_ocr.assert_called_once()
                    assert mock_ocr.call_args[0][0] is mock_blur.return_value


def test_extract_text_from_image_fallback(sample_image):
    """Test extract_text_from_image falls back to original image if initial OCR fails."""
    # Mock the preprocessing and OCR functions
    with patch('generate_slides.cv2.cvtColor', return_value=np.zeros((100, 100), dtype=np.uint8)) as mock_cvtcolor:
        with patch('generate_slides.cv2.adaptiveThreshold', return_value=np.zeros((100, 100), dtype=np.uint8)) as mock_threshold:
            with patch('generate_slides.cv2.medianBlur', return_value=np.zeros((100, 100), dtype=np.uint8)) as mock_blur:
                # First OCR call returns empty string, second returns text
                with patch('generate_slides.pytesseract.image_to_string', side_effect=["", "Fallback text"]) as mock_ocr:
                    # Call the method
                    result = OCRProcessor.extract_text_from_image(sample_image)
                    
                    # Check that the result is the text from the fallback OCR
                    assert result == "Fallback text"
                    
                    # Check that OCR was called twice
                    assert mock_ocr.call_count == 2
                    # First with processed image, then with original image
                    assert mock_ocr.call_args_list[0][0][0] is mock_blur.return_value
                    assert mock_ocr.call_args_list[1][0][0] is sample_image


def test_extract_text_from_image_with_debug(sample_image):
    """Test extract_text_from_image with debug mode enabled."""
    # Enable debug mode
    original_debug_mode = Config.DEBUG_MODE
    Config.DEBUG_MODE = True
    original_debug_dir = getattr(Config, 'DEBUG_DIR', None)
    Config.DEBUG_DIR = "debug_dir"
    
    try:
        # Mock the preprocessing, OCR, and image writing functions
        with patch('generate_slides.cv2.cvtColor', return_value=np.zeros((100, 100), dtype=np.uint8)) as mock_cvtcolor:
            with patch('generate_slides.cv2.adaptiveThreshold', return_value=np.zeros((100, 100), dtype=np.uint8)) as mock_threshold:
                with patch('generate_slides.cv2.medianBlur', return_value=np.zeros((100, 100), dtype=np.uint8)) as mock_blur:
                    with patch('generate_slides.pytesseract.image_to_string', return_value="Sample text") as mock_ocr:
                        with patch('generate_slides.cv2.imwrite') as mock_imwrite:
                            with patch('generate_slides.os.path.basename', return_value="test.png") as mock_basename:
                                with patch('generate_slides.os.path.splitext', return_value=("test", ".png")) as mock_splitext:
                                    # Call the method with a filename
                                    result = OCRProcessor.extract_text_from_image(sample_image, "test.png")
                                    
                                    # Check that imwrite was called for debug images
                                    assert mock_imwrite.call_count == 3
    finally:
        # Reset debug mode
        Config.DEBUG_MODE = original_debug_mode
        if original_debug_dir is not None:
            Config.DEBUG_DIR = original_debug_dir
        else:
            delattr(Config, 'DEBUG_DIR')


def test_extract_text_from_image_error(sample_image):
    """Test extract_text_from_image when an error occurs."""
    # Mock cv2.cvtColor to raise an exception
    with patch('generate_slides.cv2.cvtColor', side_effect=Exception("Test error")):
        # Call the method
        result = OCRProcessor.extract_text_from_image(sample_image)
        
        # Check that an empty string is returned
        assert result == ""
