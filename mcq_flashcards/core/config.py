"""Configuration and data structures for MCQ flashcard generation.

This module defines configuration settings, path constants, and
data structures used throughout the application.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

# --- PATH CONFIGURATION ---
# Go up two levels: mcq_flashcards/core -> mcq_flashcards -> _scripts
SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent
VAULT_ROOT = SCRIPT_DIR.parent
ACADEMICS_ROOT = VAULT_ROOT / "Academics"
CLASS_ROOT = ACADEMICS_ROOT / r"BCom\Semester One"
CONCEPT_SOURCE = ACADEMICS_ROOT / "Concepts"
OUTPUT_DIR = ACADEMICS_ROOT / r"BCom\Flashcards"

# Working Directories
CACHE_DIR = SCRIPT_DIR / "_cache"
RAW_DIR = SCRIPT_DIR / "_raw_responses"
ERROR_DIR = SCRIPT_DIR / "_errors"

# Ensure directories exist
for d in [CACHE_DIR, RAW_DIR, ERROR_DIR, OUTPUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# --- DEFAULT SETTINGS ---
DEFAULT_MODEL = "llama3:8b"
DEFAULT_WORKERS = 4
MAX_RETRIES = 3
BASE_DELAY = 0.5
MAX_DELAY = 10.0
GPU_UTIL_HIGH = 80
GPU_UTIL_LOW = 35
LATENCY_TARGET = 1.5

# --- LOGGING SETUP ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("FlashcardGen")


# --- DATA STRUCTURES ---

@dataclass
class Config:
    """Configuration for flashcard generation."""
    model: str = DEFAULT_MODEL
    workers: int = DEFAULT_WORKERS
    temperature: float = 0.0
    top_p: float = 0.9
    max_tokens: int = 1500
    start_week: int = 1
    end_week: int = 12


@dataclass
class ProcessingStats:
    """Statistics for tracking processing progress."""
    total_files: int = 0
    processed_files: int = 0
    successful_cards: int = 0
    failed_cards: int = 0
    cache_hits: int = 0
    total_concepts: int = 0
    processed_concepts: int = 0
    refine_attempts: int = 0
    refine_success: int = 0
