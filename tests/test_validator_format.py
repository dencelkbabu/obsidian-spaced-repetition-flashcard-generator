"""Pytest tests for validation methods."""
import pytest
from mcq_flashcards.processing.validator import MCQValidator


class TestFormatErrorValidation:
    """Test format error validation methods."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.validator = MCQValidator()
    
    def test_validate_no_generic_options_pass(self):
        """Test that real options pass validation."""
        text = """What is the capital of France?
1. London
2. Paris
3. Berlin
4. Madrid  
?  
**Answer:** 2) Paris
> **Explanation:** Paris is the capital."""
        
        assert self.validator.validate_no_generic_options(text) is True
    
    def test_validate_no_generic_options_fail(self):
        """Test that generic options fail validation."""
        text = """What is the capital of France?
1. Option 1
2. Option 2
3. Option 3
4. Option 4  
?  
**Answer:** 2) Option 2
> **Explanation:** Test."""
        
        assert self.validator.validate_no_generic_options(text) is False
    
    def test_validate_no_duplicate_options_pass(self):
        """Test that single option set passes validation."""
        text = """What is accounting?
1. Recording transactions
2. Financial reporting
3. Analyzing data
4. All of the above  
?  
**Answer:** 4) All of the above
> **Explanation:** Accounting includes all."""
        
        assert self.validator.validate_no_duplicate_options(text) is True
    
    def test_validate_no_duplicate_options_fail(self):
        """Test that duplicate options fail validation."""
        text = """What is accounting?
1. Recording transactions
2. Financial reporting
3. Analyzing data
4. All of the above  
?  
1. Option 1
2. Option 2
3. Option 3
4. Option 4  
?  
**Answer:** 4) All of the above
> **Explanation:** Test."""
        
        assert self.validator.validate_no_duplicate_options(text) is False
    
    def test_validate_answer_has_content_pass(self):
        """Test that real answer text passes validation."""
        text = """What is the capital of France?
1. London
2. Paris
3. Berlin
4. Madrid  
?  
**Answer:** 2) Paris
> **Explanation:** Paris is the capital."""
        
        assert self.validator.validate_answer_has_content(text) is True
    
    def test_validate_answer_has_content_fail(self):
        """Test that generic answer fails validation."""
        text = """What is the capital of France?
1. London
2. Paris
3. Berlin
4. Madrid  
?  
**Answer:** 2) Option 2
> **Explanation:** Test."""
        
        assert self.validator.validate_answer_has_content(text) is False
    
    def test_all_validations_pass(self):
        """Test that clean MCQ passes all validations."""
        text = """What is the capital of France?
1. London
2. Paris
3. Berlin
4. Madrid  
?  
**Answer:** 2) Paris
> **Explanation:** Paris is the capital and largest city of France."""
        
        assert self.validator.validate_no_generic_options(text) is True
        assert self.validator.validate_no_duplicate_options(text) is True
        assert self.validator.validate_answer_has_content(text) is True
