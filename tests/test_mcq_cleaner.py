"""Unit tests for MCQ cleaning functionality.

These tests verify that the MCQCleaner correctly cleans and formats
AI-generated MCQ output.
"""

import unittest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcq_flashcards.processing.cleaner import MCQCleaner


class TestMCQCleaner(unittest.TestCase):
    """Test MCQ cleaning logic."""
    
    def setUp(self):
        """Create a cleaner instance for testing."""
        self.cleaner = MCQCleaner()
    
    def test_clean_wikilinks_simple(self):
        """Test that simple wikilinks are removed."""
        text = "This is about [[Accounting]] and [[Finance]]."
        expected = "This is about Accounting and Finance."
        result = self.cleaner.clean_wikilinks(text)
        self.assertEqual(result, expected,
                        "Simple wikilinks should be converted to plain text")
    
    def test_clean_wikilinks_with_alias(self):
        """Test that wikilinks with aliases show only the alias."""
        text = "See [[Accounting Standards|IFRS]] for details."
        expected = "See IFRS for details."
        result = self.cleaner.clean_wikilinks(text)
        self.assertEqual(result, expected,
                        "Wikilinks with aliases should show only alias text")
    
    def test_clean_wikilinks_empty_input(self):
        """Test that empty input is handled gracefully."""
        self.assertEqual(self.cleaner.clean_wikilinks(""), "")
        self.assertEqual(self.cleaner.clean_wikilinks(None), "")
    
    def test_remove_meta_commentary(self):
        """Test that LLM meta-commentary is removed."""
        text = """According to the text, what is accounting?
1. Option 1
2. Option 2
3. Option 3
4. Option 4
?
**Answer:** 2) Option 2"""
        
        result = self.cleaner.clean_ai_output(text)
        self.assertNotIn("According to the text,", result,
                        "Meta-commentary should be removed")
        self.assertIn("what is accounting?", result,
                     "Question content should remain")
    
    def test_normalize_option_numbering(self):
        """Test that option numbering is normalized to '1.' format."""
        text = """Question?
1) Option 1
2) Option 2
3) Option 3
4) Option 4
?
**Answer:** 2) Option 2"""
        
        result = self.cleaner.clean_ai_output(text)
        self.assertIn("1. Option 1", result,
                     "Options should use '1.' format")
        self.assertIn("2. Option 2", result,
                     "Options should use '2.' format")
    
    def test_ensure_question_separator(self):
        """Test that '?' separator is added before Answer if missing."""
        text = """Question?
1. Option 1
2. Option 2
3. Option 3
4. Option 4
**Answer:** 2) Option 2"""
        
        result = self.cleaner.clean_ai_output(text)
        # Should have a '?' line before **Answer:** (may have trailing spaces)
        self.assertIn("?", result, "Should have '?' separator")
        self.assertIn("**Answer:**", result, "Should have Answer line")
        # Verify the '?' comes before the Answer
        q_pos = result.find("?")
        ans_pos = result.find("**Answer:**")
        self.assertLess(q_pos, ans_pos, "'?' should come before **Answer:**")
    
    def test_remove_verification_text(self):
        """Test that verification text is removed."""
        text = """**Verification:** This is correct.
Question?
1. Option 1
2. Option 2
3. Option 3
4. Option 4
?
**Answer:** 1) Option 1"""
        
        result = self.cleaner.clean_ai_output(text)
        self.assertNotIn("Verification:", result,
                        "Verification text should be removed")
    
    def test_remove_here_are_questions(self):
        """Test that 'Here are' introductions are removed."""
        text = """Here are 2 questions based on the text:

Question?
1. Option 1
2. Option 2
3. Option 3
4. Option 4
?
**Answer:** 1) Option 1"""
        
        result = self.cleaner.clean_ai_output(text)
        self.assertNotIn("Here are", result,
                        "'Here are' text should be removed")
    
    def test_compact_whitespace(self):
        """Test that excessive whitespace is compacted."""
        text = """Question?


1. Option 1


2. Option 2
3. Option 3
4. Option 4


?


**Answer:** 1) Option 1"""
        
        result = self.cleaner.clean_ai_output(text)
        # Should not have 3+ consecutive newlines
        self.assertNotIn("\n\n\n", result,
                        "Should not have triple newlines")
    
    def test_answer_format_normalization(self):
        """Test that answer format is normalized."""
        text = """Question?
1. Option 1
2. Option 2
3. Option 3
4. Option 4
?
**Answer:** 2. Option 2"""
        
        result = self.cleaner.clean_ai_output(text)
        # Answer should use ') ' format
        self.assertIn("**Answer:** 2) ", result,
                     "Answer should use ') ' format")
    
    def test_explanation_blockquote(self):
        """Test that explanations are formatted as blockquotes."""
        text = """Question?
1. Option 1
2. Option 2
3. Option 3
4. Option 4
?
**Answer:** 1) Option 1
**Explanation:** This is correct because..."""
        
        result = self.cleaner.clean_ai_output(text)
        self.assertIn("> **Explanation:**", result,
                     "Explanation should be a blockquote")
    
    def test_multiple_questions_cleaning(self):
        """Test cleaning multiple questions in one text."""
        text = """According to the text, Question 1?
1) Opt1
2) Opt2
3) Opt3
4) Opt4
**Answer:** 1) Opt1

Based on the provided summary, Question 2?
1) Opt1
2) Opt2
3) Opt3
4) Opt4
**Answer:** 2) Opt2"""
        
        result = self.cleaner.clean_ai_output(text)
        self.assertNotIn("According to the text,", result)
        self.assertNotIn("Based on the provided summary,", result)
        self.assertIn("1. Opt1", result,
                     "Should normalize numbering")


if __name__ == '__main__':
    unittest.main()
