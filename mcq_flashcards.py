import os
import requests
import re
import time
import logging
import hashlib
import pickle
import threading
from pathlib import Path
from datetime import datetime
from functools import wraps
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import yaml
from tqdm import tqdm

# --- CONFIGURATION ---
SCRIPT_DIR = Path(__file__).resolve().parent
VAULT_ROOT = SCRIPT_DIR.parent
ACADEMICS_ROOT = VAULT_ROOT / "Academics"
CLASS_ROOT = ACADEMICS_ROOT / r"BCom\Semester One"
CONCEPT_SOURCE = ACADEMICS_ROOT / "Concepts"
OUTPUT_DIR = ACADEMICS_ROOT / r"BCom\Flashcards"
CACHE_DIR = SCRIPT_DIR / "_cache"

START_WEEK = 1
END_WEEK = 12
MODEL = "llama3:8b"
LIMIT = 1  # Set to 0 to run all
RATE_LIMIT_DELAY = 0.5
TEMPERATURE = 0.0
MAX_TOKENS = 1500
TOP_P = 0.9
MAX_WORKERS = 4
# ---------------------

@dataclass
class ProcessingStats:
    total_files: int = 0
    processed_files: int = 0
    successful_cards: int = 0
    failed_cards: int = 0
    cache_hits: int = 0
    total_concepts: int = 0
    processed_concepts: int = 0

stats = ProcessingStats()
file_lock = threading.Lock()

def get_subject_persona(subject_code):
    code = subject_code.upper()
    if "ACCT" in code:
        return "Strict Accounting Professor", "Focus on precise accounting standards (IFRS/GAAP). Distinguish clearly between Bookkeeping and Accounting."
    elif "COMM" in code:
        return "Communication Expert", "Focus on business etiquette, theory, and precise terminology."
    elif "MATH" in code:
        return "Mathematics Professor", "Focus on logic, formulas, and absolute precision."
    elif "ECON" in code:
        return "Economics Professor", "Focus on micro/macro theories and standard economic definitions."
    else:
        return "University Professor", "Focus on academic accuracy."

def check_ollama_status():
    """Check if Ollama is running and reachable"""
    try:
        response = requests.get("http://localhost:11434", timeout=2)
        if response.status_code == 200:
            print(f"✅ Ollama is running (Model: {MODEL})")
            return True
    except requests.exceptions.ConnectionError:
        pass
    
    print(f"❌ Error: Ollama is not running at http://localhost:11434")
    print(f"   Please start it with 'ollama serve' and try again.")
    return False

def clean_wikilinks(text):
    if not text: return ""
    return re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', r'\1', text)

def clean_ai_output(text):
    if not text: return ""
    
    # 1. Remove square brackets globally
    text = text.replace('[', '').replace(']', '')
    
    # 2. Remove "According to..." phrases
    text = re.sub(r'(?i)(according to|based on) the (text|provided|summary).*?[\.,]\s*', '', text)
    
    # 3. Strip "Verification" sections, conversational filler, and headers
    text = re.sub(r'(?m)^(Verification:|Here are|I have generated|I will generate).*$', '', text)
    text = re.sub(r'(?s)\*\*Verification:\*\*.*?(?=\n\d+\.|$)', '', text)
    text = re.sub(r'(?i)Here are .*?questions.*?:', '', text)
    text = re.sub(r'(?m)^\*\*Question.*?\*\*.*$', '', text) # Remove "**Question X**"
    text = re.sub(r'(?m)^Question\s+\d+[:.]\s*', '', text) # Remove "Question 1:"
    text = re.sub(r'(?m)^Note:.*$', '', text) # Remove "Note: ..." filler
    
    # 4. Standardize Option Numbering (1. 2. 3. 4.)
    # Convert "1)" to "1."
    text = re.sub(r'(?m)^(\d+)\)', r'\1.', text)
    
    # 5. Clean leading artifacts (e.g., "..", "...") from lines
    # Catches "1. .. Text" or "1. **..** Text"
    text = re.sub(r'(?m)^(\d+\.\s*)(?:\*\*|)\s*\.+\s*', r'\1', text)
    # Catches plain lines starting with ..
    text = re.sub(r'(?m)^\s*\.+\s*', '', text)
    
    # 6. Standardize Answer format: "**Answer:** 2) Answer"
    # Ensure Answer line uses "2)" format even if it was "2."
    text = re.sub(r'(?m)^(\*\*Answer:\*\*\s*)(\d+)[\.\)]\s*', r'\1\2) ', text)
    
    # 7. Ensure '?' separator exists before EVERY **Answer:**
    lines = text.split('\n')
    new_lines = []
    for i, line in enumerate(lines):
        if "**Answer:**" in line:
            # Check if previous non-empty line was '?'
            j = len(new_lines) - 1
            while j >= 0 and not new_lines[j].strip():
                j -= 1
            
            if j < 0 or "?" not in new_lines[j]:
                new_lines.append("?  ")
            
            new_lines.append(line)
        elif "**Explanation:**" in line:
            if not line.strip().startswith(">"):
                new_lines.append("> " + line.strip())
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
            
    text = '\n'.join(new_lines)

    # 8. COMPACTING: Remove blank lines in specific places
    # Remove blank line between Question and Option 1
    text = re.sub(r'\n\s*\n(1\.)', r'\n\1', text)
    
    # Remove blank line between Option 4 and ?
    text = re.sub(r'\n\s*\n(\?)', r'\n\1', text)
    
    # Remove blank line between ? and **Answer:**
    text = re.sub(r'(\?.*?)\n\s*\n(\*\*Answer:)', r'\1\n\2', text)
    
    # Remove blank line between **Answer:** and > **Explanation:**
    text = re.sub(r'(\*\*Answer:.*)\n\s*\n(> \*\*Explanation:)', r'\1\n\2', text)
    
    # 9. Clean up multiple newlines (general)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # 10. ENFORCE WHITESPACE REQUIREMENTS (Final Pass)
    lines = text.split('\n')
    final_lines = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        if stripped.startswith('?'):
            # Ensure it's just "?  "
            final_lines.append("?  ")
            
            # Go back and add spaces to the PREVIOUS line if it exists (Option 4)
            if final_lines and len(final_lines) > 1:
                prev_line = final_lines[-2]
                if prev_line.strip() and not prev_line.endswith("  "):
                    final_lines[-2] = prev_line.rstrip() + "  "
        else:
            final_lines.append(line)
            
    text = '\n'.join(final_lines)
    
    return text.strip()

def validate_mcq_format(mcq_text):
    """Validate the generated MCQ against expected format"""
    if not mcq_text or mcq_text.startswith("Error:"):
        return False
    
    # Check for basic structure
    has_question = '?' in mcq_text
    # Check for numbered options (1., 2., etc or 1), 2))
    has_options = any(opt in mcq_text for opt in ['1.', '2.', '1)', '2)'])
    has_answer_tag = "**Answer:**" in mcq_text
    
    return has_question and has_options and has_answer_tag

def extract_summary(file_path):
    """Extract summary section from note file"""
    try:
        content = file_path.read_text(encoding='utf-8')
        
        # Extract Key Concepts section
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
                summary = clean_wikilinks(match.group(1).strip())
                break
        
        # If no summary found, try to use the whole file content (cleaned)
        if not summary:
             summary = clean_wikilinks(content)

        # Extract all wikilinks for concept processing
        links = re.findall(r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', content)
        cleaned_links = {link.split('|')[0] for link in links}
        
        return summary, cleaned_links
    except Exception as e:
        print(f"⚠️  Error reading {file_path}: {e}")
        return None, set()

def get_cache_key(text, model, params):
    """Generate a unique cache key based on input and params"""
    combined = f"{model}_{params}_{text}"
    return CACHE_DIR / f"{hashlib.md5(combined.encode()).hexdigest()}.pkl"

def retry_on_failure(max_retries=3, delay=1, backoff=2):
    """Robust retry decorator with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            mtries, mdelay = max_retries, delay
            while mtries > 1:
                try:
                    result = func(*args, **kwargs)
                    if isinstance(result, str) and result.startswith("Error:"):
                        raise ValueError(result) # Treat API errors as exceptions for retry
                    return result
                except Exception as e:
                    # print(f"   ⚠️  Retry ({max_retries - mtries + 1}/{max_retries}): {e}")
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return func(*args, **kwargs) # Last attempt
        return wrapper
    return decorator

@retry_on_failure(max_retries=3, delay=1)
def query_ollama_mcq(text, source_name, persona, focus):
    # Check Cache
    params = {"temperature": TEMPERATURE, "top_p": TOP_P}
    cache_path = get_cache_key(text, MODEL, str(params))
    
    if cache_path.exists():
        with open(cache_path, "rb") as f:
            stats.cache_hits += 1
            return pickle.load(f)

    # Chain-of-Thought Prompt (Accuracy Focused)
    prompt = f"""
    You are a {persona}. {focus}
    
    TASK: Generate 2 high-quality Multiple Choice Questions (MCQs) based STRICTLY on the text below.
    
    CRITICAL RULES (ACCURACY):
    1. GROUNDING: The correct answer must be EXPLICITLY stated or directly inferred from the provided text. Do not use outside knowledge.
    2. AMBIGUITY CHECK: If a question has multiple potentially correct answers based on general knowledge, but only one is supported by the text, specify "According to the text..." or "In this context...".
    3. DISTRACTORS: Wrong options must be plausible but UNDENIABLY WRONG based on the provided text.
    4. NEGATIVE CONSTRAINT: Do not ask "What type of X is Y?" if the text lists multiple valid types but the options only show one without context.
    
    INSTRUCTIONS (INTERNAL THOUGHT PROCESS):
    1. ANALYZE: Read the text and identify key facts/definitions.
    2. DRAFT: Create a question for a specific fact.
    3. VERIFY: 
       - Is the correct answer UNDENIABLY supported by the text?
       - Are the distractors (wrong options) clearly incorrect?
       - Does the question avoid ambiguity?
    4. EXPLAIN: Write a short explanation for why the answer is correct, citing the text.
    
    OUTPUT INSTRUCTIONS:
    - Output ONLY the final flashcards. 
    - DO NOT output "Question 1", "Question 2", etc. Just the question text.
    - DO NOT output your internal verification steps or conversational filler.
    - Use numbered options (1, 2, 3, 4).
    - The answer line MUST include the full text (e.g., "2) Paris", NOT just "2)").
    
    REQUIRED OUTPUT FORMAT:
    
    Question text here?
    1. Option 1
    2. Option 2
    3. Option 3
    4. Option 4
    ?
    **Answer:** Correct Number) Full Correct Answer Text
    > **Explanation:** Short explanation of why this is the correct answer.
    
    TEXT TO PROCESS:
    {text[:6000]}
    """
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate", 
            json={
                "model": MODEL, 
                "prompt": prompt, 
                "stream": False, 
                "options": {
                    "temperature": TEMPERATURE, 
                    "num_ctx": 8192,
                    "top_p": TOP_P,
                    "max_tokens": MAX_TOKENS
                }
            },
            timeout=90
        )
        
        response.raise_for_status()
        result = response.json()
        
        if 'response' not in result:
            return f"Error: Invalid response format from Ollama"
        
        cleaned_response = clean_ai_output(result['response'])
        
        # Validate the response format
        if not validate_mcq_format(cleaned_response):
            return f"Error: Generated content does not match expected MCQ format"
            
        # Save to Cache
        with open(cache_path, "wb") as f:
            pickle.dump(cleaned_response, f)
            
        return cleaned_response
    except Exception as e:
        return f"Error: {e}"

def append_to_file(filepath, text):
    with file_lock:
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(text + "\n")

def get_target_directories(subject_path):
    """Return list of directories to process (Lectures only)"""
    target_dirs = []
    lecture_types = ["Recorded Lectures", "Live Lectures"]
    
    for folder_name in lecture_types:
        full_path = subject_path / folder_name
        if full_path.exists():
            target_dirs.append(full_path)
            
    return target_dirs

def process_item(args):
    """Worker function for threading"""
    text, name, persona, focus, is_concept = args
    
    if len(text) < 20:
        return None

    cards = query_ollama_mcq(text, name, persona, focus)
    
    if cards and not cards.startswith("Error"):
        if is_concept:
            stats.successful_cards += 1
            return f"### Concept: {name}\n\n{cards}\n\n---\n"
        else:
            stats.successful_cards += 1
            clean_name = name.replace('.md', '')
            return f"### {clean_name}\n\n{cards}\n\n---\n"
    else:
        stats.failed_cards += 1
        return None

def main():
    # Check Ollama Status FIRST
    if not check_ollama_status():
        return

    print(f"\n📂 Available Subjects in {CLASS_ROOT}:")
    try:
        subjects = [d.name for d in CLASS_ROOT.iterdir() if d.is_dir() and d.name != "Flashcards"]
        print(" | ".join(subjects))
    except Exception as e:
        print(f"❌ Error reading subjects directory: {e}")
        return

    target_subject = input("\n🎯 Enter Subject Code: ").strip().upper()
    target_path = CLASS_ROOT / target_subject

    if not target_path.exists():
        print(f"❌ Subject directory not found: {target_path}")
        return

    # Week Selection
    print("\n📅 Week Selection:")
    print("   Enter a specific Week Number (e.g., 1, 2, 5)")
    print("   OR press Enter to process ALL weeks.")
    week_input = input("   Target Week: ").strip()
    
    target_week_num = None
    if week_input:
        try:
            target_week_num = int(week_input)
            print(f"✅ Selected Week: {target_week_num}")
        except ValueError:
            print("❌ Invalid week number. Processing ALL weeks.")
            target_week_num = None
    else:
        print("✅ Processing ALL weeks.")

    persona, focus = get_subject_persona(target_subject)
    print(f"🤖 Persona: {persona}")

    # Determine Output Filename
    if target_week_num:
        output_filename = f"{target_subject}_W{target_week_num:02d}_MCQ.md"
        week_tag = f"W{target_week_num:02d}"
    else:
        output_filename = f"{target_subject}_All_Weeks_MCQ.md"
        week_tag = "All_Weeks"
        
    final_output_path = OUTPUT_DIR / output_filename

    # Check overwrite
    if final_output_path.exists():
        confirm = input(f"⚠️  File {output_filename} already exists. Overwrite? (y/n): ")
        if confirm.lower() != 'y':
            print("Aborted.")
            return

    # Write Header with YAML Frontmatter
    with open(final_output_path, 'w', encoding='utf-8') as f:
        f.write("---\n")
        f.write("tags:\n")
        f.write(f"- flashcard/{target_subject}/{week_tag}\n")
        f.write("---\n")
        f.write(f"## MCQs: {target_subject} - {'Week ' + str(target_week_num) if target_week_num else 'All Weeks'}\n\n")

    # Collect files from targeted directories
    files_to_process = {}
    relevant_concepts = set()
    
    target_dirs = get_target_directories(target_path)
    if not target_dirs:
        print(f"⚠️  No 'Recorded Lectures' or 'Live Lectures' folders found in {target_subject}")
        return

    print(f"\n🔍 Scanning directories: {[d.name for d in target_dirs]}...")
    
    for directory in target_dirs:
        for file_path in directory.rglob("*.md"):
            # Check Week Match
            match = re.search(r'(?:W|Week)\s?0?(\d+)', file_path.name, re.IGNORECASE)
            if match:
                file_week = int(match.group(1))
                
                # Filter logic
                if target_week_num is not None:
                    if file_week == target_week_num:
                        files_to_process[file_path] = file_path.name
                else:
                    # Process all weeks within range
                    if START_WEEK <= file_week <= END_WEEK:
                        files_to_process[file_path] = file_path.name

    stats.total_files = len(files_to_process)
    print(f"✅ Found {stats.total_files} relevant lecture notes.")
    
    if stats.total_files == 0:
        print("❌ No files found matching criteria.")
        return

    # Prepare Lecture Jobs
    files_list = list(files_to_process.items())
    if LIMIT and LIMIT > 0:
        files_list = files_list[:LIMIT]
        print(f"⚠️  Limit set to {LIMIT}. Processing first {LIMIT} files.")

    lecture_jobs = []
    print("\n📝 Extracting summaries...")
    for path, name in tqdm(files_list, desc="Scanning"):
        summary, links = extract_summary(path)
        relevant_concepts.update(links)
        if summary:
            lecture_jobs.append((summary, name, persona, focus, False))

    # Process Lectures (Threaded)
    print(f"\n🚀 Processing {len(lecture_jobs)} lectures with {MAX_WORKERS} workers...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_item, job) for job in lecture_jobs]
        
        for future in tqdm(as_completed(futures), total=len(futures), desc="Generating MCQs"):
            result = future.result()
            if result:
                append_to_file(final_output_path, result)
                stats.processed_files += 1

    # Prepare Concept Jobs
    stats.total_concepts = len(relevant_concepts)
    print(f"\n🔗 Found {stats.total_concepts} linked concepts. Processing...")
    
    concepts_list = list(relevant_concepts)
    if LIMIT and LIMIT > 0:
        concepts_list = concepts_list[:LIMIT]
        print(f"⚠️  Limit set to {LIMIT}. Processing first {LIMIT} concepts.")

    concept_jobs = []
    for concept_name in concepts_list:
        concept_path = CONCEPT_SOURCE / f"{concept_name}.md"
        if concept_path.exists():
            summary, _ = extract_summary(concept_path)
            if summary:
                concept_jobs.append((summary, concept_name, persona, focus, True))

    # Process Concepts (Threaded)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_item, job) for job in concept_jobs]
        
        for future in tqdm(as_completed(futures), total=len(futures), desc="Concepts"):
            result = future.result()
            if result:
                append_to_file(final_output_path, result)
                stats.processed_concepts += 1

    # Final Statistics
    print(f"\n🎉 DONE! Generated {stats.processed_files} lecture cards and {stats.processed_concepts} concept cards.")
    print(f"📁 Output: {output_filename}")
    print("\n📊 Statistics:")
    print(f"   Total Files Scanned: {stats.total_files}")
    print(f"   Total Concepts Found: {stats.total_concepts}")
    print(f"   Successful Generations: {stats.successful_cards}")
    print(f"   Failed Generations: {stats.failed_cards}")
    print(f"   Cache Hits: {stats.cache_hits}")

if __name__ == "__main__":
    main()