"""Tests for performance metrics in ProcessingStats."""

import time
import pytest
from mcq_flashcards.core.config import ProcessingStats

def test_processing_stats_initialization():
    """Test that new metrics are initialized correctly."""
    stats = ProcessingStats()
    # These fields will be added
    assert not hasattr(stats, 'start_time') or stats.start_time == 0.0
    assert not hasattr(stats, 'end_time') or stats.end_time == 0.0
    assert not hasattr(stats, 'total_questions') or stats.total_questions == 0

def test_duration_calculation():
    """Test duration property calculation."""
    stats = ProcessingStats()
    # Mock attributes that will exist
    stats.start_time = 1000.0
    stats.end_time = 1060.0  # 60 seconds later
    
    # We expect a duration property
    assert stats.duration == 60.0

def test_duration_in_progress():
    """Test duration calculation while running."""
    stats = ProcessingStats()
    stats.start_time = time.time() - 10  # Started 10 seconds ago
    stats.end_time = 0.0
    
    # Allow small delta for execution time
    assert 9.0 <= stats.duration <= 11.0

def test_throughput_calculation():
    """Test questions per minute calculation."""
    stats = ProcessingStats()
    stats.start_time = 1000.0
    stats.end_time = 1060.0  # 60 seconds
    stats.total_questions = 10
    
    # 10 questions in 1 minute = 10 QPM
    assert stats.questions_per_minute == 10.0
    
    stats.total_questions = 30
    # 30 questions in 1 minute = 30 QPM
    assert stats.questions_per_minute == 30.0

def test_throughput_zero_duration():
    """Test throughput with zero duration to avoid division by zero."""
    stats = ProcessingStats()
    stats.start_time = 1000.0
    stats.end_time = 1000.0
    stats.total_questions = 10
    
    assert stats.questions_per_minute == 0.0
