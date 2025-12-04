"""Unit tests for MCQ validation.

These tests verify that the MCQValidator correctly identifies
valid and invalid MCQ formats.
"""

import unittest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcq_flashcards.processing.validator import MCQValidator


class TestMCQValidator(unittest.TestCase):
    """Test MCQ validation logic."""
    
    def setUp(self):
        """Create a validator instance for testing."""
        self.validator = MCQValidator()
    
    def test_valid_mcq_format(self):
        """Test that validator accepts properly formatted MCQs."""
        valid_mcq = """
What is the capital of France?
1. London
2. Paris
3. Berlin
4. Madrid
?
**Answer:** 2) Paris
> **Explanation:** Paris is the capital and largest city of France.
"""
        self.assertTrue(self.validator.validate(valid_mcq),
                       "Valid MCQ should pass validation")
    
    def test_missing_question_mark(self):
        """Test that validator rejects MCQs without question marks."""
        invalid_mcq = """
What is the capital of France
1. London
2. Paris
3. Berlin
4. Madrid
**Answer:** 2) Paris
"""
        self.assertFalse(self.validator.validate(invalid_mcq),
                        "MCQ without question mark should fail validation")
    
    def test_missing_options(self):
        """Test that validator rejects MCQs without numbered options."""
        invalid_mcq = """
What is the capital of France?
**Answer:** Paris
"""
        self.assertFalse(self.validator.validate(invalid_mcq),
                        "MCQ without options should fail validation")
    
    def test_missing_answer(self):
        """Test that validator rejects MCQs without answer line."""
        invalid_mcq = """
What is the capital of France?
1. London
2. Paris
3. Berlin
4. Madrid
"""
        self.assertFalse(self.validator.validate(invalid_mcq),
                        "MCQ without answer should fail validation")
    
    def test_empty_text(self):
        """Test that validator rejects empty or None text."""
        self.assertFalse(self.validator.validate(""),
                        "Empty string should fail validation")
        self.assertFalse(self.validator.validate(None),
                        "None should fail validation")
    
    def test_error_text(self):
        """Test that validator rejects error messages."""
        error_text = "Error: Failed to generate MCQ"
        self.assertFalse(self.validator.validate(error_text),
                        "Error messages should fail validation")
    
    def test_alternative_numbering_format(self):
        """Test that validator accepts alternative numbering (1), 2), etc.)."""
        valid_mcq = """
What is 2 + 2?
1) Two
2) Three
3) Four
4) Five
?
**Answer:** 3) Four
> **Explanation:** 2 + 2 equals 4.
"""
        self.assertTrue(self.validator.validate(valid_mcq),
                       "Alternative numbering format should be valid")
    
    def test_multiple_questions(self):
        """Test that validator accepts multiple questions in one text."""
        valid_mcqs = """
What is the capital of France?
1. London
2. Paris
3. Berlin
4. Madrid
?
**Answer:** 2) Paris
> **Explanation:** Paris is the capital of France.

What is 2 + 2?
1. Three
2. Four
3. Five
4. Six
?
**Answer:** 2) Four
> **Explanation:** 2 + 2 equals 4.
"""
        self.assertTrue(self.validator.validate(valid_mcqs),
                       "Multiple valid MCQs should pass validation")
    
    def test_missing_option_3(self):
        """Test that validator rejects MCQ with only 3 options."""
        invalid_mcq = """
What is the capital of France?
1. London
2. Paris
3. Berlin
?
**Answer:** 2) Paris
> **Explanation:** Paris is the capital.
"""
        self.assertFalse(self.validator.validate(invalid_mcq),
                        "MCQ with only 3 options should fail validation")
    
    def test_missing_option_4(self):
        """Test that validator rejects MCQ with only 2 options."""
        invalid_mcq = """
What is the capital of France?
1. London
2. Paris
?
**Answer:** 2) Paris
> **Explanation:** Paris is the capital.
"""
        self.assertFalse(self.validator.validate(invalid_mcq),
                        "MCQ with only 2 options should fail validation")
    
    def test_invalid_answer_number_0(self):
        """Test that validator rejects answer number 0."""
        invalid_mcq = """
What is the capital of France?
1. London
2. Paris
3. Berlin
4. Madrid
?
**Answer:** 0) None
> **Explanation:** Invalid answer.
"""
        self.assertFalse(self.validator.validate(invalid_mcq),
                        "Answer number 0 should fail validation")
    
    def test_invalid_answer_number_5(self):
        """Test that validator rejects answer number 5."""
        invalid_mcq = """
What is the capital of France?
1. London
2. Paris
3. Berlin
4. Madrid
?
**Answer:** 5) Other
> **Explanation:** Invalid answer.
"""
        self.assertFalse(self.validator.validate(invalid_mcq),
                        "Answer number 5 should fail validation")
    
    def test_missing_explanation(self):
        """Test that validator rejects MCQ without explanation."""
        invalid_mcq = """
What is the capital of France?
1. London
2. Paris
3. Berlin
4. Madrid
?
**Answer:** 2) Paris
"""
        self.assertFalse(self.validator.validate(invalid_mcq),
                        "MCQ without explanation should fail validation")
    
    def test_all_four_options_required(self):
        """Test that all 4 options must be present."""
        # Valid with all 4
        valid_mcq = """
Question?
1. Opt1
2. Opt2
3. Opt3
4. Opt4
?
**Answer:** 1) Opt1
> **Explanation:** Correct.
"""
        self.assertTrue(self.validator.validate(valid_mcq),
                       "MCQ with all 4 options should pass")


if __name__ == '__main__':
    unittest.main()
