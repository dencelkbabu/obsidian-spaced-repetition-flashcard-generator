"""Script to scan and report errors in existing flashcard files."""

import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcq_flashcards.processing.content_validator import get_validator, VALIDATORS


def scan_flashcard_file(filepath: Path) -> list:
    """Scan a flashcard file for content errors."""
    errors = []
    
    # Determine subject from filename
    filename = filepath.name
    subject = None
    for key in VALIDATORS.keys():
        if key in filename:
            subject = key
            break
    
    if not subject:
        return errors
    
    validator = get_validator(subject)
    if not validator:
        return errors
    
    try:
        content = filepath.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        print(f"  Error reading {filepath.name}: {e}")
        return errors
    
    # Split into individual MCQs (separated by ---)
    mcq_blocks = content.split('---')
    
    for i, block in enumerate(mcq_blocks):
        if not block.strip():
            continue
        
        # Validate each block
        block_errors = validator.validate(block)
        if block_errors:
            # Find the question in the block
            lines = block.strip().split('\n')
            question = None
            line_num = None
            for j, line in enumerate(lines):
                if line.strip() and not line.startswith('#') and not line.startswith('-') and not line.startswith('>') and '?' not in line[:5]:
                    question = line.strip()[:100]
                    # Estimate line number
                    line_num = sum(len(b.split('\n')) for b in mcq_blocks[:i]) + j + 1
                    break
            
            for error in block_errors:
                errors.append({
                    'file': filepath.name,
                    'line': line_num or 0,
                    'question': question or '(unknown)',
                    'error': error,
                })
    
    return errors


def main():
    flashcard_dir = Path(r"d:\Obsidian Vault\Academics\BCom\Flashcards\Semester One")
    
    all_errors = []
    
    for filepath in sorted(flashcard_dir.glob("*.md")):
        print(f"Scanning {filepath.name}...", flush=True)
        try:
            errors = scan_flashcard_file(filepath)
            all_errors.extend(errors)
        except Exception as e:
            print(f"  ERROR: {e}")
    
    print(f"\n{'='*60}")
    print(f"TOTAL ERRORS FOUND: {len(all_errors)}")
    print(f"{'='*60}\n")
    
    # Group by file
    from collections import defaultdict
    by_file = defaultdict(list)
    for err in all_errors:
        by_file[err['file']].append(err)
    
    for filename, errors in sorted(by_file.items()):
        print(f"\n## {filename} ({len(errors)} errors)")
        for err in errors:
            print(f"  Line ~{err['line']}: {err['error']}")
            print(f"    Q: {err['question'][:80]}...")


if __name__ == '__main__':
    main()
