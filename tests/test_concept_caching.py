"""Unit tests for concept file name caching."""
import unittest
from pathlib import Path
import sys
import tempfile
import shutil
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).parent.parent))
from mcq_flashcards.core.generator import FlashcardGenerator
from mcq_flashcards.core.config import Config

class TestConceptCaching(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.class_root = self.test_dir / "class_root"
        self.output_dir = self.test_dir / "output"
        self.class_root.mkdir()
        self.output_dir.mkdir()
        self.test_concepts_dir = self.test_dir / "concepts"
        self.test_concepts_dir.mkdir()
        self.config = Config(dev_mode=True)
    
    def tearDown(self):
        shutil.rmtree(self.test_dir)
    
    def test_concept_cache_initialization(self):
        (self.test_concepts_dir / "Accounting.md").touch()
        (self.test_concepts_dir / "Finance.md").touch()
        with patch('mcq_flashcards.core.generator.CONCEPT_SOURCE', self.test_concepts_dir):
            generator = FlashcardGenerator("TEST101", self.config, self.class_root, self.output_dir)
            self.assertIsInstance(generator.concept_cache, set)
            self.assertEqual(len(generator.concept_cache), 2)
            self.assertIn("Accounting", generator.concept_cache)
            self.assertIn("Finance", generator.concept_cache)
    
    def test_concept_cache_empty_directory(self):
        with patch('mcq_flashcards.core.generator.CONCEPT_SOURCE', self.test_concepts_dir):
            generator = FlashcardGenerator("TEST101", self.config, self.class_root, self.output_dir)
            self.assertIsInstance(generator.concept_cache, set)
            self.assertEqual(len(generator.concept_cache), 0)

if __name__ == '__main__':
    unittest.main()
