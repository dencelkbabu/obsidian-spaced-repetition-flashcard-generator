"""Unit tests for cache clearing functionality.

These tests verify that cache clearing works correctly for both
selective (subject-specific) and global (ALL) clearing.
"""

import unittest
from pathlib import Path
import sys
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcq_flashcards.core.config import CACHE_DIR


class TestCacheClearing(unittest.TestCase):
    """Test cache clearing functionality."""
    
    def setUp(self):
        """Create a temporary cache directory for testing."""
        self.test_cache_dir = Path(tempfile.mkdtemp())
        self.original_cache_dir = CACHE_DIR
        
        # Monkey-patch CACHE_DIR for testing
        import mcq_flashcards.core.config as config_module
        config_module.CACHE_DIR = self.test_cache_dir
        
        # Also patch in cli module
        import cli
        cli.CACHE_DIR = self.test_cache_dir
    
    def tearDown(self):
        """Clean up temporary cache directory."""
        if self.test_cache_dir.exists():
            shutil.rmtree(self.test_cache_dir)
        
        # Restore original CACHE_DIR
        import mcq_flashcards.core.config as config_module
        config_module.CACHE_DIR = self.original_cache_dir
        
        import cli
        cli.CACHE_DIR = self.original_cache_dir
    
    def test_selective_cache_clearing(self):
        """Test that clearing cache for one subject doesn't affect others."""
        # Arrange: Create cache files for multiple subjects
        (self.test_cache_dir / "ACCT1001_abc123.json").touch()
        (self.test_cache_dir / "ACCT1001_def456.json").touch()
        (self.test_cache_dir / "COMM1001_xyz789.json").touch()
        (self.test_cache_dir / "MATH1001_qwe321.json").touch()
        
        # Act: Clear only ACCT1001 cache
        from cli import clear_cache
        clear_cache("ACCT1001")
        
        # Assert: ACCT1001 files deleted, others remain
        self.assertFalse((self.test_cache_dir / "ACCT1001_abc123.json").exists(),
                        "ACCT1001 cache should be deleted")
        self.assertFalse((self.test_cache_dir / "ACCT1001_def456.json").exists(),
                        "ACCT1001 cache should be deleted")
        self.assertTrue((self.test_cache_dir / "COMM1001_xyz789.json").exists(),
                       "COMM1001 cache should NOT be deleted")
        self.assertTrue((self.test_cache_dir / "MATH1001_qwe321.json").exists(),
                       "MATH1001 cache should NOT be deleted")
    
    def test_global_cache_clearing(self):
        """Test that clearing ALL cache deletes everything."""
        # Arrange: Create cache files for multiple subjects
        (self.test_cache_dir / "ACCT1001_abc123.json").touch()
        (self.test_cache_dir / "COMM1001_xyz789.json").touch()
        (self.test_cache_dir / "MATH1001_qwe321.json").touch()
        
        # Act: Clear ALL cache
        from cli import clear_cache
        clear_cache("ALL")
        
        # Assert: All cache files deleted
        cache_files = list(self.test_cache_dir.glob("*.json"))
        self.assertEqual(len(cache_files), 0,
                        f"All cache should be deleted, but found: {cache_files}")
    
    def test_clearing_nonexistent_subject(self):
        """Test that clearing cache for non-existent subject doesn't crash."""
        # Arrange: Create some cache files
        (self.test_cache_dir / "ACCT1001_abc123.json").touch()
        
        # Act: Clear cache for subject with no cache files
        from cli import clear_cache
        try:
            clear_cache("NONEXISTENT")
            success = True
        except Exception as e:
            success = False
            self.fail(f"clear_cache should not crash on non-existent subject: {e}")
        
        # Assert: Original cache files still exist
        self.assertTrue(success, "clear_cache should handle non-existent subjects gracefully")
        self.assertTrue((self.test_cache_dir / "ACCT1001_abc123.json").exists(),
                       "Existing cache should not be affected")


if __name__ == '__main__':
    unittest.main()
