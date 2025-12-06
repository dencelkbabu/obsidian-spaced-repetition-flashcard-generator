"""Configuration and data structures for MCQ flashcard generation.

This module defines configuration settings, path constants, and
data structures used throughout the application.
"""

import time
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# --- PATH CONFIGURATION ---
# Go up two levels: mcq_flashcards/core -> mcq_flashcards -> _scripts
SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent

# Allow override via environment variable for flexibility
VAULT_ROOT = Path(os.getenv("VAULT_ROOT", str(SCRIPT_DIR.parent)))
ACADEMICS_ROOT = VAULT_ROOT / "Academics"
BCOM_ROOT = ACADEMICS_ROOT / "BCom"
CONCEPT_SOURCE = ACADEMICS_ROOT / "Concepts"

# Default semester
DEFAULT_SEMESTER = "Semester One"

# Working Directories
CACHE_DIR = SCRIPT_DIR / "_cache"
RAW_DIR = SCRIPT_DIR / "_raw_responses"
ERROR_DIR = SCRIPT_DIR / "_errors"


def get_semester_paths(semester_name: str):
    """Get semester-specific paths for class root and output directory.
    
    Args:
        semester_name: Name of the semester (e.g., "Semester One")
        
    Returns:
        Tuple of (class_root, output_dir) paths
    """
    class_root = BCOM_ROOT / semester_name
    output_dir = BCOM_ROOT / "Flashcards" / semester_name
    return class_root, output_dir


# Ensure directories exist
for d in [CACHE_DIR, RAW_DIR, ERROR_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# --- DEFAULT SETTINGS ---
DEFAULT_MODEL = "llama3.1:8b"
DEFAULT_WORKERS = 4
MAX_RETRIES = 3
BASE_DELAY = 0.5
MAX_DELAY = 10.0
GPU_UTIL_HIGH = 80
GPU_UTIL_LOW = 35
LATENCY_TARGET = 1.5

# --- PROMPT SETTINGS ---
MAX_PROMPT_LENGTH = 6000  # Maximum characters to include in LLM prompt
QUESTIONS_PER_PROMPT = 5  # Number of MCQs to generate per API call (2.6x faster, quality maintained)

# --- AUTOTUNER SETTINGS ---
MAX_METRICS_HISTORY = 50  # Maximum number of latency/error samples to keep

# --- BLOOM'S TAXONOMY ---
BLOOM_LEVELS = ["remember", "understand", "apply", "analyze", "evaluate", "create"]
DEFAULT_BLOOM_LEVEL = None  # None = mixed levels

# --- DIFFICULTY LEVELS ---
DIFFICULTY_LEVELS = ["easy", "medium", "hard"]
DEFAULT_DIFFICULTY = None  # None = mixed difficulty

# --- STUDY MODE PRESETS ---
PRESETS = {
    "exam": {"bloom": "apply", "difficulty": "medium", "description": "Exam Prep (Apply + Medium) - Recommended for exam revision"},
    "review": {"bloom": "remember", "difficulty": "easy", "description": "Quick Review (Remember + Easy) - Fast recall practice"},
    "deep": {"bloom": "analyze", "difficulty": "hard", "description": "Deep Study (Analyze + Hard) - Advanced understanding"},
    "mixed": {"bloom": None, "difficulty": None, "description": "Mixed (Random levels) - Varied practice"},
}
DEFAULT_PRESET = "exam"  # Default to exam prep

# --- LOGGING SETUP ---
from logging.handlers import RotatingFileHandler

LOG_DIR = SCRIPT_DIR / "_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Create timestamped log filename (YYYYMMDD_HHMM format)
from datetime import datetime
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
LOG_FILE = LOG_DIR / f"flashcard_gen_{timestamp}.log"

def setup_logging(level=logging.INFO):
    """Configure logging with rotation.
    
    Args:
        level: Logging level (default: INFO)
        
    Returns:
        Configured logger instance
    """
    # Create handlers
    file_handler = RotatingFileHandler(
        LOG_FILE, 
        maxBytes=5*1024*1024,  # 5 MB
        backupCount=5,
        encoding='utf-8'
    )
    console_handler = logging.StreamHandler()
    
    # Create formatter
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root = logging.getLogger()
    root.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    if root.hasHandlers():
        root.handlers.clear()
        
    root.addHandler(file_handler)
    root.addHandler(console_handler)
    
    return logging.getLogger("FlashcardGen")

import os
level = logging.DEBUG if os.getenv('FLASHCARD_DEBUG') else logging.INFO
logger = setup_logging(level=level)


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
    semester: str = DEFAULT_SEMESTER
    dev_mode: bool = False
    bloom_level: Optional[str] = None  # Target Bloom's taxonomy level
    difficulty: Optional[str] = None  # Target difficulty level

    def validate(self) -> bool:
        """Validate configuration settings.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        # Validate semester path
        class_root, _ = get_semester_paths(self.semester)
        if not class_root.exists():
            if not self.dev_mode:
                logger.error(f"Semester directory not found: {class_root}")
                return False
            # In dev mode, we allow missing paths as we might be creating them
            
        # Validate weeks
        if not (1 <= self.start_week <= 52):
            logger.error(f"Invalid start week: {self.start_week}")
            return False
            
        if not (1 <= self.end_week <= 52):
            logger.error(f"Invalid end week: {self.end_week}")
            return False
            
        if self.start_week > self.end_week:
            logger.error(f"Start week ({self.start_week}) cannot be greater than end week ({self.end_week})")
            return False
            
        # Validate workers
        if self.workers < 1 or self.workers > 16:
            logger.error(f"Invalid worker count: {self.workers} (Must be 1-16)")
            return False
        
        # Validate Bloom's level
        if self.bloom_level and self.bloom_level not in BLOOM_LEVELS:
            logger.error(f"Invalid Bloom's level: {self.bloom_level}. Must be one of: {', '.join(BLOOM_LEVELS)}")
            return False
        
        # Validate difficulty
        if self.difficulty and self.difficulty not in DIFFICULTY_LEVELS:
            logger.error(f"Invalid difficulty: {self.difficulty}. Must be one of: {', '.join(DIFFICULTY_LEVELS)}")
            return False
            
        return True


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
    start_time: float = 0.0
    end_time: float = 0.0
    total_questions: int = 0
    
    @property
    def duration(self) -> float:
        if self.end_time > 0:
            return self.end_time - self.start_time
        elif self.start_time > 0:
            return time.time() - self.start_time
        return 0.0
        
    @property
    def questions_per_minute(self) -> float:
        d = self.duration
        if d > 0:
            return (self.total_questions / d) * 60
        return 0.0
