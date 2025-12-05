"""Unit tests for prompt templates."""
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from mcq_flashcards.core.prompts import (
    SYSTEM_PROMPT_TEMPLATE, GENERATION_PROMPT_TEMPLATE, REFINE_PROMPT_TEMPLATE,
    BLOOM_INSTRUCTIONS, DIFFICULTY_INSTRUCTIONS, PERSONAS
)

class TestPromptTemplates(unittest.TestCase):
    def test_system_prompt_has_placeholders(self):
        self.assertIn("{persona}", SYSTEM_PROMPT_TEMPLATE)
        self.assertIn("{focus}", SYSTEM_PROMPT_TEMPLATE)
    
    def test_generation_prompt_has_placeholders(self):
        self.assertIn("{context}", GENERATION_PROMPT_TEMPLATE)
        self.assertIn("{num_questions}", GENERATION_PROMPT_TEMPLATE)
    
    def test_refine_prompt_has_placeholder(self):
        self.assertIn("{content}", REFINE_PROMPT_TEMPLATE)

class TestBloomInstructions(unittest.TestCase):
    def test_all_bloom_levels_exist(self):
        levels = ["remember", "understand", "apply", "analyze", "evaluate", "create"]
        for level in levels:
            self.assertIn(level, BLOOM_INSTRUCTIONS)
            self.assertGreater(len(BLOOM_INSTRUCTIONS[level]), 0)

class TestDifficultyInstructions(unittest.TestCase):
    def test_all_difficulty_levels_exist(self):
        levels = ["easy", "medium", "hard"]
        for level in levels:
            self.assertIn(level, DIFFICULTY_INSTRUCTIONS)
            self.assertGreater(len(DIFFICULTY_INSTRUCTIONS[level]), 0)

class TestPersonas(unittest.TestCase):
    def test_default_persona_exists(self):
        self.assertIn("DEFAULT", PERSONAS)
    
    def test_accounting_persona_exists(self):
        self.assertIn("ACCT", PERSONAS)
    
    def test_communication_persona_exists(self):
        self.assertIn("COMM", PERSONAS)

if __name__ == '__main__':
    unittest.main()
