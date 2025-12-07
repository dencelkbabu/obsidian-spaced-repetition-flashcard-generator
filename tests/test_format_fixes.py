"""Pytest tests for format error fixes."""
import pytest
from mcq_flashcards.processing.cleaner import MCQCleaner


class TestDuplicateOptionRemoval:
    """Test duplicate option removal functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.cleaner = MCQCleaner()
    
    def test_remove_duplicate_options_basic(self):
        """Test basic duplicate option removal."""
        input_text = """What is accounting?
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
> **Explanation:** Accounting includes all these activities."""
        
        result = self.cleaner.clean_ai_output(input_text)
        
        # Verify duplicates removed
        assert "Option 1" not in result
        assert "Option 2" not in result
        assert "Option 3" not in result
        assert "Option 4" not in result
        
        # Verify original options preserved
        assert "Recording transactions" in result
        assert "Financial reporting" in result
        assert "All of the above" in result
    
    def test_remove_question_marks_from_options(self):
        """Test question mark removal from option text."""
        input_text = """What is a fictitious asset?
1. Tangible asset
2. Intangible asset
3. Preliminary expenses?  
4. Fixed asset  
?  
**Answer:** 3) Preliminary expenses
> **Explanation:** Preliminary expenses are fictitious assets."""
        
        result = self.cleaner.clean_ai_output(input_text)
        
        # Verify question mark removed
        assert "expenses?  " not in result
        assert "Preliminary expenses" in result
    
    def test_combined_fixes(self):
        """Test both duplicate removal and question mark removal."""
        input_text = """What is the accounting equation?
1. Assets = Liabilities + Equity
2. Revenue - Expenses = Profit?  
3. Debit = Credit
4. None of the above  
?  
1. Option 1
2. Option 2
3. Option 3
4. Option 4  
?  
**Answer:** 1) Assets = Liabilities + Equity
> **Explanation:** This is the fundamental accounting equation."""
        
        result = self.cleaner.clean_ai_output(input_text)
        
        # Verify duplicates removed
        assert "Option 1" not in result
        
        # Verify question mark removed
        assert "Profit?  " not in result
        assert "Profit" in result
        
        # Verify original content preserved
        assert "Assets = Liabilities + Equity" in result
    
    def test_no_duplicates_unchanged(self):
        """Test that clean MCQs are not modified."""
        input_text = """What is the capital of France?
1. London
2. Paris
3. Berlin
4. Madrid  
?  
**Answer:** 2) Paris
> **Explanation:** Paris is the capital and largest city of France."""
        
        result = self.cleaner.clean_ai_output(input_text)
        
        # Verify all options preserved
        assert "London" in result
        assert "Paris" in result
        assert "Berlin" in result
        assert "Madrid" in result
