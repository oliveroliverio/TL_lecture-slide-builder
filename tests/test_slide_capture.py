import pytest
import numpy as np
import queue
import threading
from unittest.mock import patch, MagicMock, call
from generate_slides import SlideCapture, Config, ScreenCapture, ImageProcessor, FileManager


@pytest.fixture
def slide_capture():
    """Create a SlideCapture instance for testing."""
    return SlideCapture()


def test_init(slide_capture):
    """Test that SlideCapture initializes correctly."""
    assert isinstance(slide_capture.ocr_queue, queue.Queue)
    assert slide_capture.ocr_queue.maxsize == Config.OCR_QUEUE_SIZE
    assert slide_capture.last_image is None
    assert slide_capture.ocr_thread is None


def test_process_new_slide(slide_capture):
    """Test _process_new_slide method."""
    # Create a sample image
    sample_image = np.zeros((100, 100, 3), dtype=np.uint8)
    
    # Mock FileManager.save_image
    with patch.object(FileManager, 'save_image', return_value="test.png") as mock_save:
        # Mock queue.put
        with patch.object(slide_capture.ocr_queue, 'put') as mock_put:
            # Call the method
            slide_capture._process_new_slide(sample_image)
            
            # Check that the image was saved
            mock_save.assert_called_once_with(sample_image)
            
            # Check that the image was added to the queue
            mock_put.assert_called_once_with(("test.png", sample_image), block=False)
            
            # Check that last_image was updated
            assert slide_capture.last_image is sample_image


def test_process_new_slide_queue_full(slide_capture):
    """Test _process_new_slide method when the queue is full."""
    # Create a sample image
    sample_image = np.zeros((100, 100, 3), dtype=np.uint8)
    
    # Mock FileManager.save_image
    with patch.object(FileManager, 'save_image', return_value="test.png") as mock_save:
        # Mock queue.put to raise queue.Full
        with patch.object(slide_capture.ocr_queue, 'put', side_effect=queue.Full()) as mock_put:
            # Call the method
            slide_capture._process_new_slide(sample_image)
            
            # Check that the image was saved
            mock_save.assert_called_once_with(sample_image)
            
            # Check that put was called
            mock_put.assert_called_once()
            
            # Check that last_image was updated
            assert slide_capture.last_image is sample_image


@patch('generate_slides.threading.Thread')
def test_start(mock_thread, slide_capture):
    """Test start method."""
    # Mock Config.initialize
    with patch.object(Config, 'initialize') as mock_init:
        # Mock _main_loop to prevent infinite loop
        with patch.object(slide_capture, '_main_loop') as mock_loop:
            # Call the method
            slide_capture.start()
            
            # Check that Config was initialized
            mock_init.assert_called_once()
            
            # Check that the OCR thread was started
            mock_thread.assert_called_once_with(target=slide_capture._ocr_worker, daemon=True)
            mock_thread.return_value.start.assert_called_once()
            
            # Check that _main_loop was called
            mock_loop.assert_called_once()


def test_main_loop_face_detected(slide_capture):
    """Test _main_loop when a face is detected."""
    # Set up to run once and then raise an exception to exit the loop
    mock_image = np.zeros((100, 100, 3), dtype=np.uint8)
    
    # Mock dependencies
    with patch.object(ScreenCapture, 'capture_screen', return_value=mock_image) as mock_capture:
        with patch.object(ImageProcessor, 'get_face_area_fraction', return_value=0.3) as mock_face:
            # We need to make the loop run only once, so we'll use a side effect that raises an exception on the second call
            with patch('generate_slides.time.sleep', side_effect=Exception("Stop loop")) as mock_sleep:
                # Call the method and catch the exception
                with pytest.raises(Exception, match="Stop loop"):
                    slide_capture._main_loop()
                
                # Check that capture_screen was called
                mock_capture.assert_called_once()
                
                # Check that get_face_area_fraction was called
                mock_face.assert_called_once_with(mock_image)
                
                # Check that sleep was called with CAPTURE_INTERVAL
                mock_sleep.assert_called_once_with(Config.CAPTURE_INTERVAL)
                
                # Check that last_image is still None (no slide captured)
                assert slide_capture.last_image is None


def test_main_loop_first_slide(slide_capture):
    """Test _main_loop with the first slide (no previous slide)."""
    # Set up to run once and then raise an exception to exit the loop
    mock_image = np.zeros((100, 100, 3), dtype=np.uint8)
    
    # Mock dependencies
    with patch.object(ScreenCapture, 'capture_screen', return_value=mock_image) as mock_capture:
        with patch.object(ImageProcessor, 'get_face_area_fraction', return_value=0.2) as mock_face:
            with patch.object(slide_capture, '_process_new_slide') as mock_process:
                # We need to make the loop run only once, so we'll use a side effect that raises an exception on the second call
                with patch('generate_slides.time.sleep', side_effect=Exception("Stop loop")) as mock_sleep:
                    # Call the method and catch the exception
                    with pytest.raises(Exception, match="Stop loop"):
                        slide_capture._main_loop()
                    
                    # Check that _process_new_slide was called once
                    mock_process.assert_called_once_with(mock_image)


def test_main_loop_similar_text(slide_capture):
    """Test _main_loop with similar text."""
    # Set up to run once and then raise an exception to exit the loop
    mock_image1 = np.zeros((100, 100, 3), dtype=np.uint8)
    mock_image2 = np.zeros((100, 100, 3), dtype=np.uint8)
    slide_capture.last_image = mock_image1
    
    # Mock dependencies
    with patch.object(ScreenCapture, 'capture_screen', return_value=mock_image2) as mock_capture:
        with patch.object(ImageProcessor, 'get_face_area_fraction', return_value=0.2) as mock_face:
            with patch.object(ImageProcessor, 'text_similarity', return_value=0.96) as mock_similarity:
                with patch.object(slide_capture, '_process_new_slide') as mock_process:
                    # We need to make the loop run only once, so we'll use a side effect that raises an exception on the second call
                    with patch('generate_slides.time.sleep', side_effect=Exception("Stop loop")) as mock_sleep:
                        # Call the method and catch the exception
                        with pytest.raises(Exception, match="Stop loop"):
                            slide_capture._main_loop()
                        
                        # Check that text_similarity was called once
                        mock_similarity.assert_called_once_with(mock_image2, mock_image1)
                        
                        # Check that _process_new_slide was NOT called
                        mock_process.assert_not_called()


def test_main_loop_different_text(slide_capture):
    """Test _main_loop with different text."""
    # Set up to run once and then raise an exception to exit the loop
    mock_image1 = np.zeros((100, 100, 3), dtype=np.uint8)
    mock_image2 = np.ones((100, 100, 3), dtype=np.uint8)
    slide_capture.last_image = mock_image1
    
    # Mock dependencies
    with patch.object(ScreenCapture, 'capture_screen', return_value=mock_image2) as mock_capture:
        with patch.object(ImageProcessor, 'get_face_area_fraction', return_value=0.2) as mock_face:
            with patch.object(ImageProcessor, 'text_similarity', return_value=0.7) as mock_similarity:
                with patch.object(slide_capture, '_process_new_slide') as mock_process:
                    # We need to make the loop run only once, so we'll use a side effect that raises an exception on the second call
                    with patch('generate_slides.time.sleep', side_effect=Exception("Stop loop")) as mock_sleep:
                        # Call the method and catch the exception
                        with pytest.raises(Exception, match="Stop loop"):
                            slide_capture._main_loop()
                        
                        # Check that _process_new_slide was called once
                        mock_process.assert_called_once_with(mock_image2)
