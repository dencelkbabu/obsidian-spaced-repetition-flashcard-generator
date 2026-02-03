"""Unit tests for content validation."""

import unittest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcq_flashcards.processing.content_validator import (
    get_validator,
    ACCTValidator,
    MATHValidator,
    ECONValidator,
    COMMValidator,
    INFSValidator,
    MGMTValidator,
)


class TestGetValidator(unittest.TestCase):
    """Test validator factory function."""
    
    def test_get_acct_validator(self):
        validator = get_validator("ACCT1001")
        self.assertIsInstance(validator, ACCTValidator)
    
    def test_get_math_validator(self):
        validator = get_validator("MATH1001")
        self.assertIsInstance(validator, MATHValidator)
    
    def test_get_econ_validator(self):
        validator = get_validator("ECON1001")
        self.assertIsInstance(validator, ECONValidator)
    
    def test_get_comm_validator(self):
        validator = get_validator("COMM1001")
        self.assertIsInstance(validator, COMMValidator)
    
    def test_get_infs_validator(self):
        validator = get_validator("INFS1001")
        self.assertIsInstance(validator, INFSValidator)
    
    def test_get_mgmt_validator(self):
        validator = get_validator("MGMT1001")
        self.assertIsInstance(validator, MGMTValidator)
    
    def test_unknown_subject_returns_none(self):
        validator = get_validator("UNKNOWN999")
        self.assertIsNone(validator)


class TestACCTValidator(unittest.TestCase):
    """Test accounting-specific validation."""
    
    def setUp(self):
        self.validator = ACCTValidator()
    
    def test_detects_credit_purchase_cash_error(self):
        text = "For credit purchases, Debit Purchases and Credit Cash"
        errors = self.validator.validate(text)
        self.assertTrue(any("Creditors" in e for e in errors))
    
    def test_detects_reversed_journal_entry(self):
        text = "Debit Sundry Creditors and Credit Purchases"
        errors = self.validator.validate(text)
        self.assertTrue(any("Reversed" in e for e in errors))
    
    def test_detects_supplier_nominal_error(self):
        text = "The supplier account is a Nominal Account"
        errors = self.validator.validate(text)
        self.assertTrue(any("Personal" in e for e in errors))
    
    def test_passes_correct_journal_entry(self):
        text = "Debit Purchases and Credit Sundry Creditors for credit purchase"
        errors = self.validator.validate(text)
        self.assertEqual(len(errors), 0)


class TestMATHValidator(unittest.TestCase):
    """Test mathematics-specific validation."""
    
    def setUp(self):
        self.validator = MATHValidator()
    
    def test_detects_calculation_error_addition(self):
        text = "The answer is 5 + 3 = 9"
        errors = self.validator.validate(text)
        self.assertTrue(any("CALC ERROR" in e for e in errors))
    
    def test_detects_calculation_error_subtraction(self):
        text = "We compute 100 - 40 = 50"
        errors = self.validator.validate(text)
        self.assertTrue(any("CALC ERROR" in e for e in errors))
    
    def test_passes_correct_calculation(self):
        text = "The result is 5 + 3 = 8"
        errors = self.validator.validate(text)
        self.assertEqual(len(errors), 0)


class TestECONValidator(unittest.TestCase):
    """Test economics-specific validation."""
    
    def setUp(self):
        self.validator = ECONValidator()
    
    def test_detects_demand_shift_error(self):
        text = "When demand increases, the curve shifts left"
        errors = self.validator.validate(text)
        self.assertTrue(any("RIGHT" in e for e in errors))
    
    def test_detects_supply_shift_error(self):
        text = "When supply decreases, the curve shifts right"
        errors = self.validator.validate(text)
        self.assertTrue(any("LEFT" in e for e in errors))
    
    def test_passes_correct_demand_shift(self):
        text = "When demand increases, the curve shifts right"
        errors = self.validator.validate(text)
        self.assertEqual(len(errors), 0)


class TestINFSValidator(unittest.TestCase):
    """Test information systems-specific validation."""
    
    def setUp(self):
        self.validator = INFSValidator()
    
    def test_detects_ctrl_c_paste_error(self):
        text = "Ctrl+C is used to paste content"
        errors = self.validator.validate(text)
        self.assertTrue(any("Copy" in e for e in errors))
    
    def test_detects_ctrl_v_copy_error(self):
        text = "Ctrl+V is for copy operations"
        errors = self.validator.validate(text)
        self.assertTrue(any("Paste" in e for e in errors))
    
    def test_passes_correct_shortcuts(self):
        # Correct usage: Ctrl+C for copy, Ctrl+V for paste
        text = "Use Ctrl+C to copy text. Then Ctrl+V to paste it."
        errors = self.validator.validate(text)
        self.assertEqual(len(errors), 0)


class TestMGMTValidator(unittest.TestCase):
    """Test management-specific validation."""
    
    def setUp(self):
        self.validator = MGMTValidator()
    
    def test_detects_taylor_14_principles_error(self):
        text = "Taylor proposed 14 Principles of Management"
        errors = self.validator.validate(text)
        self.assertTrue(any("Fayol" in e for e in errors))
    
    def test_detects_fayol_scientific_management_error(self):
        text = "Fayol developed Scientific Management theory"
        errors = self.validator.validate(text)
        self.assertTrue(any("Taylor" in e for e in errors))
    
    def test_passes_correct_attribution(self):
        # Properly attributed: Fayol for 14 Principles, Taylor for Scientific Management
        text = "Fayol proposed 14 Principles. Taylor developed Scientific Management."
        errors = self.validator.validate(text)
        self.assertEqual(len(errors), 0)


class TestCalculationVerification(unittest.TestCase):
    """Test universal calculation verification."""
    
    def setUp(self):
        self.validator = MATHValidator()  # Any validator will work
    
    def test_detects_multiplication_error(self):
        text = "The product is 5 x 4 = 25"
        errors = self.validator.validate(text)
        self.assertTrue(any("CALC ERROR" in e for e in errors))
    
    def test_passes_correct_multiplication(self):
        text = "The product is 5 * 4 = 20"
        errors = self.validator.validate(text)
        self.assertEqual(len(errors), 0)
    
    def test_passes_division(self):
        text = "The result is 20 / 4 = 5"
        errors = self.validator.validate(text)
        self.assertEqual(len(errors), 0)


if __name__ == '__main__':
    unittest.main()
