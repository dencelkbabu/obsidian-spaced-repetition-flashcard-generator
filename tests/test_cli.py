"""Unit tests for CLI argument parsing and functions.

These tests verify CLI argument parsing, subject/semester selection,
and other CLI utility functions.
"""

import unittest
from pathlib import Path
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from io import StringIO

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import cli
from mcq_flashcards.core.config import BCOM_ROOT


class TestCLIFunctions(unittest.TestCase):
    """Test CLI utility functions."""
    
    @patch('requests.get')
    def test_check_ollama_running(self, mock_get):
        """Test Ollama connection check when running."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = cli.check_ollama()
        self.assertTrue(result)
    
    @patch('requests.get')
    def test_check_ollama_not_running(self, mock_get):
        """Test Ollama connection check when not running."""
        import requests
        mock_get.side_effect = requests.ConnectionError("Connection refused")
        
        result = cli.check_ollama()
        self.assertFalse(result)
    
    def test_get_semesters(self):
        """Test getting list of semesters."""
        # This will use actual BCOM_ROOT, so just verify it returns a list
        semesters = cli.get_semesters()
        self.assertIsInstance(semesters, list)
    
    @patch('cli.get_semesters')
    @patch('builtins.input')
    def test_select_semester_default(self, mock_input, mock_get_semesters):
        """Test semester selection with default (Enter key)."""
        mock_get_semesters.return_value = ["Semester One", "Semester Two"]
        mock_input.return_value = ""  # User presses Enter
        
        result = cli.select_semester()
        self.assertEqual(result, "Semester One")  # DEFAULT_SEMESTER
    
    @patch('cli.get_semesters')
    @patch('builtins.input')
    def test_select_semester_by_number(self, mock_input, mock_get_semesters):
        """Test semester selection by number."""
        mock_get_semesters.return_value = ["Semester One", "Semester Two"]
        mock_input.return_value = "2"
        
        result = cli.select_semester()
        self.assertEqual(result, "Semester Two")
    
    @patch('cli.get_semesters')
    @patch('builtins.input')
    def test_select_semester_invalid_number(self, mock_input, mock_get_semesters):
        """Test semester selection with invalid number."""
        mock_get_semesters.return_value = ["Semester One"]
        mock_input.return_value = "99"
        
        result = cli.select_semester()
        self.assertIsNone(result)
    
    @patch('builtins.input')
    def test_select_week_specific(self, mock_input):
        """Test week selection with specific number."""
        mock_input.return_value = "5"
        
        result = cli.select_week()
        self.assertEqual(result, 5)
    
    @patch('builtins.input')
    def test_select_week_all(self, mock_input):
        """Test week selection for all weeks."""
        mock_input.return_value = ""  # Enter for all
        
        result = cli.select_week()
        self.assertIsNone(result)
    
    @patch('builtins.input')
    def test_select_preset_default(self, mock_input):
        """Test study mode preset selection with default."""
        mock_input.return_value = ""  # Default to exam prep
        
        bloom, difficulty = cli.select_preset()
        self.assertEqual(bloom, "apply")
        self.assertEqual(difficulty, "medium")
    
    @patch('builtins.input')
    def test_select_preset_review(self, mock_input):
        """Test selecting review preset."""
        mock_input.return_value = "2"  # Review mode
        
        bloom, difficulty = cli.select_preset()
        self.assertEqual(bloom, "remember")
        self.assertEqual(difficulty, "easy")
    
    @patch('builtins.input')
    def test_select_preset_deep(self, mock_input):
        """Test selecting deep study preset."""
        mock_input.return_value = "3"  # Deep study
        
        bloom, difficulty = cli.select_preset()
        self.assertEqual(bloom, "analyze")
        self.assertEqual(difficulty, "hard")
    
    @patch('builtins.input')
    def test_select_preset_mixed(self, mock_input):
        """Test selecting mixed preset."""
        mock_input.return_value = "4"  # Mixed
        
        bloom, difficulty = cli.select_preset()
        self.assertIsNone(bloom)
        self.assertIsNone(difficulty)


class TestCLIArgumentParsing(unittest.TestCase):
    """Test CLI argument parsing."""
    
    def setUp(self):
        """Set up test environment."""
        # Store original sys.argv
        self.original_argv = sys.argv.copy()
    
    def tearDown(self):
        """Restore original sys.argv."""
        sys.argv = self.original_argv
    
    @patch('cli.run_dev')
    def test_dev_mode_with_subject(self, mock_run_dev):
        """Test dev mode with subject argument."""
        sys.argv = ['cli.py', '-d', 'ACCT1001']
        
        cli.main()
        
        mock_run_dev.assert_called_once()
    
    @patch('cli.run_interactive')
    def test_interactive_mode_no_args(self, mock_run_interactive):
        """Test interactive mode when no arguments provided."""
        sys.argv = ['cli.py']
        
        cli.main()
        
        mock_run_interactive.assert_called_once()


if __name__ == '__main__':
    unittest.main()
