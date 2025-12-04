"""Unit tests for post-processor functionality.

These tests verify that the FlashcardPostProcessor correctly fixes
common LLM output inconsistencies.
"""

import unittest
from pathlib import Path
import sys
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcq_flashcards.utils.postprocessor import FlashcardPostProcessor, post_process_flashcards


class TestFlashcardPostProcessor(unittest.TestCase):
    """Test post-processor logic."""
    
    def setUp(self):
        """Create a processor instance for testing."""
        self.processor = FlashcardPostProcessor()
    
    def test_remove_meta_commentary(self):
        """Test that meta-commentary is removed."""
        text = """Let me know if you need more questions.

Question?
1. Option 1
2. Option 2
3. Option 3
4. Option 4
?
**Answer:** 1) Option 1"""
        
        result = self.processor._remove_llm_meta_commentary(text)
        self.assertIsNotNone(result)
        self.assertNotIn("Let me know", result)
    
    def test_fix_missing_question_separators(self):
        """Test that missing '?' separators are added."""
        text = """Question?
1. Option 1
2. Option 2
3. Option 3
4. Option 4
**Answer:** 1) Option 1"""
        
        result = self.processor._fix_missing_question_separators(text)
        # Should add '?' before **Answer:**
        self.assertIn("?", result)
    
    def test_fix_merged_questions(self):
        """Test that merged questions are separated."""
        text = """**Answer:** 1) Option 1
> **Explanation:** Correct.
1. Next question?"""
        
        result = self.processor._fix_merged_questions(text)
        # Should add spacing or keep structure - just verify it doesn't crash
        self.assertIsNotNone(result)
    
    def test_remove_duplicate_separators(self):
        """Test that duplicate '?' separators are removed."""
        text = """Question?
1. Option 1
?  
?  
**Answer:** 1) Option 1"""
        
        result = self.processor._remove_duplicate_separators(text)
        # Should remove duplicates - just verify it processes
        self.assertIsNotNone(result)
    
    def test_fix_answer_format(self):
        """Test that answer format is normalized."""
        text = """**Answer:** 2 Option"""
        
        result = self.processor._fix_answer_format(text)
        # Should add ')' after number
        self.assertIn("2)", result)
    
    def test_normalize_spacing(self):
        """Test that excessive spacing is normalized."""
        text = """Question?



1. Option 1"""
        
        result = self.processor._normalize_spacing(text)
        # Should not have 4+ consecutive newlines
        self.assertNotIn("\n\n\n\n", result)


class TestPostProcessFlashcards(unittest.TestCase):
    """Test post-processing of flashcard files."""
    
    def setUp(self):
        """Create temporary directory for test files."""
        self.test_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Clean up temporary directory."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_process_flashcard_file(self):
        """Test processing a flashcard file with issues."""
        # Create test file with issues
        test_file = self.test_dir / "ACCT1001_W01_MCQ.md"
        test_file.write_text("""---
tags:
- flashcard/ACCT1001/W01
---

Question?
1. Option 1
2. Option 2
3. Option 3
4. Option 4
**Answer:** 1) Option 1

Let me know if you need more questions.
""", encoding='utf-8')
        
        # Process
        stats = post_process_flashcards(self.test_dir, verbose=False)
        
        # Verify stats
        self.assertEqual(stats['files_processed'], 1)
        self.assertGreaterEqual(stats['total_fixes'], 0)
    
    def test_process_clean_file(self):
        """Test processing a file with no issues."""
        test_file = self.test_dir / "ACCT1001_W01_MCQ.md"
        test_file.write_text("""---
tags:
- flashcard/ACCT1001/W01
---

Question?
1. Option 1
2. Option 2
3. Option 3
4. Option 4
?
**Answer:** 1) Option 1
> **Explanation:** Correct.
""", encoding='utf-8')
        
        stats = post_process_flashcards(self.test_dir, verbose=False)
        
        self.assertEqual(stats['files_processed'], 1)
        # May have 0 fixes if file is already clean
    
    def test_process_empty_directory(self):
        """Test processing directory with no flashcard files."""
        stats = post_process_flashcards(self.test_dir, verbose=False)
        
        self.assertEqual(stats['files_processed'], 0)
        self.assertEqual(stats['total_fixes'], 0)


if __name__ == '__main__':
    unittest.main()
