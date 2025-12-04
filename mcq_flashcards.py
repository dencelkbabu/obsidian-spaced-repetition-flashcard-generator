#!/usr/bin/env python3
"""MCQ Flashcard Generator - Backwards Compatible Entry Point

This file maintains backwards compatibility with the original script.
The actual implementation has been refactored into the mcq_flashcards package.

For new code, import from the package directly:
    from mcq_flashcards import FlashcardGenerator, Config
    
Or use the cli module:
    from cli import main
"""

from cli import main

if __name__ == "__main__":
    main()