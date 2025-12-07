"""MCQ validation utilities.

This module provides the MCQValidator class for validating
MCQ format and structure.
"""

import re
from typing import Optional


class MCQValidator:
    """Validates MCQ format and structure with strict checks."""
    
    def validate(self, text: str) -> bool:
        """Validate that text contains a properly formatted MCQ.
        
        Performs strict validation including:
        - Question mark present
        - Exactly 4 options (numbered 1-4)
        - Valid answer number (1-4)
        - Explanation present
        
        Args:
            text: MCQ text to validate
            
        Returns:
            True if text is a valid MCQ, False otherwise
        """
        if not text or text.startswith("Error:"):
            return False
        
        # Check for question mark
        if '?' not in text:
            return False
        
        # Check for exactly 4 options
        option_count = self._count_options(text)
        if option_count != 4:
            return False
        
        # Check for valid answer number
        answer_num = self._extract_answer_number(text)
        if answer_num is None or answer_num not in range(1, 5):
            return False
        
        # Check for explanation
        if "**Explanation:**" not in text:
            return False
        
        return True
    
    def _count_options(self, text: str) -> int:
        """Count numbered options in the text.
        
        Supports both formats: '1.' and '1)'
        
        Args:
            text: MCQ text to analyze
            
        Returns:
            Number of distinct options found (1-4)
        """
        options_found = set()
        
        # Match patterns like "1." or "1)" at start of line
        pattern = r'^\s*([1-4])[\.\)]'
        
        for line in text.split('\n'):
            match = re.match(pattern, line)
            if match:
                options_found.add(int(match.group(1)))
        
        return len(options_found)
    
    def _extract_answer_number(self, text: str) -> Optional[int]:
        """Extract answer number from the Answer line.
        
        Looks for patterns like:
        - **Answer:** 2) Text
        - **Answer:** 2. Text
        
        Args:
            text: MCQ text containing answer
            
        Returns:
            Answer number (1-4) or None if not found/invalid
        """
        # Match "**Answer:** N)" or "**Answer:** N."
        pattern = r'\*\*Answer:\*\*\s*(\d+)[\)\.]'
        
        match = re.search(pattern, text)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                return None
        
        return None
    
    def validate_no_generic_options(self, text: str) -> bool:
        """Check for generic 'Option N' placeholders in options.
        
        Args:
            text: MCQ text to validate
            
        Returns:
            True if no generic placeholders found, False otherwise
        """
        # Check for lines like "1. Option 1" or "2. Option 2"
        if re.search(r'^\d+\.\s+Option \d+\s*$', text, re.MULTILINE):
            return False
        return True
    
    def validate_no_duplicate_options(self, text: str) -> bool:
        """Check for duplicate option sets.
        
        Detects when options are listed twice in the same MCQ.
        
        Args:
            text: MCQ text to validate
            
        Returns:
            True if no duplicates found, False otherwise
        """
        lines = text.split('\n')
        option_count = 0
        
        for line in lines:
            if re.match(r'^\d+\.\s+', line):
                option_count += 1
                # If we see more than 4 options, we have duplicates
                if option_count > 4:
                    return False
            elif '**Answer:**' in line:
                # Reset for next question
                option_count = 0
        
        return True
    
    def validate_answer_has_content(self, text: str) -> bool:
        """Check that answer includes actual text, not 'Option N'.
        
        Args:
            text: MCQ text to validate
            
        Returns:
            True if answer has real content, False if generic
        """
        answer_match = re.search(r'\*\*Answer:\*\*\s*\d+\)\s+(.+)$', text, re.MULTILINE)
        if answer_match:
            answer_text = answer_match.group(1).strip()
            # Check if answer is just "Option N"
            if re.match(r'^Option \d+$', answer_text):
                return False
        return True
