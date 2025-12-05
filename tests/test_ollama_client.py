"""Integration tests for OllamaClient.

These tests verify the OllamaClient's retry logic, timeout handling,
and AutoTuner integration using mocked HTTP requests.
"""

import unittest
from pathlib import Path
import sys
import time
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcq_flashcards.core.client import OllamaClient
from mcq_flashcards.core.config import Config


class TestOllamaClient(unittest.TestCase):
    """Test OllamaClient integration."""
    
    def setUp(self):
        """Create a client instance for testing."""
        self.config = Config()
        self.client = OllamaClient(self.config)
    
    @patch('requests.post')
    def test_successful_request(self, mock_post):
        """Test successful API request."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "llama3.1:8b",
            "response": "Test MCQ output",
            "done": True
        }
        mock_post.return_value = mock_response
        
        worker_state = {"delay": 0.5, "retries": 0}
        result = self.client.generate("Test prompt", worker_state)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["response"], "Test MCQ output")
        self.assertEqual(worker_state["retries"], 0)
    
    @patch('requests.post')
    def test_retry_on_failure(self, mock_post):
        """Test that client retries on failure."""
        # First call fails, second succeeds
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 500
        
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "response": "Success after retry"
        }
        
        mock_post.side_effect = [mock_response_fail, mock_response_success]
        
        worker_state = {"delay": 0.01, "retries": 0}  # Small delay for fast test
        result = self.client.generate("Test prompt", worker_state)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["response"], "Success after retry")
        self.assertEqual(mock_post.call_count, 2)
    
    @patch('requests.post')
    def test_max_retries_exceeded(self, mock_post):
        """Test that client gives up after max retries."""
        # Always fail
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        
        worker_state = {"delay": 0.01, "retries": 0}
        result = self.client.generate("Test prompt", worker_state)
        
        self.assertIsNone(result)
        # Should have tried MAX_RETRIES times (3)
        self.assertEqual(mock_post.call_count, 3)
    
    @patch('requests.post')
    def test_timeout_handling(self, mock_post):
        """Test that client handles timeouts gracefully."""
        import requests
        mock_post.side_effect = requests.Timeout("Request timed out")
        
        worker_state = {"delay": 0.01, "retries": 0}
        result = self.client.generate("Test prompt", worker_state)
        
        self.assertIsNone(result)
    
    @patch('requests.post')
    def test_connection_error_handling(self, mock_post):
        """Test that client handles connection errors."""
        import requests
        mock_post.side_effect = requests.ConnectionError("Connection failed")
        
        worker_state = {"delay": 0.01, "retries": 0}
        result = self.client.generate("Test prompt", worker_state)
        
        self.assertIsNone(result)
    
    @patch('requests.get')
    def test_check_connection_success(self, mock_get):
        """Test connection check when server is available."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        self.assertTrue(self.client.check_connection())
    
    @patch('requests.get')
    def test_check_connection_failure(self, mock_get):
        """Test connection check when server is unavailable."""
        import requests
        mock_get.side_effect = requests.ConnectionError("Server not found")
        
        self.assertFalse(self.client.check_connection())
    
    @patch('mcq_flashcards.core.client.AUTOTUNER')
    @patch('requests.post')
    def test_autotuner_integration(self, mock_post, mock_autotuner):
        """Test that client integrates with AutoTuner."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Test"}
        mock_post.return_value = mock_response
        
        mock_autotuner.recommend_throttle.return_value = 1.0
        
        worker_state = {"delay": 0.5, "retries": 0}
        self.client.generate("Test prompt", worker_state)
        
        # Verify AutoTuner methods were called
        self.assertTrue(mock_autotuner.add_latency.called,
                       "AutoTuner.add_latency should be called")


    def test_generate_empty_prompt(self):
        """Test generate with empty prompt."""
        response = self.client.generate("", {"retries": 0, "delay": 1.0})
        self.assertIsNone(response)

if __name__ == '__main__':
    unittest.main()
