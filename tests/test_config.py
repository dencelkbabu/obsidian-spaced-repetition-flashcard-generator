"""Unit tests for Config validation."""

import unittest
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcq_flashcards.core.config import Config

class TestConfig(unittest.TestCase):
    """Test Config validation."""
    
    @patch('mcq_flashcards.core.config.get_semester_paths')
    def test_validate_valid(self, mock_paths):
        """Test validation with valid settings."""
        # Mock existing directory
        mock_root = MagicMock()
        mock_root.exists.return_value = True
        mock_paths.return_value = (mock_root, MagicMock())
        
        config = Config(start_week=1, end_week=12, workers=4)
        self.assertTrue(config.validate())
        
    @patch('mcq_flashcards.core.config.get_semester_paths')
    def test_validate_invalid_path(self, mock_paths):
        """Test validation with missing semester directory."""
        # Mock missing directory
        mock_root = MagicMock()
        mock_root.exists.return_value = False
        mock_paths.return_value = (mock_root, MagicMock())
        
        config = Config()
        self.assertFalse(config.validate())
        
    @patch('mcq_flashcards.core.config.get_semester_paths')
    def test_validate_invalid_weeks(self, mock_paths):
        """Test validation with invalid week range."""
        # Mock existing directory
        mock_root = MagicMock()
        mock_root.exists.return_value = True
        mock_paths.return_value = (mock_root, MagicMock())
        
        # Invalid: start > end
        config = Config(start_week=10, end_week=5)
        self.assertFalse(config.validate())
        
        # Invalid: start < 1
        config = Config(start_week=0, end_week=5)
        self.assertFalse(config.validate())
        
    @patch('mcq_flashcards.core.config.get_semester_paths')
    def test_validate_invalid_workers(self, mock_paths):
        """Test validation with invalid worker count."""
        # Mock existing directory
        mock_root = MagicMock()
        mock_root.exists.return_value = True
        mock_paths.return_value = (mock_root, MagicMock())
        
        # Invalid: 0 workers
        config = Config(workers=0)
        self.assertFalse(config.validate())
        
        # Invalid: too many workers
        config = Config(workers=20)
        self.assertFalse(config.validate())

if __name__ == '__main__':
    unittest.main()
