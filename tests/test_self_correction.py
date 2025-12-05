"""Unit tests for self-correction stats."""
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from mcq_flashcards.core.config import ProcessingStats

class TestSelfCorrectionStats(unittest.TestCase):
    def test_stats_initialization(self):
        stats = ProcessingStats()
        self.assertEqual(stats.refine_attempts, 0)
        self.assertEqual(stats.refine_success, 0)
    
    def test_refine_attempt_tracking(self):
        stats = ProcessingStats()
        stats.refine_attempts += 1
        self.assertEqual(stats.refine_attempts, 1)
    
    def test_refine_success_tracking(self):
        stats = ProcessingStats()
        stats.refine_attempts += 1
        stats.refine_success += 1
        self.assertEqual(stats.refine_success, 1)

if __name__ == '__main__':
    unittest.main()
