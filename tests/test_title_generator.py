import pytest
import os
import re
from unittest.mock import patch, MagicMock
from generate_slides import TitleGenerator, Config


def test_generate_title_from_text_empty_text():
    """Test generate_title_from_text with empty text."""
    result = TitleGenerator.generate_title_from_text("")
    assert result is None


def test_generate_title_from_text_no_api_key():
    """Test generate_title_from_text when no API key is available."""
    # Mock os.environ.get to return None for the API key
    with patch('generate_slides.os.environ.get', return_value=None):
        # Mock the fallback method
        with patch.object(TitleGenerator, 'generate_fallback_title', return_value="fallback_title") as mock_fallback:
            result = TitleGenerator.generate_title_from_text("Sample text")
            
            # Check that the fallback method was called
            mock_fallback.assert_called_once_with("Sample text")
            # Check that the result is from the fallback method
            assert result == "fallback_title"


def test_generate_title_from_text_api_success():
    """Test generate_title_from_text when the API call succeeds."""
    # Mock os.environ.get to return an API key
    with patch('generate_slides.os.environ.get', return_value="fake_api_key"):
        # Mock the requests.post method
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Sample Title"}}]
        }
        
        with patch('generate_slides.requests.post', return_value=mock_response):
            # Mock the _clean_title method
            with patch.object(TitleGenerator, '_clean_title', return_value="sample_title") as mock_clean:
                result = TitleGenerator.generate_title_from_text("Sample text")
                
                # Check that the API was called with the correct arguments
                assert mock_clean.call_args[0][0] == "Sample Title"
                # Check that the result is the cleaned title
                assert result == "sample_title"


def test_generate_title_from_text_api_error():
    """Test generate_title_from_text when the API call fails."""
    # Mock os.environ.get to return an API key
    with patch('generate_slides.os.environ.get', return_value="fake_api_key"):
        # Mock the requests.post method to return an error
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        
        with patch('generate_slides.requests.post', return_value=mock_response):
            # Mock the fallback method
            with patch.object(TitleGenerator, 'generate_fallback_title', return_value="fallback_title") as mock_fallback:
                result = TitleGenerator.generate_title_from_text("Sample text")
                
                # Check that the fallback method was called
                mock_fallback.assert_called_once_with("Sample text")
                # Check that the result is from the fallback method
                assert result == "fallback_title"


def test_generate_title_from_text_exception():
    """Test generate_title_from_text when an exception occurs."""
    # Mock os.environ.get to return an API key
    with patch('generate_slides.os.environ.get', return_value="fake_api_key"):
        # Mock the requests.post method to raise an exception
        with patch('generate_slides.requests.post', side_effect=Exception("Test error")):
            # Mock the fallback method
            with patch.object(TitleGenerator, 'generate_fallback_title', return_value="fallback_title") as mock_fallback:
                result = TitleGenerator.generate_title_from_text("Sample text")
                
                # Check that the fallback method was called
                mock_fallback.assert_called_once_with("Sample text")
                # Check that the result is from the fallback method
                assert result == "fallback_title"


def test_generate_fallback_title_success():
    """Test generate_fallback_title with successful text processing."""
    # Mock the _clean_title method
    with patch.object(TitleGenerator, '_clean_title', return_value="clean_title") as mock_clean:
        result = TitleGenerator.generate_fallback_title("This is a sample text")
        
        # Check that _clean_title was called with the joined words
        mock_clean.assert_called_once_with("This_is_a_sample_text")
        # Check that the result is the cleaned title
        assert result == "clean_title"


def test_generate_fallback_title_exception():
    """Test generate_fallback_title when an exception occurs."""
    # Mock the text processing to raise an exception
    with patch.object(TitleGenerator, '_clean_title', side_effect=Exception("Test error")):
        result = TitleGenerator.generate_fallback_title("Sample text")
        
        # Check that "untitled" is returned
        assert result == "untitled"


def test_clean_title():
    """Test _clean_title with various inputs."""
    # Test with special characters
    result = TitleGenerator._clean_title("Sample Title! @#$%^&*()")
    assert result == "Sample_Title"
    
    # Test with multiple spaces and underscores
    result = TitleGenerator._clean_title("Sample   Title___with___spaces")
    assert result == "Sample_Title_with_spaces"
    
    # Test with leading and trailing underscores
    result = TitleGenerator._clean_title("_Sample Title_")
    assert result == "Sample_Title"
    
    # Test with a title that's too long
    original_max_length = Config.MAX_TITLE_LENGTH
    Config.MAX_TITLE_LENGTH = 10
    try:
        result = TitleGenerator._clean_title("This is a very long title that exceeds the maximum length")
        assert len(result) == 10
        assert result == "This_is_a_"
    finally:
        Config.MAX_TITLE_LENGTH = original_max_length
