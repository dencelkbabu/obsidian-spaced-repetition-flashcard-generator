"""Content validation for MCQ correctness - all subjects.

This module provides subject-specific validators that check for common
errors in generated MCQ content, including calculation verification.
"""

import re
from typing import List, Optional
from abc import ABC, abstractmethod


class SubjectValidator(ABC):
    """Base class for subject-specific validation."""
    
    @abstractmethod
    def get_error_patterns(self) -> List[tuple]:
        """Return list of (regex_pattern, error_message) tuples."""
        pass
    
    def validate(self, text: str) -> List[str]:
        """Validate MCQ text and return list of errors found."""
        errors = []
        for pattern, message in self.get_error_patterns():
            if re.search(pattern, text, re.IGNORECASE):
                errors.append(message)
        
        # Check calculations for all subjects
        calc_error = self._check_calculations(text)
        if calc_error:
            errors.append(calc_error)
        
        return errors
    
    def _check_calculations(self, text: str) -> Optional[str]:
        """Verify ALL arithmetic in text."""
        # Define operators and their functions
        ops = [
            (r'(\d+)\s*\+\s*(\d+)\s*=\s*(\d+)', '+', lambda a, b: a + b),
            (r'(\d+)\s*-\s*(\d+)\s*=\s*(\d+)', '-', lambda a, b: a - b),
            (r'(\d+)\s*[×x*]\s*(\d+)\s*=\s*(\d+)', '×', lambda a, b: a * b),
            (r'(\d+)\s*/\s*(\d+)\s*=\s*(\d+)', '/', lambda a, b: a // b if b != 0 else 0),
        ]
        
        for pattern, op_symbol, op_func in ops:
            for match in re.finditer(pattern, text):
                try:
                    a = int(match.group(1))
                    b = int(match.group(2))
                    c = int(match.group(3))
                    expected = op_func(a, b)
                    if expected != c:
                        return f"CALC ERROR: {a} {op_symbol} {b} = {expected}, not {c}"
                except (ValueError, ZeroDivisionError):
                    continue
        
        return None


class ACCTValidator(SubjectValidator):
    """Accounting-specific validation rules."""
    
    def get_error_patterns(self):
        return [
            (r"credit.*purchase.*Debit.*Cash", "Credit purchase → Cr. Creditors, not Cash"),
            (r"Debit Cash.*Credit Purchases", "Purchases are debited, not Cash"),
            (r"supplier.*Nominal\s*Account", "Suppliers are Personal Accounts"),
            (r"company.*Nominal\s*Account", "Companies are Personal Accounts"),
            (r"Debit Sundry Creditors.*Credit Purchases", "Reversed entry: should be Dr. Purchases, Cr. Creditors"),
            (r"Debit Rent.*Credit Expense", "Rent is an expense, debited not credited"),
        ]


class MATHValidator(SubjectValidator):
    """Mathematics-specific validation rules."""
    
    def get_error_patterns(self):
        return [
            (r"ratio.*(\d+):(\d+).*means.*\2.*to.*\1", "Ratio explanation reversed"),
            (r"percentage.*=.*\d+\s*/\s*100", "Percentage formula: (Part/Whole) × 100"),
        ]


class ECONValidator(SubjectValidator):
    """Economics-specific validation rules."""
    
    def get_error_patterns(self):
        return [
            (r"demand.*increase.*shift.*left", "Demand↑ shifts curve RIGHT, not left"),
            (r"supply.*decrease.*shift.*right", "Supply↓ shifts curve LEFT, not right"),
            (r"movement.*shift", "Movement along curve ≠ Shift of curve"),
        ]


class COMMValidator(SubjectValidator):
    """Communication-specific validation rules."""
    
    def get_error_patterns(self):
        return [
            (r"8\s*C'?s?\s*of\s*Communication", "There are 7 C's of Communication, not 8"),
            (r"6\s*C'?s?\s*of\s*Communication", "There are 7 C's of Communication, not 6"),
        ]


class INFSValidator(SubjectValidator):
    """Information Systems-specific validation rules."""
    
    def get_error_patterns(self):
        return [
            # Use word boundary and limit context to catch only direct associations
            (r"Ctrl\+C\s+(?:is\s+)?(?:used\s+)?(?:for\s+|to\s+)?paste", "Ctrl+C = Copy, not Paste"),
            (r"Ctrl\+V\s+(?:is\s+)?(?:used\s+)?(?:for\s+|to\s+)?copy", "Ctrl+V = Paste, not Copy"),
            (r"Ctrl\+X\s+(?:is\s+)?(?:used\s+)?(?:for\s+|to\s+)?copy", "Ctrl+X = Cut, not Copy"),
            (r"Ctrl\+Z\s+(?:is\s+)?(?:used\s+)?(?:for\s+|to\s+)?redo", "Ctrl+Z = Undo, not Redo"),
        ]


class MGMTValidator(SubjectValidator):
    """Management-specific validation rules."""
    
    def get_error_patterns(self):
        return [
            # Use word boundaries and limit context
            (r"Taylor\s+(?:proposed|developed|created|formulated|gave|introduced)\s+(?:the\s+)?14\s*Principles", "14 Principles = Fayol, not Taylor"),
            (r"Fayol\s+(?:proposed|developed|created|formulated|gave|introduced)\s+(?:the\s+)?Scientific\s*Management", "Scientific Management = Taylor, not Fayol"),
            (r"Mintzberg\s+(?:proposed|developed|created|formulated|gave|introduced)\s+(?:the\s+)?14\s*Principles", "14 Principles = Fayol, not Mintzberg"),
        ]


# Validator registry
VALIDATORS = {
    "ACCT": ACCTValidator(),
    "MATH": MATHValidator(),
    "ECON": ECONValidator(),
    "COMM": COMMValidator(),
    "INFS": INFSValidator(),
    "MGMT": MGMTValidator(),
}


def get_validator(subject: str) -> Optional[SubjectValidator]:
    """Get appropriate validator for a subject.
    
    Args:
        subject: Subject code (e.g., 'ACCT1001')
        
    Returns:
        SubjectValidator instance or None if no specific validator exists
    """
    subject_upper = subject.upper()
    for key, validator in VALIDATORS.items():
        if key in subject_upper:
            return validator
    return None
