"""Unit tests for caching mechanism."""

import pytest
import json
import shutil
from pathlib import Path
import sys
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcq_flashcards.core.generator import FlashcardGenerator
from mcq_flashcards.core.config import Config, CACHE_DIR

@pytest.fixture
def clean_cache():
    """Fixture to clean up cache before and after tests."""
    if CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR)
    CACHE_DIR.mkdir(exist_ok=True)
    yield
    if CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR)

@pytest.fixture
def generator():
    """Fixture to create a generator instance."""
    config = Config(dev_mode=True)
    return FlashcardGenerator("TEST101", config, Path("."), Path("."))

def test_cache_key_generation(generator):
    """Test that cache keys are generated correctly with .json extension."""
    text = "Sample text content"
    key = generator.get_cache_key(text)
    
    assert isinstance(key, Path)
    assert key.suffix == ".json"
    assert key.parent == CACHE_DIR

def test_cache_write_read(generator, clean_cache):
    """Test writing to and reading from cache using JSON."""
    text = "Unique content for caching"
    response = "Cached response data"
    
    # Manually write to cache (simulating what generate_single does internally)
    cache_path = generator.get_cache_key(text)
    
    # Write JSON
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump({"response": response, "version": "1.0"}, f)
        
    # Verify file exists and is JSON
    assert cache_path.exists()
    content = json.loads(cache_path.read_text(encoding='utf-8'))
    assert content["response"] == response

def test_cache_invalidation_old_pickle(generator, clean_cache):
    """Test that old .pkl files are ignored."""
    text = "Old pickle content"
    # Create a fake .pkl file
    pkl_path = CACHE_DIR / "old_cache.pkl"
    pkl_path.write_bytes(b"some binary data")
    
    # The generator should look for .json, not .pkl
    key = generator.get_cache_key(text)
    assert key.suffix == ".json"
    assert not key.exists()
