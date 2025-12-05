"""Test parallel file reading functionality."""

import unittest
from pathlib import Path
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcq_flashcards.core.generator import FlashcardGenerator
from mcq_flashcards.core.config import Config


class TestParallelFileReading(unittest.TestCase):
    """Test parallel file extraction with ThreadPoolExecutor."""
    
    def setUp(self):
        """Create test environment with multiple files."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.class_root = self.test_dir / "class_root"
        self.output_dir = self.test_dir / "output"
        self.class_root.mkdir()
        self.output_dir.mkdir()
        
        # Create test subject directory
        self.subject_dir = self.class_root / "TEST1001"
        self.subject_dir.mkdir()
        
        # Create Recorded Lectures directory
        self.lectures_dir = self.subject_dir / "Recorded Lectures" / "W01 - Test"
        self.lectures_dir.mkdir(parents=True)
        
        # Create multiple test lecture files
        for i in range(10):
            note_path = self.lectures_dir / f"W01 L{i:02d} TEST1001 - Lecture {i}.md"
            note_path.write_text(f"""---
tags:
- lecture/TEST1001
---

## 📝 Notes

Content for lecture {i} about [[Concept{i}]].

## 💡 Key Concepts & Summary

This lecture covered topic {i}.
""", encoding='utf-8')
        
        self.config = Config(dev_mode=True)
        self.generator = FlashcardGenerator(
            "TEST1001",
            self.config,
            self.class_root,
            self.output_dir
        )
        
        # Ensure cache dir exists
        from mcq_flashcards.core.config import CACHE_DIR
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    def tearDown(self):
        """Clean up test environment."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_parallel_file_reading_correctness(self):
        """Test that parallel reading extracts all files correctly."""
        files = sorted(self.lectures_dir.glob("*.md"))
        self.assertEqual(len(files), 10, "Should have 10 test files")
        
        # Extract summaries in parallel (this happens in process_week)
        import concurrent.futures
        from tqdm import tqdm
        
        lecture_jobs = []
        concepts_set = set()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_file = {executor.submit(self.generator.extract_summary, p): p for p in files}
            
            for future in concurrent.futures.as_completed(future_to_file):
                p = future_to_file[future]
                try:
                    summary, links = future.result()
                    concepts_set.update(links)
                    if summary:
                        lecture_jobs.append((summary, p.name, False))
                except Exception as e:
                    self.fail(f"Failed to extract from {p.name}: {e}")
        
        # Verify all files were processed
        self.assertEqual(len(lecture_jobs), 10, "Should extract 10 summaries")
        
        # Verify concepts were extracted
        self.assertEqual(len(concepts_set), 10, "Should extract 10 unique concepts")
        for i in range(10):
            self.assertIn(f"Concept{i}", concepts_set, f"Should extract Concept{i}")
    
    def test_parallel_vs_sequential_equivalence(self):
        """Test that parallel reading produces same results as sequential."""
        files = sorted(self.lectures_dir.glob("*.md"))
        
        # Sequential extraction
        sequential_jobs = []
        sequential_concepts = set()
        for p in files:
            summary, links = self.generator.extract_summary(p)
            sequential_concepts.update(links)
            if summary:
                sequential_jobs.append((summary, p.name, False))
        
        # Parallel extraction
        import concurrent.futures
        parallel_jobs = []
        parallel_concepts = set()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_file = {executor.submit(self.generator.extract_summary, p): p for p in files}
            
            for future in concurrent.futures.as_completed(future_to_file):
                p = future_to_file[future]
                summary, links = future.result()
                parallel_concepts.update(links)
                if summary:
                    parallel_jobs.append((summary, p.name, False))
        
        # Results should be equivalent (order may differ)
        self.assertEqual(len(sequential_jobs), len(parallel_jobs))
        self.assertEqual(sequential_concepts, parallel_concepts)
    
    def test_parallel_error_handling(self):
        """Test that errors in one file don't break parallel processing."""
        files = sorted(self.lectures_dir.glob("*.md"))
        
        # Mock extract_summary to fail on one file
        original_extract = self.generator.extract_summary
        call_count = [0]
        
        def mock_extract(path):
            call_count[0] += 1
            if "L05" in path.name:
                raise ValueError("Simulated error")
            return original_extract(path)
        
        import concurrent.futures
        lecture_jobs = []
        error_count = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_file = {executor.submit(mock_extract, p): p for p in files}
            
            for future in concurrent.futures.as_completed(future_to_file):
                p = future_to_file[future]
                try:
                    summary, links = future.result()
                    if summary:
                        lecture_jobs.append((summary, p.name, False))
                except Exception:
                    error_count += 1
        
        # Should process 9 files successfully, 1 failed
        self.assertEqual(len(lecture_jobs), 9, "Should extract 9 summaries (1 failed)")
        self.assertEqual(error_count, 1, "Should have 1 error")
        self.assertEqual(call_count[0], 10, "Should attempt all 10 files")


if __name__ == '__main__':
    unittest.main()
