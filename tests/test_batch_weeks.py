"""Tests for batch week processing functionality."""

import sys
from pathlib import Path

# Add parent directory to path for cli import
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from cli import parse_week_argument


class TestParseWeekArgument:
    """Test the parse_week_argument function."""
    
    def test_single_week(self):
        """Test parsing a single week number."""
        assert parse_week_argument("1") == [1]
        assert parse_week_argument("5") == [5]
        assert parse_week_argument("12") == [12]
    
    def test_week_range(self):
        """Test parsing week ranges."""
        assert parse_week_argument("1-4") == [1, 2, 3, 4]
        assert parse_week_argument("5-8") == [5, 6, 7, 8]
        assert parse_week_argument("1-1") == [1]  # Single week as range
    
    def test_comma_separated(self):
        """Test parsing comma-separated weeks."""
        assert parse_week_argument("1,3,5") == [1, 3, 5]
        assert parse_week_argument("2,4,6,8") == [2, 4, 6, 8]
        assert parse_week_argument("10,5,1") == [1, 5, 10]  # Should be sorted
    
    def test_mixed_format(self):
        """Test parsing mixed ranges and lists."""
        assert parse_week_argument("1-3,5") == [1, 2, 3, 5]
        assert parse_week_argument("1,3-5,7") == [1, 3, 4, 5, 7]
        assert parse_week_argument("1-2,4-6,8") == [1, 2, 4, 5, 6, 8]
    
    def test_all_keyword(self):
        """Test ALL keyword."""
        assert parse_week_argument("ALL") is None
        assert parse_week_argument("all") is None
        assert parse_week_argument("All") is None
    
    def test_empty_or_none(self):
        """Test empty or None input."""
        assert parse_week_argument("") is None
        assert parse_week_argument(None) is None
    
    def test_whitespace_handling(self):
        """Test that whitespace is handled correctly."""
        assert parse_week_argument(" 1 ") == [1]
        assert parse_week_argument("1 - 4") == [1, 2, 3, 4]
        assert parse_week_argument("1 , 3 , 5") == [1, 3, 5]
        assert parse_week_argument(" 1-3 , 5 ") == [1, 2, 3, 5]
    
    def test_duplicate_removal(self):
        """Test that duplicates are removed."""
        assert parse_week_argument("1,1,1") == [1]
        assert parse_week_argument("1-3,2-4") == [1, 2, 3, 4]
        assert parse_week_argument("1,2,1-3") == [1, 2, 3]
    
    def test_invalid_range_start_greater_than_end(self, capsys):
        """Test invalid range where start > end."""
        result = parse_week_argument("5-1")
        assert result == []
        captured = capsys.readouterr()
        assert "Invalid range" in captured.out
        assert "start > end" in captured.out
    
    def test_invalid_week_number_too_low(self, capsys):
        """Test invalid week number (< 1)."""
        result = parse_week_argument("0")
        assert result == []
        captured = capsys.readouterr()
        assert "Invalid week" in captured.out
        assert "must be 1-52" in captured.out
    
    def test_invalid_week_number_too_high(self, capsys):
        """Test invalid week number (> 52)."""
        result = parse_week_argument("53")
        assert result == []
        captured = capsys.readouterr()
        assert "Invalid week" in captured.out
        assert "must be 1-52" in captured.out
    
    def test_invalid_range_too_low(self, capsys):
        """Test invalid range with week < 1."""
        result = parse_week_argument("0-3")
        assert result == []
        captured = capsys.readouterr()
        assert "Invalid range" in captured.out
        assert "must be 1-52" in captured.out
    
    def test_invalid_range_too_high(self, capsys):
        """Test invalid range with week > 52."""
        result = parse_week_argument("50-55")
        assert result == []
        captured = capsys.readouterr()
        assert "Invalid range" in captured.out
        assert "must be 1-52" in captured.out
    
    def test_invalid_format_non_numeric(self, capsys):
        """Test invalid format with non-numeric input."""
        result = parse_week_argument("abc")
        assert result == []
        captured = capsys.readouterr()
        assert "Invalid week format" in captured.out
        assert "Valid formats" in captured.out
    
    def test_invalid_format_mixed_invalid(self, capsys):
        """Test invalid format in mixed input."""
        result = parse_week_argument("1,abc,3")
        assert result == []
        captured = capsys.readouterr()
        assert "Invalid week format" in captured.out
