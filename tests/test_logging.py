"""Unit tests for logging configuration."""

import unittest
import shutil
import logging
import os
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcq_flashcards.core.config import setup_logging, LOG_DIR, LOG_FILE

class TestLogging(unittest.TestCase):
    """Test logging setup."""
    
    def setUp(self):
        """Clean up logs before test."""
        # Close all handlers first
        logger = logging.getLogger("FlashcardGen")
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
        
        # Also close root logger handlers if any point to the file
        root = logging.getLogger()
        for handler in root.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                handler.close()
                root.removeHandler(handler)

        if LOG_DIR.exists():
            try:
                shutil.rmtree(LOG_DIR)
            except PermissionError:
                pass # Still might fail if another process holds it, but we try
        
        LOG_DIR.mkdir(exist_ok=True)
        
    def tearDown(self):
        """Clean up after test."""
        # Close handlers to release file locks
        logger = logging.getLogger("FlashcardGen")
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
            
        if LOG_DIR.exists():
            try:
                shutil.rmtree(LOG_DIR)
            except PermissionError:
                pass # Windows file locking might prevent deletion
                
    def test_log_creation(self):
        """Test that log file is created."""
        logger = setup_logging()
        logger.info("Test log message")
        
        self.assertTrue(LOG_FILE.exists())
        content = LOG_FILE.read_text(encoding='utf-8')
        self.assertIn("Test log message", content)
        
    def test_log_rotation(self):
        """Test that logs rotate."""
        # Reconfigure with small maxBytes for testing
        from logging.handlers import RotatingFileHandler
        
        logger = logging.getLogger("FlashcardGen")
        # Remove existing handlers
        for h in logger.handlers[:]:
            h.close()
            logger.removeHandler(h)
            
        handler = RotatingFileHandler(
            LOG_FILE, 
            maxBytes=100,  # Very small size
            backupCount=2,
            encoding='utf-8'
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        # Write enough to trigger rotation
        for i in range(10):
            logger.info(f"Line {i} " * 5)
            
        # Check if backup files exist
        # Note: RotatingFileHandler creates .1, .2 etc.
        log_files = list(LOG_DIR.glob("flashcard_gen.log*"))
        self.assertGreater(len(log_files), 1, "Should have rotated logs")

if __name__ == '__main__':
    unittest.main()
