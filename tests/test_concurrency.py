"""Tests for concurrent access and thread safety."""

import unittest
import threading
import tempfile
import shutil
import time
import json
from pathlib import Path
import sys
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcq_flashcards.core.generator import FlashcardGenerator
from mcq_flashcards.core.config import Config, CACHE_DIR

class TestConcurrentCache(unittest.TestCase):
    """Test thread safety of caching mechanism."""
    
    def setUp(self):
        """Create test environment."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.class_root = self.test_dir / "class_root"
        self.output_dir = self.test_dir / "output"
        self.class_root.mkdir()
        self.output_dir.mkdir()
        
        # Mock config
        self.config = Config(dev_mode=True, workers=4)
        
        # Create generator
        self.generator = FlashcardGenerator(
            "TEST101", 
            self.config, 
            self.class_root, 
            self.output_dir
        )
        
        # Ensure clean cache for this test
        self.original_cache_dir = CACHE_DIR
        self.test_cache_dir = self.test_dir / "_cache"
        self.test_cache_dir.mkdir()
        
        # Monkey patch CACHE_DIR in generator module
        self.cache_patcher = patch('mcq_flashcards.core.generator.CACHE_DIR', self.test_cache_dir)
        self.cache_patcher.start()
        
        # Monkey patch CACHE_DIR in generator instance
        # Note: We can't easily patch the global constant, but we can patch 
        # the generator's get_cache_key method to use our test dir
        self.original_get_cache_key = self.generator.get_cache_key
        self.generator.get_cache_key = self._mock_get_cache_key

    def _mock_get_cache_key(self, text):
        """Mock get_cache_key to use test cache dir."""
        import hashlib
        combined = f"{self.config.model}_{text}"
        hash_key = hashlib.md5(combined.encode()).hexdigest()
        return self.test_cache_dir / f"{self.generator.subject}_{hash_key}.json"

    def tearDown(self):
        """Clean up."""
        self.cache_patcher.stop()
        shutil.rmtree(self.test_dir)
        # Restore method
        self.generator.get_cache_key = self.original_get_cache_key

    def test_concurrent_cache_writes(self):
        """Test multiple threads trying to cache the same content."""
        text = "Concurrent test content"
        expected_response = "MCQ Content"
        
        # Mock client to return response with slight delay
        def mock_generate(*args, **kwargs):
            time.sleep(0.01) # Simulate network delay
            return {"response": expected_response}
            
        self.generator.client.generate = MagicMock(side_effect=mock_generate)
        self.generator.validator.validate = MagicMock(return_value=True)
        self.generator.cleaner.clean_ai_output = MagicMock(return_value=expected_response)
        
        # Run 10 threads trying to generate same content
        n_threads = 10
        with ThreadPoolExecutor(max_workers=n_threads) as executor:
            futures = [
                executor.submit(self.generator.generate_single, text, f"job_{i}") 
                for i in range(n_threads)
            ]
            results = [f.result() for f in futures]
            
        # Verify all succeeded
        for res in results:
            self.assertEqual(res, expected_response)
            
        # Verify cache file exists and is valid JSON
        cache_path = self.generator.get_cache_key(text)
        self.assertTrue(cache_path.exists())
        
        with open(cache_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
            self.assertEqual(content, expected_response)

    def test_concurrent_read_write(self):
        """Test mixed reading and writing."""
        text = "Read/Write content"
        expected_response = "MCQ Content"
        
        # Pre-populate cache
        cache_path = self.generator.get_cache_key(text)
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(expected_response, f)
            
        def worker(i):
            if i % 2 == 0:
                # Reader
                return self.generator.generate_single(text, f"reader_{i}")
            else:
                # Writer (simulated by deleting cache first? No, that's race condition we want to avoid in real code)
                # Instead, let's just call generate_single. If cache exists, it reads.
                # To test write contention, we need different texts or force regeneration.
                # Let's try different texts for writers.
                return self.generator.generate_single(f"Unique content {i}", f"writer_{i}")

        # Mock for writers
        self.generator.client.generate = MagicMock(return_value={"response": expected_response})
        self.generator.validator.validate = MagicMock(return_value=True)
        self.generator.cleaner.clean_ai_output = MagicMock(return_value=expected_response)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker, i) for i in range(10)]
            results = [f.result() for f in futures]
            
        # Just verify no crashes
        self.assertEqual(len(results), 10)

if __name__ == '__main__':
    unittest.main()
