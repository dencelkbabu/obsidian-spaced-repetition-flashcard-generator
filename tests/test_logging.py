"""Unit tests for logging configuration."""

import shutil
import logging
import pytest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcq_flashcards.core.config import setup_logging, LOG_DIR, LOG_FILE

@pytest.fixture
def clean_logs():
    """Fixture to clean up logs before and after tests."""
    # Setup: Close handlers
    _close_handlers()
    
    if LOG_DIR.exists():
        try:
            shutil.rmtree(LOG_DIR)
        except PermissionError:
            pass
    
    LOG_DIR.mkdir(exist_ok=True)
    
    yield
    
    # Teardown: Close handlers and cleanup
    _close_handlers()
    
    if LOG_DIR.exists():
        try:
            shutil.rmtree(LOG_DIR)
        except PermissionError:
            pass

def _close_handlers():
    """Helper to close all logging handlers."""
    logger = logging.getLogger("FlashcardGen")
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)
    
    root = logging.getLogger()
    for handler in root.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            handler.close()
            root.removeHandler(handler)

def test_log_creation(clean_logs):
    """Test that log file is created."""
    logger = setup_logging()
    logger.info("Test log message")
    
    assert LOG_FILE.exists()
    content = LOG_FILE.read_text(encoding='utf-8')
    assert "Test log message" in content

def test_log_rotation(clean_logs):
    """Test that logs rotate."""
    from logging.handlers import RotatingFileHandler
    
    logger = logging.getLogger("FlashcardGen")
    _close_handlers()
        
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
    log_files = list(LOG_DIR.glob("flashcard_gen.log*"))
    assert len(log_files) > 1, "Should have rotated logs"
