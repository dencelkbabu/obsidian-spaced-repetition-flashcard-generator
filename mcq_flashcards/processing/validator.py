"""MCQ validation utilities.

This module provides the MCQValidator class for validating
MCQ format and structure.
"""


class MCQValidator:
    """Validates MCQ format and structure."""
    
    def validate(self, text: str) -> bool:
        """Validate that text contains a properly formatted MCQ.
        
        Checks for:
        - Question mark (indicates question)
        - Options (numbered 1., 2., etc.)
        - Answer line
        
        Args:
            text: MCQ text to validate
            
        Returns:
            True if text appears to be a valid MCQ, False otherwise
        """
        if not text or text.startswith("Error:"):
            return False
        has_question = '?' in text
        has_options = any(opt in text for opt in ['1.', '2.', '1)', '2)'])
        has_answer = "**Answer:**" in text
        return has_question and has_options and has_answer
