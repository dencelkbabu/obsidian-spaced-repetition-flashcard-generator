"""MCQ text cleaning utilities.

This module provides the MCQCleaner class for cleaning and formatting
AI-generated MCQ text output.
"""

import re


class MCQCleaner:
    """Cleans and formats AI-generated MCQ text."""
    
    def clean_wikilinks(self, text: str) -> str:
        """Remove Obsidian wikilink syntax from text.
        
        Args:
            text: Text containing [[wikilinks]]
            
        Returns:
            Text with wikilinks replaced by plain text
        """
        if not text:
            return ""
        return re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', r'\1', text)

    def clean_ai_output(self, text: str) -> str:
        """Clean and format AI-generated MCQ output.
        
        Performs comprehensive cleaning including:
        - Removing meta-commentary
        - Normalizing formatting
        - Ensuring proper question/answer structure
        - Compacting whitespace
        
        Args:
            text: Raw AI output text
            
        Returns:
            Cleaned and formatted MCQ text
        """
        if not text:
            return ""
        
        # Basic cleanup
        text = text.replace('[', '').replace(']', '')
        text = re.sub(r'(?i)(according to|based on) the (text|provided|summary).*?[\.,]\s*', '', text)
        text = re.sub(r'(?m)^(Verification:|Here are|I have generated|I will generate).*$', '', text)
        text = re.sub(r'(?s)\*\*Verification:\*\*.*?(?=\n\d+\.|$)', '', text)
        text = re.sub(r'(?i)Here are .*?questions.*?:', '', text)
        text = re.sub(r'(?m)^\*\*Question.*?\*\*.*$', '', text)
        text = re.sub(r'(?m)^Question\s+\d+[:.]\s*', '', text)
        text = re.sub(r'(?m)^Note:.*$', '', text)
        
        # Formatting fixes
        text = re.sub(r'(?m)^(\d+)\)', r'\1.', text)  # 1) -> 1.
        text = re.sub(r'(?m)^(\d+\.\s*)(?:\*\*|)\s*\.+\s*', r'\1', text)  # 1. .. -> 1.
        text = re.sub(r'(?m)^\s*\.+\s*', '', text)  # .. lines
        text = re.sub(r'(?m)^(\*\*Answer:\*\*\s*)(\d+)[\\.)]', r'\1\2) ', text)  # Answer: 2. -> Answer: 2)
        
        # Ensure '?' separator and blank line removal (Compacting)
        lines = text.split('\n')
        new_lines = []
        for i, line in enumerate(lines):
            if "**Answer:**" in line:
                # Ensure preceding '?'
                j = len(new_lines) - 1
                while j >= 0 and not new_lines[j].strip():
                    j -= 1
                if j < 0 or "?" not in new_lines[j]:
                    new_lines.append("?  ")
                new_lines.append(line)
            elif "**Explanation:**" in line:
                new_lines.append("> " + line.strip() if not line.strip().startswith(">") else line)
            else:
                new_lines.append(line)
        
        text = '\n'.join(new_lines)
        
        # Remove specific blank lines for compactness
        text = re.sub(r'\n\s*\n(1\.)', r'\n\1', text)
        text = re.sub(r'\n\s*\n(\?)', r'\n\1', text)
        text = re.sub(r'(\?.*?)\n\s*\n(\*\*Answer:)', r'\1\n\2', text)
        text = re.sub(r'(\*\*Answer:.*)\n\s*\n(> \*\*Explanation:)', r'\1\n\2', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Final whitespace check
        final_lines = []
        for line in text.split('\n'):
            if line.strip().startswith('?'):
                final_lines.append("?  ")
                if final_lines and len(final_lines) > 1:
                    prev = final_lines[-2]
                    if prev.strip() and not prev.endswith("  "):
                        final_lines[-2] = prev.rstrip() + "  "
            else:
                final_lines.append(line)
                
        return '\n'.join(final_lines).strip()
