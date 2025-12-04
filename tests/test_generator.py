"""Integration tests for FlashcardGenerator.

These tests verify end-to-end flashcard generation with mocked
Ollama responses and file I/O.
"""

import unittest
from pathlib import Path
import sys
import tempfile
import shutil
import json
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcq_flashcards.core.generator import FlashcardGenerator
from mcq_flashcards.core.config import Config


class TestFlashcardGenerator(unittest.TestCase):
    """Test FlashcardGenerator integration."""
    
    def setUp(self):
        """Create test environment."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.class_root = self.test_dir / "class_root"
        self.output_dir = self.test_dir / "output"
        self.class_root.mkdir()
        self.output_dir.mkdir()
        
        # Create test subject directory
        self.subject_dir = self.class_root / "ACCT1001"
        self.subject_dir.mkdir()
        
        self.config = Config(dev_mode=True)
        self.generator = FlashcardGenerator(
            "ACCT1001",
            self.config,
            self.class_root,
            self.output_dir
        )
    
    def tearDown(self):
        """Clean up test environment."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_persona_selection_accounting(self):
        """Test that accounting subject gets correct persona."""
        persona, focus = self.generator._get_persona()
        self.assertEqual(persona, "Strict Accounting Professor")
        self.assertIn("IFRS/GAAP", focus)
    
    def test_persona_selection_default(self):
        """Test default persona for unknown subject."""
        gen = FlashcardGenerator("UNKNOWN", self.config, self.class_root, self.output_dir)
        persona, focus = gen._get_persona()
        self.assertEqual(persona, "University Professor")
    
    def test_bloom_instruction_apply(self):
        """Test Bloom's instruction for 'apply' level."""
        config = Config(bloom_level="apply")
        gen = FlashcardGenerator("ACCT1001", config, self.class_root, self.output_dir)
        instruction = gen._get_bloom_instruction()
        self.assertIn("APPLICATION", instruction)
        self.assertIn("practical scenarios", instruction)
    
    def test_bloom_instruction_none(self):
        """Test no Bloom's instruction when level is None."""
        instruction = self.generator._get_bloom_instruction()
        self.assertEqual(instruction, "")
    
    def test_difficulty_instruction_medium(self):
        """Test difficulty instruction for medium level."""
        config = Config(difficulty="medium")
        gen = FlashcardGenerator("ACCT1001", config, self.class_root, self.output_dir)
        instruction = gen._get_difficulty_instruction()
        self.assertIn("MEDIUM", instruction)
        self.assertIn("realistic scenarios", instruction)
    
    def test_cache_key_generation(self):
        """Test that cache keys are generated consistently."""
        text = "Test content"
        key1 = self.generator.get_cache_key(text)
        key2 = self.generator.get_cache_key(text)
        
        self.assertEqual(key1, key2, "Same text should generate same cache key")
        self.assertTrue(key1.name.startswith("ACCT1001_"))
        self.assertTrue(key1.name.endswith(".pkl"))
    
    def test_generate_single_with_cache(self):
        """Test that cached responses are reused."""
        mock_response = {
            "response": "Question?\n1. Opt1\n2. Opt2\n3. Opt3\n4. Opt4\n?\n**Answer:** 1) Opt1"
        }
        
        with patch.object(self.generator.client, 'generate', return_value=mock_response) as mock_generate:
            # First call
            result1 = self.generator.generate_single("Test text for caching", "test1")
            self.assertIsNotNone(result1)
            initial_call_count = mock_generate.call_count
            
            # Second call with same text - should use cache
            result2 = self.generator.generate_single("Test text for caching", "test2")
            self.assertIsNotNone(result2)
            
            # Client should not be called again (cache hit)
            self.assertEqual(mock_generate.call_count, initial_call_count,
                           "Client should not be called again when cache is hit")
    
    def test_extract_summary_from_lecture_note(self):
        """Test extracting summary from lecture note."""
        # Create test lecture note
        note_path = self.test_dir / "test_note.md"
        note_path.write_text("""---
tags:
- lecture/ACCT1001
---

## 📝 Notes

Content about [[Accounting]] and [[Finance]].

## 💡 Key Concepts & Summary

This lecture covered accounting fundamentals.
""", encoding='utf-8')
        
        summary, links = self.generator.extract_summary(note_path)
        
        self.assertIsNotNone(summary)
        self.assertIn("accounting fundamentals", summary)
        self.assertIn("Accounting", links)
        self.assertIn("Finance", links)
    
    def test_extract_summary_wikilink_cleaning(self):
        """Test that wikilinks are cleaned from summary."""
        note_path = self.test_dir / "test_note.md"
        note_path.write_text("""## Key Concepts

The [[Accounting Equation]] is fundamental.
""", encoding='utf-8')
        
        summary, links = self.generator.extract_summary(note_path)
        
        # Summary should have wikilinks removed
        self.assertNotIn("[[", summary)
        self.assertNotIn("]]", summary)
        self.assertIn("Accounting Equation", summary)
        
        # But links should be extracted
        self.assertIn("Accounting Equation", links)


if __name__ == '__main__':
    unittest.main()
