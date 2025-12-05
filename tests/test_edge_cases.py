"""Tests for edge cases (large files, unicode)."""

import unittest
import tempfile
import shutil
import os
from pathlib import Path
import sys
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcq_flashcards.core.generator import FlashcardGenerator
from mcq_flashcards.core.config import Config

class TestEdgeCases(unittest.TestCase):
    """Test edge cases for robustness."""
    
    def setUp(self):
        """Create test environment."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.class_root = self.test_dir / "class_root"
        self.output_dir = self.test_dir / "output"
        self.class_root.mkdir()
        self.output_dir.mkdir()
        
        self.config = Config(dev_mode=True)
        self.generator = FlashcardGenerator(
            "TEST101", 
            self.config, 
            self.class_root, 
            self.output_dir
        )
        
        # Mock client to avoid API calls
        self.generator.client.generate = MagicMock(return_value={"response": "MCQ Content"})
        self.generator.validator.validate = MagicMock(return_value=True)

        # Monkey patch CACHE_DIR in generator module
        self.test_cache_dir = self.test_dir / "_cache"
        self.test_cache_dir.mkdir()
        self.cache_patcher = patch('mcq_flashcards.core.generator.CACHE_DIR', self.test_cache_dir)
        self.cache_patcher.start()
        
        # Also patch get_cache_key to use test dir (as it might use self.config.model etc)
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
        self.generator.get_cache_key = self.original_get_cache_key
        shutil.rmtree(self.test_dir)

    def test_large_file_processing(self):
        """Test processing of a large file (>10MB)."""
        # Create a 11MB file
        large_file = self.test_dir / "large_note.md"
        
        # Write in chunks to avoid memory spike during creation
        chunk = "Content line with some text repeated.\n" * 1000 # ~38KB
        with open(large_file, 'w', encoding='utf-8') as f:
            f.write("## 📝 Notes\n")
            for _ in range(300): # 300 * 38KB ≈ 11.4MB
                f.write(chunk)
                
        # Verify size
        size_mb = large_file.stat().st_size / (1024 * 1024)
        self.assertGreater(size_mb, 10)
        
        # Test extraction (this uses regex, might be slow)
        summary, links = self.generator.extract_summary(large_file)
        
        # Should not crash, but might return None if regex fails or times out (though we don't have timeout on regex)
        # Actually, our regex looks for "## Key Concepts", if not found it returns whole content cleaned.
        # Cleaning 11MB might be slow but should work.
        
        # Note: extract_summary reads whole file into memory.
        self.assertIsNotNone(summary)
        # Should be truncated or handled? The current implementation reads all.
        # We just want to ensure it doesn't crash.

    def test_unicode_and_emojis(self):
        """Test handling of Unicode characters and emojis."""
        content = """
## 📝 Notes
Here is some content with emojis: 🚀 📝 ⚠️
And some non-ASCII: Español, Français, 中文.
Math symbols: ∑, ∫, π.

## 💡 Key Concepts & Summary
The concept of [[Übermensch]] is complex.
Also [[Naïve Bayes]].
"""
        note_path = self.test_dir / "unicode_note.md"
        note_path.write_text(content, encoding='utf-8')
        
        summary, links = self.generator.extract_summary(note_path)
        
        self.assertIn("Übermensch", links)
        self.assertIn("Naïve Bayes", links)
        self.assertIn("🚀", summary)
        self.assertIn("中文", summary)
        
        # Test generation with unicode input
        result = self.generator.generate_single(summary, "unicode_test")
        self.assertIsNotNone(result)

if __name__ == '__main__':
    unittest.main()
