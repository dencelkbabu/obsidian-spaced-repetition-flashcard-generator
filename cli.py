"""Command-line interface for MCQ flashcard generation.

This module provides the main() function that handles user interaction
and orchestrates the flashcard generation process.
"""

import os

import requests

from mcq_flashcards import __version__
from mcq_flashcards.core.config import Config, BCOM_ROOT, DEFAULT_SEMESTER, get_semester_paths
from mcq_flashcards.core.generator import FlashcardGenerator
from mcq_flashcards.utils.power import WindowsInhibitor


def main():
    """Main CLI entry point for flashcard generation."""
    print(f"⚡ Flashcard Generator v{__version__}")
    
    # Check Ollama First
    try:
        requests.get("http://localhost:11434", timeout=1)
    except:
        print("❌ Error: Ollama is not running.")
        return

    # Semester Selection
    print(f"\n📚 Available Semesters:")
    try:
        semesters = [d.name for d in BCOM_ROOT.iterdir() 
                     if d.is_dir() and d.name.startswith("Semester")]
        if not semesters:
            print("❌ No semesters found.")
            return
        
        for i, sem in enumerate(semesters, 1):
            print(f"  {i}. {sem}")
    except Exception:
        print("❌ Error reading semesters.")
        return
    
    sem_input = input("\n📚 Select Semester (number or name, or Enter for default): ").strip()
    
    if not sem_input:
        semester = DEFAULT_SEMESTER
        print(f"   → Using default: {semester}")
    elif sem_input.isdigit():
        idx = int(sem_input) - 1
        if 0 <= idx < len(semesters):
            semester = semesters[idx]
        else:
            print("❌ Invalid semester number.")
            return
    else:
        # Try to match by name
        matches = [s for s in semesters if sem_input.lower() in s.lower()]
        if len(matches) == 1:
            semester = matches[0]
        else:
            print("❌ Invalid semester name.")
            return
    
    # Get semester-specific paths
    class_root, output_dir = get_semester_paths(semester)
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Interactive Inputs
    print(f"\n📂 Available Subjects in {semester}:")
    try:
        all_subjects = [d.name for d in class_root.iterdir() if d.is_dir()]
        print(" | ".join(all_subjects))
    except Exception:
        print("❌ Error reading subjects.")
        return

    subj_input = input("\n🎯 Enter Subject Code (or press Enter for ALL): ").strip().upper()
    
    # Default to ALL if empty
    if not subj_input:
        subj_input = "ALL"
        print("   → Processing ALL subjects")
    
    target_subjects = []
    if subj_input == "ALL":
        target_subjects = all_subjects
    elif (class_root / subj_input).exists():
        target_subjects = [subj_input]
    else:
        print("❌ Invalid subject.")
        return

    week_in = input("📅 Enter Week (or Enter for All): ").strip()
    week = int(week_in) if week_in.isdigit() else None

    # System Power Management
    os_inhibitor = None
    if os.name == 'nt':
        os_inhibitor = WindowsInhibitor()
        os_inhibitor.inhibit()

    try:
        for i, subject in enumerate(target_subjects, 1):
            if len(target_subjects) > 1:
                print(f"\n{'='*40}")
                print(f"🔄 BATCH PROCESSING {i}/{len(target_subjects)}: {subject}")
                print(f"{'='*40}")
            
            cfg = Config(semester=semester)
            gen = FlashcardGenerator(subject, cfg, class_root, output_dir)
            gen.run(week)
        
        # Post-processing step
        print(f"\n{'='*40}")
        print("🧹 POST-PROCESSING")
        print(f"{'='*40}")
        
        from mcq_flashcards.utils.postprocessor import post_process_flashcards
        
        stats = post_process_flashcards(output_dir, verbose=True)
        
        if stats['total_fixes'] > 0:
            print(f"\n✨ Post-processing complete! Fixed {stats['total_fixes']} issues across {stats['files_with_issues']} files.")
            
            # Verification pass - check if any issues remain
            print("\n🔍 Running verification pass...")
            verify_stats = post_process_flashcards(output_dir, verbose=False)
            
            if verify_stats['total_fixes'] > 0:
                print(f"⚠️  Warning: {verify_stats['total_fixes']} issues still detected after post-processing!")
                print("   The post-processor logic may need improvement.")
            else:
                print("✓ Verification passed: All files are clean!")
        else:
            print(f"\n✓ No issues found. All files are clean!")
            
    finally:
        if os_inhibitor:
            os_inhibitor.uninhibit()


if __name__ == "__main__":
    main()
