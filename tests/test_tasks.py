
import pytest
from unittest.mock import patch
from tasks import transcribe_and_summarize

def test_transcribe_and_summarize_success():
    """
    Test the Celery task logic with mocked external calls to avoid
    real network requests during CI/testing.
    """
    mock_transcript = "This is a test transcript that is long enough to be summarized."
    mock_summary = "This is a test summary."

    with patch('tasks.transcribe_audio_from_video') as mock_transcribe:
        with patch('tasks.summarize_text') as mock_summarize:
            
            # Setup mocks
            mock_transcribe.return_value = mock_transcript
            mock_summarize.return_value = mock_summary

            # Call the function directly (synchronously) for testing
            result = transcribe_and_summarize(video_url="http://fake.url", video_id="fake_id")

            # Assertions
            assert result['status'] == 'ok'
            assert result['summary'] == mock_summary
            assert result['text_len'] == len(mock_transcript)
            
            mock_transcribe.assert_called_once()
            mock_summarize.assert_called_once_with(mock_transcript)

def test_transcribe_and_summarize_retry():
    """
    Test that the task retries on exception (mocking the retry mechanism).
    """
    with patch('tasks.transcribe_audio_from_video') as mock_transcribe:
        with patch('tasks.transcribe_and_summarize.retry') as mock_retry:
            # Setup mock to raise exception
            mock_transcribe.side_effect = Exception("Network Error")
            mock_retry.side_effect = Exception("Retry Triggered") # specific to stop execution flow in test

            try:
                transcribe_and_summarize(video_url="http://fail.url")
            except Exception as e:
                assert str(e) == "Retry Triggered"
            
            mock_retry.assert_called()
