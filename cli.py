"""Command-line interface for MCQ flashcard generation.

This module provides the main() function that handles user interaction
and orchestrates the flashcard generation process.
"""

import os

import requests

from mcq_flashcards import __version__
from mcq_flashcards.core.config import Config, CLASS_ROOT
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

    # Interactive Inputs
    print(f"\n📂 Available Subjects in {CLASS_ROOT}:")
    try:
        all_subjects = [d.name for d in CLASS_ROOT.iterdir() if d.is_dir() and d.name != "Flashcards"]
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
    elif (CLASS_ROOT / subj_input).exists():
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
            
            cfg = Config()
            gen = FlashcardGenerator(subject, cfg)
            gen.run(week)
        
        # Post-processing step
        print(f"\n{'='*40}")
        print("🧹 POST-PROCESSING")
        print(f"{'='*40}")
        
        from mcq_flashcards.utils.postprocessor import post_process_flashcards
        from mcq_flashcards.core.config import OUTPUT_DIR
        
        stats = post_process_flashcards(OUTPUT_DIR, verbose=True)
        
        if stats['total_fixes'] > 0:
            print(f"\n✨ Post-processing complete! Fixed {stats['total_fixes']} issues across {stats['files_with_issues']} files.")
            
            # Verification pass - check if any issues remain
            print("\n🔍 Running verification pass...")
            verify_stats = post_process_flashcards(OUTPUT_DIR, verbose=False)
            
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
