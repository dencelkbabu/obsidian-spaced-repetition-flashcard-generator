"""Main flashcard generation logic.

This module contains the FlashcardGenerator class which orchestrates
the entire MCQ generation process from lecture notes.
"""

import concurrent.futures
import hashlib
import json
import os
import random
import re
import threading
import time
import tempfile
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from tqdm import tqdm

from mcq_flashcards.core.config import (
    Config,
    ProcessingStats,
    CONCEPT_SOURCE,
    CACHE_DIR,
    RAW_DIR,
    ERROR_DIR,
    BASE_DELAY,
    MAX_PROMPT_LENGTH,
    logger,
)
from mcq_flashcards.core.client import OllamaClient
from mcq_flashcards.processing.cleaner import MCQCleaner
from mcq_flashcards.processing.validator import MCQValidator
from mcq_flashcards.core.prompts import (
    PERSONAS,
    BLOOM_INSTRUCTIONS,
    DIFFICULTY_INSTRUCTIONS,
    SYSTEM_PROMPT_TEMPLATE,
    GENERATION_PROMPT_TEMPLATE,
    REFINE_PROMPT_TEMPLATE
)



class FlashcardGenerator:
    """Main flashcard generation orchestrator."""
    
    def __init__(self, subject: str, config: Config, class_root: Path, output_dir: Path):
        """Initialize the flashcard generator.
        
        Args:
            subject: Subject code (e.g., 'ACCT1001')
            config: Configuration object
            class_root: Path to semester's class root directory
            output_dir: Path to output directory for flashcards
        """
        self.subject = subject.upper()
        self.config = config
        self.class_root = class_root
        self.output_dir = output_dir
        self.client = OllamaClient(config)
        self.cleaner = MCQCleaner()
        self.validator = MCQValidator()
        self.stats = ProcessingStats()
        self.file_lock = threading.Lock()
        self.stats_lock = threading.Lock()
        
        self.subject_path = self.class_root / self.subject
        self.persona, self.focus = self._get_persona()

    def _get_persona(self) -> Tuple[str, str]:
        """Get subject-specific persona and focus for prompt engineering.
        
        Returns:
            Tuple of (persona, focus) strings
        """
        for key, (persona, focus) in PERSONAS.items():
            if key in self.subject and key != "DEFAULT":
                return persona, focus
        return PERSONAS["DEFAULT"]

    def _get_bloom_instruction(self) -> str:
        """Get Bloom's taxonomy instruction for prompt.
        
        Returns:
            Bloom's level instruction, or empty string if no level specified
        """
        if not self.config.bloom_level:
            return ""
        return BLOOM_INSTRUCTIONS.get(self.config.bloom_level, "")

    def _get_difficulty_instruction(self) -> str:
        """Get difficulty level instruction for prompt.
        
        Returns:
            Difficulty instruction, or empty string if no difficulty specified
        """
        if not self.config.difficulty:
            return ""
        return DIFFICULTY_INSTRUCTIONS.get(self.config.difficulty, "")



    def get_cache_key(self, text: str) -> Path:
        """Generate cache key for a given text.
        
        Args:
            text: Input text to cache
            
        Returns:
            Path to cache file
        """
        combined = f"{self.config.model}_{text}"
        hash_key = hashlib.md5(combined.encode()).hexdigest()
        return CACHE_DIR / f"{self.subject}_{hash_key}.json"

    def _save_raw_log(self, name: str, data: any, suffix: str = ""):
        """Save raw API response for debugging.
        
        Args:
            name: Name for the log file
            data: Data to save
            suffix: Optional suffix for filename
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{name}{suffix}.json"
            clean_name = re.sub(r'[\\/*?:"<>|]', "", filename)  # Sanitize
            with open(RAW_DIR / clean_name, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Failed to save raw log: {e}")

    def _save_error_log(self, name: str, error: str, context: str):
        """Save error log for debugging.
        
        Args:
            name: Name for the error log
            error: Error message
            context: Additional context (e.g., stack trace)
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ERROR_{timestamp}_{name}.txt"
            clean_name = re.sub(r'[\\/*?:"<>|]', "", filename)
            with open(ERROR_DIR / clean_name, 'w', encoding='utf-8') as f:
                f.write(f"Error: {error}\n\nContext:\n{context}")
        except Exception:
            pass

    def _construct_prompt(self, context: str, num_questions: int = 5) -> str:
        """Construct the prompt for the LLM.
        
        Args:
            context: The text content to generate questions from
            num_questions: Number of questions to generate
            
        Returns:
            Formatted prompt string
        """
        bloom = self._get_bloom_instruction()
        difficulty = self._get_difficulty_instruction()
        
        return GENERATION_PROMPT_TEMPLATE.format(
            context=context,
            num_questions=num_questions,
            bloom_instruction=bloom,
            difficulty_instruction=difficulty
        )

    def generate_single(self, text: str, name: str) -> Optional[str]:
        """Generate MCQs for a single piece of text.
        
        Args:
            text: Source text to generate MCQs from
            name: Name for logging/caching
            
        Returns:
            Generated MCQ text, or None if generation failed
        """
        # Check Cache
        cache_path = self.get_cache_key(text)
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    with self.stats_lock:
                        self.stats.cache_hits += 1
                    return json.load(f)
            except (json.JSONDecodeError, EOFError, FileNotFoundError) as e:
                logger.warning(f"Cache read failed for {name}: {e}. Regenerating...")

        # Construct Prompt
        prompt = self._construct_prompt(text)
        
        # Call LLM
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            persona=self.persona,
            focus=self.focus
        )
        
        worker_state = {"delay": BASE_DELAY + random.uniform(0, 0.2), "retries": 0}
        
        # 1. Initial Generation
        response = self.client.generate(prompt, worker_state, system=system_prompt)
        if not response or 'response' not in response:
            return None

        self._save_raw_log(name, response, "_raw")
        cleaned_text = self.cleaner.clean_ai_output(response['response'])

        # 2. Validation & Refine Pass
        if not self.validator.validate(cleaned_text):
            with self.stats_lock:
                self.stats.refine_attempts += 1
            logger.info(f"⚠️  Invalid format for {name}. Attempting Self-Correction...")
            
            refine_prompt = REFINE_PROMPT_TEMPLATE.format(content=cleaned_text)
            
            refine_response = self.client.generate(refine_prompt, worker_state)
            if refine_response and 'response' in refine_response:
                self._save_raw_log(name, refine_response, "_refine")
                cleaned_refine = self.cleaner.clean_ai_output(refine_response['response'])
                
                if self.validator.validate(cleaned_refine):
                    with self.stats_lock:
                        self.stats.refine_success += 1
                    cleaned_text = cleaned_refine  # Success!
                else:
                    self._save_error_log(name, "Validation Failed after Refine", cleaned_refine)
                    return None
            else:
                return None

        # Save to Cache (atomic write to prevent corruption)
        temp_fd, temp_path = tempfile.mkstemp(dir=CACHE_DIR, suffix='.json', text=True)
        try:
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                json.dump(cleaned_text, f, ensure_ascii=False)
            # Atomic move (POSIX atomic, Windows near-atomic)
            os.replace(temp_path, cache_path)
        except Exception as e:
            # Clean up temp file on error
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            logger.warning(f"Failed to write cache for {name}: {e}")
            
        return cleaned_text

    def process_item(self, args) -> Optional[str]:
        """Process a single item (lecture or concept).
        
        Args:
            args: Tuple of (text, name, is_concept)
            
        Returns:
            Formatted MCQ section, or None if processing failed
        """
        text, name, is_concept = args
        if len(text) < 20:
            return None

        try:
            result = self.generate_single(text, name)
            if result:
                with self.stats_lock:
                    self.stats.successful_cards += 1
                    self.stats.total_questions += QUESTIONS_PER_PROMPT
                    if is_concept:
                        self.stats.processed_concepts += 1
                    else:
                        self.stats.processed_files += 1
                
                if is_concept:
                    return f"### Concept: {name}\n\n{result}\n\n---\n"
                else:
                    clean_name = name.replace('.md', '')
                    return f"### {clean_name}\n\n{result}\n\n---\n"
            else:
                with self.stats_lock:
                    self.stats.failed_cards += 1
                return None
        except Exception as e:
            with self.stats_lock:
                self.stats.failed_cards += 1
            self._save_error_log(name, str(e), traceback.format_exc())
            return None

    def extract_summary(self, file_path: Path) -> Tuple[Optional[str], Set[str]]:
        """Extract summary and wikilinks from a markdown file.
        
        Args:
            file_path: Path to markdown file
            
        Returns:
            Tuple of (summary_text, set_of_wikilinks)
        """
        try:
            content = file_path.read_text(encoding='utf-8')
            patterns = [
                r'##\s*Key Concepts.*?\n(.*?)(?=\n##|\Z)',
                r'##\s*Key\s+Concepts.*?\n(.*?)(?=\n##|\Z)',
                r'###\s*Key Concepts.*?\n(.*?)(?=\n##|\Z)',
                r'#\s*Key Concepts.*?\n(.*?)(?=\n#|\Z)'
            ]
            summary = None
            for pattern in patterns:
                match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
                if match:
                    summary = self.cleaner.clean_wikilinks(match.group(1).strip())
                    break
            
            if not summary:
                summary = self.cleaner.clean_wikilinks(content)
            
            # Regex to capture the filename part of a wikilink
            # Matches [[Filename]] or [[Filename|Alias]] or [[Filename#Anchor]]
            # Group 1 is the Filename
            links = re.findall(r'\[\[([^|#\]]+)(?:[|#][^\]]+)?\]\]', content)
            cleaned_links = {link.strip() for link in links}
            return summary, cleaned_links
        except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
            logger.warning(f"Failed to extract summary from {file_path}: {e}")
            return None, set()

    def process_week(self, week: int, files: List[Path], limit: int):
        """Process all files for a given week.
        
        Args:
            week: Week number
            files: List of markdown files for this week
            limit: Limit on number of concepts to process (0 = no limit)
        """
        # Reset Stats for this week
        self.stats = ProcessingStats()
        self.stats.start_time = time.time()
        
        # Build filename with optional Bloom's level and difficulty
        bloom_suffix = f"_{self.config.bloom_level}" if self.config.bloom_level else ""
        diff_suffix = f"_{self.config.difficulty}" if self.config.difficulty else ""
        out_name = f"{self.subject}_W{week:02d}_MCQ{bloom_suffix}{diff_suffix}.md"
        tag = f"W{week:02d}"
        
        # Dev Mode Handling
        if self.config.dev_mode:
            # Use _dev subdirectory and append suffix
            dev_dir = self.output_dir.parent / "_dev"
            dev_dir.mkdir(parents=True, exist_ok=True)
            out_name = f"{self.subject}_W{week:02d}_MCQ{bloom_suffix}{diff_suffix}_dev.md"
            out_path = dev_dir / out_name
            # Auto-overwrite in dev mode (no prompt)
        else:
            out_path = self.output_dir / out_name
            
            # Interactive Overwrite Check (Prod only)
            if out_path.exists():
                print(f"\n⚠️  {out_name} exists.")
                if input("   Overwrite? (y/n): ").lower() != 'y':
                    print("   Skipping...")
                    return

        # Write Header
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(f"---\ntags:\n- flashcard/{self.subject}/{tag}\n---\n")
            f.write(f"## MCQs: {self.subject} - {tag}\n\n")

        self.stats.total_files = len(files)
        
        # Prepare Lecture Jobs
        lecture_jobs = []
        concepts_set = set()
        
        print(f"\n📝 Extracting content for Week {week}...")
        for p in tqdm(files):
            summary, links = self.extract_summary(p)
            concepts_set.update(links)
            if summary:
                lecture_jobs.append((summary, p.name, False))

        # Prepare Concept Jobs
        concept_jobs = []
        self.stats.total_concepts = len(concepts_set)
        c_list = list(concepts_set)
        if limit > 0:
            c_list = c_list[:limit]
        
        for c in c_list:
            cp = CONCEPT_SOURCE / f"{c}.md"
            if cp.exists():
                s, _ = self.extract_summary(cp)
                if s:
                    concept_jobs.append((s, c, True))

        # Execute
        all_jobs = lecture_jobs + concept_jobs
        print(f"🚀 Processing {len(all_jobs)} items with {self.config.workers} workers...")

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.workers) as executor:
            futures = [executor.submit(self.process_item, job) for job in all_jobs]
            
            for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Generating"):
                result = future.result()
                if result:
                    with self.file_lock:
                        with open(out_path, 'a', encoding='utf-8') as f:
                            f.write(result)

        # Final Report for Week
        self.stats.end_time = time.time()
        print(f"🎉 DONE! Output: {out_name}")
        print(f"📊 Statistics for Week {week}:")
        print(f"   Files: {self.stats.processed_files}/{self.stats.total_files}")
        print(f"   Concepts: {self.stats.processed_concepts}/{self.stats.total_concepts}")
        print(f"   Success: {self.stats.successful_cards} | Failed: {self.stats.failed_cards}")
        print(f"   Cache Hits: {self.stats.cache_hits}")
        print(f"   Self-Corrections: {self.stats.refine_success}/{self.stats.refine_attempts}")
        print(f"   ⏱️  Time: {self.stats.duration:.1f}s ({self.stats.questions_per_minute:.1f} Q/min)")

    def run(self, target_week: Optional[int], limit: int = 0):
        """Run the flashcard generation process.
        
        Args:
            target_week: Specific week to process, or None for all weeks
            limit: Limit on concepts per week (0 = no limit)
        """
        if not self.client.check_connection():
            print("❌ Ollama not reachable. Start with 'ollama serve'.")
            return

        # 1. Scan and Group Files by Week
        week_files: Dict[int, List[Path]] = {}
        target_dirs = [self.subject_path / d for d in ["Recorded Lectures", "Live Lectures"] if (self.subject_path / d).exists()]
        
        print(f"\n🔍 Scanning {self.subject}...")
        for d in target_dirs:
            for p in d.rglob("*.md"):
                match = re.search(r'(?:W|Week)\s?0?(\d+)', p.name, re.IGNORECASE)
                if match:
                    wk = int(match.group(1))
                    
                    # Filter if specific week requested
                    if target_week and wk != target_week:
                        continue
                    
                    # Filter by config range
                    if not target_week and not (self.config.start_week <= wk <= self.config.end_week):
                        continue
                    
                    if wk not in week_files:
                        week_files[wk] = []
                    week_files[wk].append(p)

        if not week_files:
            print("❌ No files found.")
            return

        # 2. Process Each Week
        sorted_weeks = sorted(week_files.keys())
        print(f"📅 Found weeks: {', '.join(map(str, sorted_weeks))}")
        print(f"   (AutoTuner Active: Monitoring GPU & Errors)")
        
        for wk in sorted_weeks:
            self.process_week(wk, week_files[wk], limit)
