import pytest
import numpy as np
import cv2
from unittest.mock import patch, MagicMock
from generate_slides import ImageProcessor


@pytest.fixture
def sample_image():
    """Create a sample image for testing."""
    return np.zeros((100, 100, 3), dtype=np.uint8)


def test_get_face_area_fraction_no_faces(sample_image):
    """Test get_face_area_fraction when no faces are detected."""
    # Mock the face detector to return no detections
    with patch.object(ImageProcessor.face_detector, 'process') as mock_process:
        mock_results = MagicMock()
        mock_results.detections = None
        mock_process.return_value = mock_results
        
        # Call the method
        result = ImageProcessor.get_face_area_fraction(sample_image)
        
        # Check that the result is 0
        assert result == 0
        
        # Check that process was called with the correct arguments
        mock_process.assert_called_once()
        # Check that cv2.cvtColor was called to convert BGR to RGB
        assert mock_process.call_args[0][0].shape == sample_image.shape


def test_get_face_area_fraction_with_faces(sample_image):
    """Test get_face_area_fraction when faces are detected."""
    # Mock the face detector to return detections
    with patch.object(ImageProcessor.face_detector, 'process') as mock_process:
        # Create a mock detection with a bounding box
        mock_detection = MagicMock()
        mock_bbox = MagicMock()
        mock_bbox.width = 0.2
        mock_bbox.height = 0.3
        mock_detection.location_data.relative_bounding_box = mock_bbox
        
        # Create a second mock detection
        mock_detection2 = MagicMock()
        mock_bbox2 = MagicMock()
        mock_bbox2.width = 0.1
        mock_bbox2.height = 0.1
        mock_detection2.location_data.relative_bounding_box = mock_bbox2
        
        # Set up the mock results
        mock_results = MagicMock()
        mock_results.detections = [mock_detection, mock_detection2]
        mock_process.return_value = mock_results
        
        # Call the method
        result = ImageProcessor.get_face_area_fraction(sample_image)
        
        # Check that the result is the sum of the areas
        # First face: 0.2 * 0.3 = 0.06
        # Second face: 0.1 * 0.1 = 0.01
        # Total: 0.06 + 0.01 = 0.07
        assert result == pytest.approx(0.07)


def test_image_similarity_different_shapes():
    """Test image_similarity when images have different shapes."""
    img1 = np.zeros((100, 100, 3), dtype=np.uint8)
    img2 = np.zeros((200, 200, 3), dtype=np.uint8)
    
    result = ImageProcessor.image_similarity(img1, img2)
    
    # Should return 0 for different shapes
    assert result == 0


def test_image_similarity_identical_images():
    """Test image_similarity with identical images."""
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    
    # Mock the SSIM function to return a specific value
    with patch('generate_slides.ssim', return_value=(1.0, None)) as mock_ssim:
        result = ImageProcessor.image_similarity(img, img)
        
        # Should return the value from SSIM
        assert result == 1.0
        
        # Check that SSIM was called with grayscale images
        assert mock_ssim.call_count == 1
        assert len(mock_ssim.call_args[0]) == 2
        assert mock_ssim.call_args[0][0].shape == (100, 100)
        assert mock_ssim.call_args[0][1].shape == (100, 100)


def test_image_similarity_different_images():
    """Test image_similarity with different images."""
    img1 = np.zeros((100, 100, 3), dtype=np.uint8)
    img2 = np.ones((100, 100, 3), dtype=np.uint8) * 255
    
    # Mock the SSIM function to return a specific value
    with patch('generate_slides.ssim', return_value=(0.5, None)) as mock_ssim:
        result = ImageProcessor.image_similarity(img1, img2)
        
        # Should return the value from SSIM
        assert result == 0.5
