"""Command-line interface for MCQ flashcard generation.

This module provides the main() function that handles user interaction
and orchestrates the flashcard generation process.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional

import requests
from tqdm import tqdm

from mcq_flashcards import __version__
from mcq_flashcards.core.config import (
    Config, 
    BCOM_ROOT, 
    DEFAULT_SEMESTER, 
    get_semester_paths,
    CACHE_DIR,
    BLOOM_LEVELS,
    DIFFICULTY_LEVELS,
    PRESETS,
)
from mcq_flashcards.core.generator import FlashcardGenerator
from mcq_flashcards.utils.power import WindowsInhibitor
from mcq_flashcards.utils.postprocessor import post_process_flashcards


def check_ollama() -> bool:
    """Check if Ollama is running."""
    try:
        requests.get("http://localhost:11434", timeout=1)
        return True
    except (requests.ConnectionError, requests.Timeout) as e:
        print("❌ Error: Ollama is not running.")
        return False


def parse_week_argument(week_arg: str) -> Optional[List[int]]:
    """Parse week argument into list of week numbers.
    
    Supports multiple formats:
    - Single: "1" → [1]
    - Range: "1-4" → [1, 2, 3, 4]
    - List: "1,3,5" → [1, 3, 5]
    - Mixed: "1-3,5,7-9" → [1, 2, 3, 5, 7, 8, 9]
    - All: "ALL" → None
    
    Args:
        week_arg: Week argument string
        
    Returns:
        List of week numbers, or None for ALL weeks, or empty list on error
    """
    if not week_arg or week_arg.lower() == "all":
        return None
    
    weeks = set()
    
    try:
        # Split by comma
        parts = week_arg.split(',')
        
        for part in parts:
            part = part.strip()
            
            # Check for range (e.g., "1-4")
            if '-' in part:
                start, end = part.split('-', 1)
                start, end = int(start.strip()), int(end.strip())
                
                if start > end:
                    print(f"❌ Invalid range: {part} (start > end)")
                    return []
                
                if start < 1 or end > 52:
                    print(f"❌ Invalid range: {part} (weeks must be 1-52)")
                    return []
                
                weeks.update(range(start, end + 1))
            else:
                # Single week number
                week_num = int(part)
                if week_num < 1 or week_num > 52:
                    print(f"❌ Invalid week: {week_num} (must be 1-52)")
                    return []
                weeks.add(week_num)
        
        return sorted(list(weeks))
    
    except ValueError:
        print(f"❌ Invalid week format: {week_arg}")
        print("   Valid formats: 1, 1-4, 1,3,5, 1-3,5, ALL")
        return []


def clear_cache(subject: str) -> None:
    """Clear cache files for the specified subject or all subjects.
    
    Args:
        subject: Subject code or "ALL"
    """
    if not CACHE_DIR.exists():
        return

    files_to_delete = []
    if subject == "ALL":
        files_to_delete = list(CACHE_DIR.glob("*.json")) + list(CACHE_DIR.glob("*.pkl"))
        print(f"\n🧹 Clearing entire cache directory...")
    else:
        files_to_delete = list(CACHE_DIR.glob(f"{subject}_*.json")) + list(CACHE_DIR.glob(f"{subject}_*.pkl"))
        print(f"\n🧹 Clearing cache for {subject}...")

    if not files_to_delete:
        print("   → No cache files found.")
        return

    count = 0
    for f in tqdm(files_to_delete, desc="Clearing cache", unit="file"):
        try:
            f.unlink()
            count += 1
        except Exception as e:
            tqdm.write(f"   ⚠️ Failed to delete {f.name}: {e}")

    print(f"   → Cleared {count} cache files")


def cleanup_dev_folder(output_dir: Path) -> None:
    """Clean up _dev folder and its contents.
    
    Args:
        output_dir: Path to the Flashcards output directory
    """
    dev_dir = output_dir.parent / "_dev"
    if dev_dir.exists():
        try:
            import shutil
            shutil.rmtree(dev_dir)
            print("🧹 Cleaned up _dev folder from previous testing")
        except Exception as e:
            print(f"⚠️  Warning: Could not clean _dev folder: {e}")


def get_semesters() -> List[str]:
    """Get list of available semesters."""
    try:
        return [d.name for d in BCOM_ROOT.iterdir() 
                if d.is_dir() and d.name.startswith("Semester")]
    except (FileNotFoundError, PermissionError) as e:
        print(f"⚠️  Warning: Could not read semesters: {e}")
        return []



def select_semester() -> Optional[str]:
    """Prompt user to select a semester interactively.
    
    Returns:
        Selected semester name, or None if selection failed
    """
    semesters = get_semesters()
    if not semesters:
        print("❌ No semesters found.")
        return None

    print(f"\n📚 Available Semesters:")
    for i, sem in enumerate(semesters, 1):
        print(f"  {i}. {sem}")
    
    sem_input = input("\n📚 Select Semester (number or name, or Enter for default): ").strip()
    
    if not sem_input:
        semester = DEFAULT_SEMESTER
        print(f"   → Using default: {semester}")
        return semester
    
    if sem_input.isdigit():
        idx = int(sem_input) - 1
        if 0 <= idx < len(semesters):
            return semesters[idx]
        else:
            print("❌ Invalid semester number.")
            return None
    
    matches = [s for s in semesters if sem_input.lower() in s.lower()]
    if len(matches) == 1:
        return matches[0]
    else:
        print("❌ Invalid semester name.")
        return None


def select_subjects(class_root: Path, semester: str) -> Optional[List[str]]:
    """Prompt user to select subjects interactively.
    
    Args:
        class_root: Path to semester's class root directory
        semester: Semester name for display
        
    Returns:
        List of selected subject codes, or None if selection failed
    """
    print(f"\n📂 Available Subjects in {semester}:")
    try:
        all_subjects = [d.name for d in class_root.iterdir() if d.is_dir()]
        print(" | ".join(all_subjects))
    except (FileNotFoundError, PermissionError) as e:
        print(f"❌ Error reading subjects: {e}")
        return None

    subj_input = input("\n🎯 Enter Subject Code (or press Enter for ALL): ").strip().upper()
    
    if not subj_input or subj_input == "ALL":
        if not subj_input:
            print("   → Processing ALL subjects")
        return all_subjects
    
    if (class_root / subj_input).exists():
        return [subj_input]
    else:
        print("❌ Invalid subject.")
        return None


def select_week() -> Optional[int]:
    """Prompt user to select a week number.
    
    Returns:
        Week number, or None for all weeks
    """
    week_in = input("📅 Enter Week (or Enter for All): ").strip()
    return int(week_in) if week_in.isdigit() else None


def select_preset() -> tuple[Optional[str], Optional[str]]:
    """Prompt user to select a study mode preset.
    
    Returns:
        Tuple of (bloom_level, difficulty)
    """
    print(f"\n🎯 Select Study Mode:")
    
    # Display presets dynamically
    preset_keys = ["exam", "review", "deep", "mixed"]
    for i, key in enumerate(preset_keys, 1):
        print(f"  {i}. {PRESETS[key]['description']}")
    print(f"  5. Custom (Advanced - Choose Bloom's + Difficulty manually)")
    
    preset_input = input("\nSelect mode (1-5, or Enter for Exam Prep): ").strip()
    
    # Default to exam prep
    if not preset_input:
        preset = PRESETS["exam"]
        print("   → Using: Exam Prep (Apply + Medium)")
        return preset["bloom"], preset["difficulty"]
    
    # Map number to preset
    preset_map = {
        "1": "exam",
        "2": "review",
        "3": "deep",
        "4": "mixed",
    }
    
    if preset_input in preset_map:
        preset_key = preset_map[preset_input]
        preset = PRESETS[preset_key]
        print(f"   → Using: {preset['description'].split(' - ')[0]}")
        return preset["bloom"], preset["difficulty"]
    
    # Custom option
    if preset_input == "5":
        print("\n📚 Custom Mode - Select Bloom's and Difficulty:")
        bloom = select_bloom_level_custom()
        difficulty = select_difficulty_custom()
        return bloom, difficulty
    
    # Invalid input, default to exam prep
    print("❌ Invalid selection. Using Exam Prep.")
    preset = PRESETS["exam"]
    return preset["bloom"], preset["difficulty"]


def select_bloom_level_custom() -> Optional[str]:
    """Prompt user to select Bloom's level (for custom mode only)."""
    print(f"\n🎓 Bloom's Taxonomy Levels:")
    for i, level in enumerate(BLOOM_LEVELS, 1):
        print(f"  {i}. {level.capitalize()}")
    
    bloom_input = input("\n🎯 Select Bloom's Level (number/name, or Enter for mixed): ").strip().lower()
    
    if not bloom_input:
        return None
    
    if bloom_input.isdigit():
        idx = int(bloom_input) - 1
        if 0 <= idx < len(BLOOM_LEVELS):
            return BLOOM_LEVELS[idx]
    
    if bloom_input in BLOOM_LEVELS:
        return bloom_input
    
    matches = [level for level in BLOOM_LEVELS if bloom_input in level]
    if len(matches) == 1:
        return matches[0]
    
    return None


def select_difficulty_custom() -> Optional[str]:
    """Prompt user to select difficulty (for custom mode only)."""
    print(f"\n💪 Difficulty Levels:")
    for i, level in enumerate(DIFFICULTY_LEVELS, 1):
        print(f"  {i}. {level.capitalize()}")
    
    diff_input = input("\n🎯 Select Difficulty (number/name, or Enter for mixed): ").strip().lower()
    
    if not diff_input:
        return None
    
    if diff_input.isdigit():
        idx = int(diff_input) - 1
        if 0 <= idx < len(DIFFICULTY_LEVELS):
            return DIFFICULTY_LEVELS[idx]
    
    if diff_input in DIFFICULTY_LEVELS:
        return diff_input
    
    matches = [level for level in DIFFICULTY_LEVELS if diff_input in level]
    if len(matches) == 1:
        return matches[0]
    
    return None


def run_interactive() -> None:
    """Run in interactive production mode."""
    print(f"⚡ Flashcard Generator v{__version__}")
    
    if not check_ollama():
        return

    # Semester Selection
    semester = select_semester()
    if not semester:
        return
    
    class_root, output_dir = get_semester_paths(semester)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Clean up _dev folder from testing
    cleanup_dev_folder(output_dir)

    # Subject Selection
    target_subjects = select_subjects(class_root, semester)
    if not target_subjects:
        return

    # Week Selection
    week = select_week()

    # Study Mode Preset Selection
    bloom_level, difficulty = select_preset()

    # Cache Clearing
    should_clear = input("\n🧹 Clear cache before processing? (y/n) [n]: ").strip().lower()
    if should_clear == 'y':
        # Determine subject for cache clearing
        subject_for_cache = "ALL" if len(target_subjects) > 1 else target_subjects[0]
        clear_cache(subject_for_cache)

    # Execution
    execute_generation(target_subjects, semester, class_root, output_dir, [week] if week else None, dev_mode=False, bloom_level=bloom_level, difficulty=difficulty)


def run_dev(args: argparse.Namespace) -> None:
    """Run in development mode with CLI arguments."""
    # Set debug logging if requested
    if args.debug:
        os.environ['FLASHCARD_DEBUG'] = '1'
        # Reinitialize logger to pick up debug level
        import logging
        from mcq_flashcards.core.config import setup_logging
        setup_logging(level=logging.DEBUG)
    
    print(f"⚡ Flashcard Generator v{__version__} (Dev Mode)")
    
    if not check_ollama():
        return

    # Semester
    semester = args.semester
    if not semester:
        semesters = get_semesters()
        if semesters:
            semester = semesters[0] # Default to first found
        else:
            semester = DEFAULT_SEMESTER
    
    class_root, output_dir = get_semester_paths(semester)
    if not class_root.exists():
        print(f"❌ Semester directory not found: {class_root}")
        return
    output_dir.mkdir(parents=True, exist_ok=True)

    # Subject
    subject = args.subject.upper()
    target_subjects = []
    
    if subject == "ALL":
        try:
            target_subjects = [d.name for d in class_root.iterdir() if d.is_dir()]
        except (FileNotFoundError, PermissionError) as e:
            print(f"❌ Error reading subjects: {e}")
            return
    elif (class_root / subject).exists():
        target_subjects = [subject]
    else:
        print(f"❌ Invalid subject: {subject}")
        return

    # Week
    weeks = None  # None = ALL weeks
    if args.week:
        weeks = parse_week_argument(args.week)
        if weeks == []:  # Empty list = parsing error
            return
    else:
        # Default to Week 1 in dev mode if not specified
        weeks = [1]

    # Cache Clearing
    if args.clear_cache or args.deep_clear:
        clear_cache(subject)
        if args.deep_clear:
            print("✨ Cache cleared (Deep Clean). Exiting.")
            return

    # Execution
    weeks_display = "ALL" if weeks is None else ", ".join(map(str, weeks))
    print(f"\n📂 Processing: {subject} - Week(s) {weeks_display} - {semester}")
    execute_generation(target_subjects, semester, class_root, output_dir, weeks, dev_mode=True, bloom_level=args.bloom, difficulty=args.difficulty)


def execute_generation(subjects: List[str], semester: str, class_root: Path, output_dir: Path, weeks: Optional[List[int]], dev_mode: bool = False, bloom_level: Optional[str] = None, difficulty: Optional[str] = None):
    """Common execution logic for both modes.
    
    Args:
        weeks: List of week numbers to process, or None for ALL weeks
    """
    os_inhibitor = None
    if os.name == 'nt':
        os_inhibitor = WindowsInhibitor()
        os_inhibitor.inhibit()

    try:
        for i, subject in enumerate(subjects, 1):
            if len(subjects) > 1:
                print(f"\n{'='*40}")
                print(f"🔄 BATCH PROCESSING {i}/{len(subjects)}: {subject}")
                print(f"{'='*40}")
            
            cfg = Config(semester=semester, dev_mode=dev_mode, bloom_level=bloom_level, difficulty=difficulty)
            
            # Validate configuration
            if not cfg.validate():
                print("❌ Configuration validation failed. Check logs for details.")
                continue

            gen = FlashcardGenerator(subject, cfg, class_root, output_dir)
            
            # Process weeks
            if weeks is None:
                # ALL weeks
                gen.run(None)
            elif len(weeks) == 1:
                # Single week
                gen.run(weeks[0])
            else:
                # Multiple specific weeks
                for week_num in weeks:
                    print(f"\n{'─'*40}")
                    print(f"📝 Processing Week {week_num}")
                    print(f"{'─'*40}")
                    gen.run(week_num)
        
        # Post-processing
        print(f"\n{'='*40}")
        print("🧹 POST-PROCESSING")
        print(f"{'='*40}")
        
        stats = post_process_flashcards(output_dir, verbose=True)
        
        if stats['total_fixes'] > 0:
            print(f"\n✨ Post-processing complete! Fixed {stats['total_fixes']} issues across {stats['files_with_issues']} files.")
            
            print("\n🔍 Running verification pass...")
            verify_stats = post_process_flashcards(output_dir, verbose=False)
            
            if verify_stats['total_fixes'] > 0:
                print(f"⚠️  Warning: {verify_stats['total_fixes']} issues still detected after post-processing!")
            else:
                print("✓ Verification passed: All files are clean!")
        else:
            print(f"\n✓ No issues found. All files are clean!")
            
    finally:
        if os_inhibitor:
            os_inhibitor.uninhibit()


def main() -> None:
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="MCQ Flashcard Generator",
        usage="%(prog)s [-d SUBJECT [WEEK] [-c]] | %(prog)s (interactive)"
    )
    
    # Dev mode flag
    parser.add_argument("-d", "--dev", action="store_true", help="Enable development mode")
    
    # Positional arguments for dev mode
    parser.add_argument("subject", nargs="?", help="Subject code or ALL (Required in dev mode)")
    parser.add_argument("week", nargs="?", help="Week(s): number (1), range (1-4), list (1,3,5), or ALL (Default: 1)")
    
    # Optional flags
    parser.add_argument("-c", "--clear-cache", action="store_true", help="Clear cache before processing")
    parser.add_argument("--deep-clear", action="store_true", help="Only clear cache and exit (requires -d)")
    parser.add_argument("--debug", action="store_true", help="Enable detailed DEBUG logging")
    parser.add_argument("--bloom", choices=BLOOM_LEVELS, help="Target Bloom's taxonomy level")
    parser.add_argument("--difficulty", choices=DIFFICULTY_LEVELS, help="Target difficulty level")
    parser.add_argument("-s", "--semester", help="Override semester (Dev mode)")
    parser.add_argument("-w", "--week-flag", dest="week_flag", help="Override week (Alternative flag)")

    args = parser.parse_args()

    # Logic Dispatch
    if args.dev:
        if args.deep_clear and not args.subject:
            args.subject = "ALL"
            
        if not args.subject:
            print("❌ Error: Dev mode requires a subject argument")
            print("\nUsage:")
            print("  Dev mode:   python mcq_flashcards.py -d <SUBJECT> [WEEK] [-c]")
            print("  Prod mode:  python mcq_flashcards.py")
            return
        
        # Handle week argument (positional vs flag)
        if args.week_flag:
            args.week = args.week_flag
            
        run_dev(args)
    else:
        # Prod mode (Interactive)
        if args.subject or args.week or args.clear_cache or args.semester:
            # User provided args but forgot -d
            print("❌ Error: Arguments provided without --dev flag.")
            print("Use -d to enable dev mode, or run without arguments for interactive mode.")
            return
            
        run_interactive()


if __name__ == "__main__":
    main()
