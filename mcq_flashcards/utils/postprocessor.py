"""Post-processing utilities for cleaning up generated flashcard files.

This module provides functions to fix common LLM output inconsistencies
in the generated MCQ markdown files.
"""

import re
from pathlib import Path
from typing import List, Tuple


class FlashcardPostProcessor:
    """Post-processes generated flashcard files to fix formatting inconsistencies."""
    
    def __init__(self):
        """Initialize the post-processor."""
        self.fixes_applied = 0
        self.issues_found = []
    
    def process_file(self, file_path: Path) -> Tuple[int, List[str]]:
        """Process a single flashcard file and fix inconsistencies.
        
        Args:
            file_path: Path to the flashcard markdown file
            
        Returns:
            Tuple of (number of fixes applied, list of issues found)
        """
        self.fixes_applied = 0
        self.issues_found = []
        
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        # Apply all fixes
        content = self._remove_llm_meta_commentary(content)
        content = self._fix_missing_question_separators(content)
        content = self._fix_merged_questions(content)
        content = self._remove_duplicate_separators(content)
        content = self._fix_answer_format(content)
        content = self._normalize_spacing(content)
        
        # Only write if changes were made
        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
        
        return self.fixes_applied, self.issues_found
    
    def _remove_llm_meta_commentary(self, text: str) -> str:
        """Remove LLM meta-commentary like 'Let me know if...' or 'Here are...'
        
        Args:
            text: Input text
            
        Returns:
            Cleaned text
        """
        patterns = [
            r'(?m)^Let me know if .*$',
            r'(?m)^I hope .*$',
            r'(?m)^Please .*$',
            r'(?m)^Feel free .*$',
            r'(?m)^If you .*$',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                self.fixes_applied += len(matches)
                self.issues_found.append(f"Removed meta-commentary: {matches[0][:50]}...")
                text = re.sub(pattern, '', text)
        
        return text
    
    def _fix_missing_question_separators(self, text: str) -> str:
        """Fix missing '?' separator before **Answer:** lines.
        
        Args:
            text: Input text
            
        Returns:
            Fixed text
        """
        # Pattern: option line followed directly by **Answer:** without ?
        pattern = r'(\d+\.\s+.+?)\s*\n(\*\*Answer:\*\*)'
        
        def replacer(match):
            self.fixes_applied += 1
            self.issues_found.append("Added missing '?' separator")
            return f"{match.group(1)}  \n?  \n{match.group(2)}"
        
        return re.sub(pattern, replacer, text)
    
    def _fix_merged_questions(self, text: str) -> str:
        """Fix questions that are merged without proper separation.
        
        Args:
            text: Input text
            
        Returns:
            Fixed text
        """
        # Pattern: **Answer:** followed by another question number without proper spacing
        pattern = r'(\*\*Answer:\*\* \d+\).*?\n\*\*Explanation:\*\*.*?)\n(\d+\.\s+)'
        
        def replacer(match):
            self.fixes_applied += 1
            self.issues_found.append("Fixed merged questions")
            return f"{match.group(1)}\n\n{match.group(2)}"
        
        return re.sub(pattern, replacer, text)
    
    def _remove_duplicate_separators(self, text: str) -> str:
        """Remove duplicate '?' separators.
        
        Args:
            text: Input text
            
        Returns:
            Fixed text
        """
        # Pattern: Multiple ? lines in a row
        pattern = r'\?  \n\?  \n'
        
        count = text.count(pattern)
        if count > 0:
            self.fixes_applied += count
            self.issues_found.append(f"Removed {count} duplicate '?' separators")
            text = re.sub(pattern, '?  \n', text)
        
        return text
    
    def _fix_answer_format(self, text: str) -> str:
        """Fix answer format inconsistencies.
        
        Args:
            text: Input text
            
        Returns:
            Fixed text
        """
        # Pattern: **Answer:** followed by just number without )
        pattern = r'\*\*Answer:\*\*\s+(\d+)\s+([A-Z])'
        
        def replacer(match):
            self.fixes_applied += 1
            self.issues_found.append("Fixed answer format")
            return f"**Answer:** {match.group(1)}) {match.group(2)}"
        
        return re.sub(pattern, replacer, text)
    
    def _normalize_spacing(self, text: str) -> str:
        """Normalize spacing issues.
        
        Args:
            text: Input text
            
        Returns:
            Fixed text
        """
        # Remove excessive blank lines (more than 2 consecutive)
        pattern = r'\n{4,}'
        count = len(re.findall(pattern, text))
        if count > 0:
            self.fixes_applied += count
            self.issues_found.append(f"Normalized {count} excessive blank lines")
            text = re.sub(pattern, '\n\n', text)
        
        return text


def post_process_flashcards(output_dir: Path, verbose: bool = True) -> dict:
    """Post-process all flashcard files in the output directory.
    
    Args:
        output_dir: Directory containing flashcard markdown files
        verbose: Whether to print progress information
        
    Returns:
        Dictionary with processing statistics
    """
    processor = FlashcardPostProcessor()
    stats = {
        'files_processed': 0,
        'total_fixes': 0,
        'files_with_issues': 0,
        'issues_by_file': {}
    }
    
    for file_path in output_dir.glob("*_MCQ*.md"):
        fixes, issues = processor.process_file(file_path)
        stats['files_processed'] += 1
        stats['total_fixes'] += fixes
        
        if fixes > 0:
            stats['files_with_issues'] += 1
            stats['issues_by_file'][file_path.name] = {
                'fixes': fixes,
                'issues': issues
            }
            
            if verbose:
                print(f"✓ {file_path.name}: {fixes} fixes applied")
                for issue in issues[:3]:  # Show first 3 issues
                    print(f"  - {issue}")
    
    if verbose:
        print(f"\n📊 Post-Processing Summary:")
        print(f"   Files processed: {stats['files_processed']}")
        print(f"   Files with issues: {stats['files_with_issues']}")
        print(f"   Total fixes applied: {stats['total_fixes']}")
    
    return stats
