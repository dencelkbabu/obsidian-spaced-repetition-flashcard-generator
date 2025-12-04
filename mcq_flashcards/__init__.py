"""MCQ Flashcard Generator Package

A modular flashcard generation system for creating high-quality
multiple-choice questions from lecture notes.

Version: 3.11.0
"""

__version__ = "3.11.0"

# Core exports
from mcq_flashcards.core.config import Config, ProcessingStats
from mcq_flashcards.core.client import OllamaClient
from mcq_flashcards.core.generator import FlashcardGenerator

# Processing exports
from mcq_flashcards.processing.cleaner import MCQCleaner
from mcq_flashcards.processing.validator import MCQValidator

# Utility exports
from mcq_flashcards.utils.autotuner import AutoTuner, AUTOTUNER
from mcq_flashcards.utils.power import WindowsInhibitor

__all__ = [
    "__version__",
    "Config",
    "ProcessingStats",
    "OllamaClient",
    "FlashcardGenerator",
    "MCQCleaner",
    "MCQValidator",
    "AutoTuner",
    "AUTOTUNER",
    "WindowsInhibitor",
]
