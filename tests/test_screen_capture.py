import pytest
import numpy as np
import cv2
from unittest.mock import patch, MagicMock
from generate_slides import ScreenCapture, Config


@pytest.fixture
def mock_mss():
    """Create a mock mss instance."""
    with patch('generate_slides.mss.mss') as mock_mss:
        # Create a mock screenshot
        mock_screenshot = MagicMock()
        # Instead of returning a numpy array directly, make it behave like a PIL image
        mock_screenshot.__array__ = lambda x: np.zeros((100, 100, 4), dtype=np.uint8)
        
        # Set up the mock sct object
        mock_sct = MagicMock()
        mock_sct.grab.return_value = mock_screenshot
        mock_sct.monitors = {0: {'left': 0, 'top': 0, 'width': 100, 'height': 100},
                            1: {'left': 0, 'top': 0, 'width': 100, 'height': 100},
                            2: {'left': 0, 'top': 0, 'width': 100, 'height': 100}}
        
        # Set up the mock mss context manager
        mock_mss.return_value.__enter__.return_value = mock_sct
        
        yield mock_mss


def test_capture_screen_uses_config_screen_index(mock_mss):
    """Test that capture_screen uses the screen index from Config by default."""
    # Set a specific screen index in Config
    original_index = Config.SCREEN_INDEX
    Config.SCREEN_INDEX = 1
    
    try:
        # Mock np.array and cv2.cvtColor to avoid actual image processing
        with patch('generate_slides.np.array', return_value=np.zeros((100, 100, 4), dtype=np.uint8)) as mock_np_array:
            with patch('generate_slides.cv2.cvtColor', return_value=np.zeros((100, 100, 3), dtype=np.uint8)):
                # Call the method without specifying a screen index
                ScreenCapture.capture_screen()
                
                # Get the mock sct object
                mock_sct = mock_mss.return_value.__enter__.return_value
                
                # Check that grab was called with the correct monitor
                mock_sct.grab.assert_called_once_with(mock_sct.monitors[1])
    finally:
        # Reset the screen index
        Config.SCREEN_INDEX = original_index


def test_capture_screen_with_custom_index(mock_mss):
    """Test that capture_screen uses a custom screen index when provided."""
    # Mock np.array and cv2.cvtColor to avoid actual image processing
    with patch('generate_slides.np.array', return_value=np.zeros((100, 100, 4), dtype=np.uint8)):
        with patch('generate_slides.cv2.cvtColor', return_value=np.zeros((100, 100, 3), dtype=np.uint8)):
            # Call the method with a specific screen index
            ScreenCapture.capture_screen(screen_index=0)
            
            # Get the mock sct object
            mock_sct = mock_mss.return_value.__enter__.return_value
            
            # Check that grab was called with the correct monitor
            mock_sct.grab.assert_called_once_with(mock_sct.monitors[0])


def test_capture_screen_returns_bgr_image(mock_mss):
    """Test that capture_screen returns a BGR image."""
    # Set up the mock to return a specific array
    mock_sct = mock_mss.return_value.__enter__.return_value
    mock_array = np.ones((100, 100, 4), dtype=np.uint8) * 255
    
    with patch('generate_slides.np.array', return_value=mock_array):
        with patch('generate_slides.cv2.cvtColor', return_value=np.ones((100, 100, 3), dtype=np.uint8) * 200) as mock_cvtcolor:
            # Call the method
            result = ScreenCapture.capture_screen()
            
            # Check that cvtColor was called with the correct arguments
            mock_cvtcolor.assert_called_once()
            np.testing.assert_array_equal(mock_cvtcolor.call_args[0][0], mock_array)
            assert mock_cvtcolor.call_args[0][1] == cv2.COLOR_BGRA2BGR
            
            # Check the result
            assert result.shape == (100, 100, 3)
            assert result.dtype == np.uint8
            assert np.all(result == 200)
