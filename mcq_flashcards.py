import argparse
import concurrent.futures
import hashlib
import json
import logging
import pickle
import random
import re
import subprocess
import threading
import time
import traceback
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any

import requests
import yaml
from tqdm import tqdm

# --- CONFIGURATION & CONSTANTS ---
SCRIPT_DIR = Path(__file__).resolve().parent
VAULT_ROOT = SCRIPT_DIR.parent
ACADEMICS_ROOT = VAULT_ROOT / "Academics"
CLASS_ROOT = ACADEMICS_ROOT / r"BCom\Semester One"
CONCEPT_SOURCE = ACADEMICS_ROOT / "Concepts"
OUTPUT_DIR = ACADEMICS_ROOT / r"BCom\Flashcards"

# New Directories for v2.0.0
CACHE_DIR = SCRIPT_DIR / "_cache"
RAW_DIR = SCRIPT_DIR / "_raw_responses"
ERROR_DIR = SCRIPT_DIR / "_errors"

# Ensure directories exist
for d in [CACHE_DIR, RAW_DIR, ERROR_DIR, OUTPUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Default Settings
DEFAULT_MODEL = "llama3:8b"
DEFAULT_WORKERS = 4
MAX_RETRIES = 3
BASE_DELAY = 0.5
MAX_DELAY = 10.0
GPU_UTIL_HIGH = 80
GPU_UTIL_LOW = 35
LATENCY_TARGET = 1.5

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("FlashcardGen")

# --- DATA STRUCTURES ---

@dataclass
class Config:
    model: str = DEFAULT_MODEL
    workers: int = DEFAULT_WORKERS
    temperature: float = 0.0
    top_p: float = 0.9
    max_tokens: int = 1500
    start_week: int = 1
    end_week: int = 12

@dataclass
class ProcessingStats:
    total_files: int = 0
    processed_files: int = 0
    successful_cards: int = 0
    failed_cards: int = 0
    cache_hits: int = 0
    total_concepts: int = 0
    processed_concepts: int = 0
    refine_attempts: int = 0
    refine_success: int = 0

# --- AUTO TUNER ---

class AutoTuner:
    def __init__(self):
        self.latencies: List[float] = []
        self.errors: List[float] = []
        self.lock = threading.Lock()

    def add_latency(self, t: float):
        with self.lock:
            self.latencies.append(t)
            if len(self.latencies) > 50:
                self.latencies.pop(0)

    def add_error(self):
        with self.lock:
            self.errors.append(time.time())
            if len(self.errors) > 50:
                self.errors.pop(0)

    def avg_latency(self) -> float:
        with self.lock:
            return sum(self.latencies) / len(self.latencies) if self.latencies else 0.0

    def error_rate(self) -> int:
        # Errors in last minute
        with self.lock:
            now = time.time()
            self.errors = [e for e in self.errors if now - e < 60]
            return len(self.errors)

    def get_gpu_util(self) -> int:
        """Query nvidia-smi for GPU utilization."""
        try:
            # Run nvidia-smi to get GPU utilization
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=1
            )
            if result.returncode == 0:
                return int(result.stdout.strip().split('\n')[0])
        except Exception:
            pass
        return 50  # Fallback if unavailable

    def recommend_throttle(self) -> float:
        """Return a multiplier for the delay based on system health."""
        gpu = self.get_gpu_util()
        avg_lat = self.avg_latency()
        err_rate = self.error_rate()

        throttle = 1.0

        # GPU Overload Protection
        if gpu > GPU_UTIL_HIGH:
            throttle *= 2.0
        elif gpu < GPU_UTIL_LOW and throttle > 1.0:
            throttle *= 0.7 # Relax if cool

        # Latency Check
        if avg_lat > LATENCY_TARGET:
            throttle *= 1.5

        # Error Spike Check
        if err_rate > 5:
            throttle *= 2.0

        return throttle

AUTOTUNER = AutoTuner()

# --- OLLAMA CLIENT ---

class OllamaClient:
    def __init__(self, config: Config):
        self.config = config
        self.base_url = "http://localhost:11434/api/generate"

    def check_connection(self) -> bool:
        try:
            requests.get("http://localhost:11434", timeout=2)
            return True
        except requests.exceptions.RequestException:
            return False

    def generate(self, prompt: str, worker_state: Dict[str, Any]) -> Optional[Dict]:
        """Generate with exponential backoff and AutoTuner throttling."""
        for attempt in range(MAX_RETRIES):
            start_time = time.time()
            try:
                payload = {
                    "model": self.config.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.config.temperature,
                        "top_p": self.config.top_p,
                        "max_tokens": self.config.max_tokens,
                        "num_ctx": 8192
                    }
                }
                
                response = requests.post(self.base_url, json=payload, timeout=120)
                latency = time.time() - start_time
                AUTOTUNER.add_latency(latency)

                if response.status_code == 200:
                    worker_state["retries"] = 0
                    return response.json()
                
                AUTOTUNER.add_error()

            except Exception as e:
                AUTOTUNER.add_error()
                # Log only if it's the last retry
                if attempt == MAX_RETRIES - 1:
                    logger.debug(f"Request failed: {e}")

            # Backoff Logic
            worker_state["retries"] += 1
            delay = min(worker_state["delay"] * (2 ** worker_state["retries"]), MAX_DELAY)
            throttle = AUTOTUNER.recommend_throttle()
            final_sleep = delay * throttle
            
            time.sleep(final_sleep)

        return None

# --- TEXT PROCESSING ---

class MCQCleaner:
    def clean_wikilinks(self, text: str) -> str:
        if not text: return ""
        return re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', r'\1', text)

    def clean_ai_output(self, text: str) -> str:
        if not text: return ""
        
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
        text = re.sub(r'(?m)^(\d+)\)', r'\1.', text) # 1) -> 1.
        text = re.sub(r'(?m)^(\d+\.\s*)(?:\*\*|)\s*\.+\s*', r'\1', text) # 1. .. -> 1.
        text = re.sub(r'(?m)^\s*\.+\s*', '', text) # .. lines
        text = re.sub(r'(?m)^(\*\*Answer:\*\*\s*)(\d+)[\.\)]\s*', r'\1\2) ', text) # Answer: 2. -> Answer: 2)
        
        # Ensure '?' separator and blank line removal (Compacting)
        lines = text.split('\n')
        new_lines = []
        for i, line in enumerate(lines):
            if "**Answer:**" in line:
                # Ensure preceding '?'
                j = len(new_lines) - 1
                while j >= 0 and not new_lines[j].strip(): j -= 1
                if j < 0 or "?" not in new_lines[j]: new_lines.append("?  ")
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

class MCQValidator:
    def validate(self, text: str) -> bool:
        if not text or text.startswith("Error:"): return False
        has_question = '?' in text
        has_options = any(opt in text for opt in ['1.', '2.', '1)', '2)'])
        has_answer = "**Answer:**" in text
        return has_question and has_options and has_answer

# --- MAIN GENERATOR ---

class FlashcardGenerator:
    def __init__(self, subject: str, config: Config):
        self.subject = subject.upper()
        self.config = config
        self.client = OllamaClient(config)
        self.cleaner = MCQCleaner()
        self.validator = MCQValidator()
        self.stats = ProcessingStats()
        self.file_lock = threading.Lock()
        self.stats_lock = threading.Lock()
        
        self.subject_path = CLASS_ROOT / self.subject
        self.persona, self.focus = self._get_persona()

    def _get_persona(self) -> Tuple[str, str]:
        if "ACCT" in self.subject:
            return "Strict Accounting Professor", "Focus on precise accounting standards (IFRS/GAAP). Distinguish clearly between Bookkeeping and Accounting."
        elif "COMM" in self.subject:
            return "Communication Expert", "Focus on business etiquette, theory, and precise terminology."
        elif "MATH" in self.subject:
            return "Mathematics Professor", "Focus on logic, formulas, and absolute precision."
        elif "ECON" in self.subject:
            return "Economics Professor", "Focus on micro/macro theories and standard economic definitions."
        return "University Professor", "Focus on academic accuracy."

    def get_cache_key(self, text: str) -> Path:
        combined = f"{self.config.model}_{text}"
        return CACHE_DIR / f"{hashlib.md5(combined.encode()).hexdigest()}.pkl"

    def _save_raw_log(self, name: str, data: Any, suffix: str = ""):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{name}{suffix}.json"
            clean_name = re.sub(r'[\\/*?:"<>|]', "", filename) # Sanitize
            with open(RAW_DIR / clean_name, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Failed to save raw log: {e}")

    def _save_error_log(self, name: str, error: str, context: str):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ERROR_{timestamp}_{name}.txt"
            clean_name = re.sub(r'[\\/*?:"<>|]', "", filename)
            with open(ERROR_DIR / clean_name, 'w', encoding='utf-8') as f:
                f.write(f"Error: {error}\n\nContext:\n{context}")
        except Exception:
            pass

    def generate_single(self, text: str, name: str) -> Optional[str]:
        # Check Cache
        cache_path = self.get_cache_key(text)
        if cache_path.exists():
            try:
                with open(cache_path, "rb") as f:
                    with self.stats_lock:
                        self.stats.cache_hits += 1
                    return pickle.load(f)
            except Exception:
                pass # Corrupt cache, ignore

        # Prompt Construction
        prompt = f"""
        You are a {self.persona}. {self.focus}
        TASK: Generate 2 high-quality Multiple Choice Questions (MCQs) based STRICTLY on the text below.
        
        CRITICAL RULES:
        1. GROUNDING: Answer must be EXPLICITLY in the text.
        2. DISTRACTORS: Plausible but undeniably wrong.
        3. FORMAT: Use the EXACT format below.
        
        REQUIRED OUTPUT FORMAT:
        Question text here?
        1. Option 1
        2. Option 2
        3. Option 3
        4. Option 4
        ?
        **Answer:** Correct Number) Full Correct Answer Text
        > **Explanation:** Short explanation.

        TEXT TO PROCESS:
        {text[:6000]}
        """

        worker_state = {"delay": BASE_DELAY + random.uniform(0, 0.2), "retries": 0}
        
        # 1. Initial Generation
        response = self.client.generate(prompt, worker_state)
        if not response or 'response' not in response:
            return None

        self._save_raw_log(name, response, "_raw")
        cleaned_text = self.cleaner.clean_ai_output(response['response'])

        # 2. Validation & Refine Pass
        if not self.validator.validate(cleaned_text):
            with self.stats_lock:
                self.stats.refine_attempts += 1
            logger.info(f"⚠️  Invalid format for {name}. Attempting Self-Correction...")
            
            refine_prompt = f"""
            The previous output did not match the required MCQ format. 
            Please REFORMAT the following content to match the exact format required.
            
            CONTENT TO FIX:
            {cleaned_text}
            
            REQUIRED FORMAT:
            Question?
            1. Opt1
            2. Opt2
            3. Opt3
            4. Opt4
            ?
            **Answer:** 1) Answer
            > **Explanation:** Text
            """
            
            refine_response = self.client.generate(refine_prompt, worker_state)
            if refine_response and 'response' in refine_response:
                self._save_raw_log(name, refine_response, "_refine")
                cleaned_refine = self.cleaner.clean_ai_output(refine_response['response'])
                
                if self.validator.validate(cleaned_refine):
                    with self.stats_lock:
                        self.stats.refine_success += 1
                    cleaned_text = cleaned_refine # Success!
                else:
                    self._save_error_log(name, "Validation Failed after Refine", cleaned_refine)
                    return None
            else:
                return None

        # Save to Cache
        with open(cache_path, "wb") as f:
            pickle.dump(cleaned_text, f)
            
        return cleaned_text

    def process_item(self, args) -> Optional[str]:
        text, name, is_concept = args
        if len(text) < 20: return None

        try:
            result = self.generate_single(text, name)
            if result:
                with self.stats_lock:
                    self.stats.successful_cards += 1
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
            
            if not summary: summary = self.cleaner.clean_wikilinks(content)
            
            links = re.findall(r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', content)
            cleaned_links = {link.split('|')[0] for link in links}
            return summary, cleaned_links
        except Exception:
            return None, set()

    def run(self, target_week: Optional[int], limit: int = 0):
        if not self.client.check_connection():
            print("❌ Ollama not reachable. Start with 'ollama serve'.")
            return

        # Setup Output
        if target_week:
            out_name = f"{self.subject}_W{target_week:02d}_MCQ.md"
            tag = f"W{target_week:02d}"
        else:
            out_name = f"{self.subject}_All_Weeks_MCQ.md"
            tag = "All_Weeks"
            
        out_path = OUTPUT_DIR / out_name
        
        # Interactive Overwrite Check
        if out_path.exists():
            if input(f"⚠️  {out_name} exists. Overwrite? (y/n): ").lower() != 'y':
                print("Aborted.")
                return

        # Write Header
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(f"---\ntags:\n- flashcard/{self.subject}/{tag}\n---\n")
            f.write(f"## MCQs: {self.subject} - {tag}\n\n")

        # Collect Jobs
        files_map = {}
        concepts_set = set()
        
        target_dirs = [self.subject_path / d for d in ["Recorded Lectures", "Live Lectures"] if (self.subject_path / d).exists()]
        
        print(f"\n🔍 Scanning {self.subject}...")
        for d in target_dirs:
            for p in d.rglob("*.md"):
                match = re.search(r'(?:W|Week)\s?0?(\d+)', p.name, re.IGNORECASE)
                if match:
                    wk = int(match.group(1))
                    if target_week and wk != target_week: continue
                    if not target_week and not (self.config.start_week <= wk <= self.config.end_week): continue
                    files_map[p] = p.name

        self.stats.total_files = len(files_map)
        if self.stats.total_files == 0:
            print("❌ No files found.")
            return

        # Prepare Lecture Jobs
        lecture_jobs = []
        items = list(files_map.items())
        if limit > 0: items = items[:limit]
        
        print("📝 Extracting content...")
        for p, name in tqdm(items):
            summary, links = self.extract_summary(p)
            concepts_set.update(links)
            if summary:
                lecture_jobs.append((summary, name, False))

        # Prepare Concept Jobs
        concept_jobs = []
        self.stats.total_concepts = len(concepts_set)
        c_list = list(concepts_set)
        if limit > 0: c_list = c_list[:limit]
        
        for c in c_list:
            cp = CONCEPT_SOURCE / f"{c}.md"
            if cp.exists():
                s, _ = self.extract_summary(cp)
                if s: concept_jobs.append((s, c, True))

        # Execute
        all_jobs = lecture_jobs + concept_jobs
        print(f"\n🚀 Processing {len(all_jobs)} items with {self.config.workers} workers...")
        print(f"   (AutoTuner Active: Monitoring GPU & Errors)")

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.workers) as executor:
            futures = [executor.submit(self.process_item, job) for job in all_jobs]
            
            for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Generating"):
                result = future.result()
                if result:
                    with self.file_lock:
                        with open(out_path, 'a', encoding='utf-8') as f:
                            f.write(result)

        # Final Report
        print(f"\n🎉 DONE! Output: {out_name}")
        print(f"📊 Statistics:")
        print(f"   Files: {self.stats.processed_files}/{self.stats.total_files}")
        print(f"   Concepts: {self.stats.processed_concepts}/{self.stats.total_concepts}")
        print(f"   Success: {self.stats.successful_cards} | Failed: {self.stats.failed_cards}")
        print(f"   Cache Hits: {self.stats.cache_hits}")
        print(f"   Self-Corrections: {self.stats.refine_success}/{self.stats.refine_attempts}")

# --- CLI ENTRY POINT ---

def main():
    print("⚡ Flashcard Generator v2.0.0 (AutoTuner + Refine)")
    
    # Check Ollama First
    try:
        requests.get("http://localhost:11434", timeout=1)
    except:
        print("❌ Error: Ollama is not running.")
        return

    # Interactive Inputs
    print(f"\n📂 Available Subjects in {CLASS_ROOT}:")
    try:
        subjects = [d.name for d in CLASS_ROOT.iterdir() if d.is_dir() and d.name != "Flashcards"]
        print(" | ".join(subjects))
    except Exception:
        print("❌ Error reading subjects.")
        return

    subj = input("\n🎯 Enter Subject Code: ").strip().upper()
    if not (CLASS_ROOT / subj).exists():
        print("❌ Invalid subject.")
        return

    week_in = input("📅 Enter Week (or Enter for All): ").strip()
    week = int(week_in) if week_in.isdigit() else None

    # Run
    cfg = Config()
    gen = FlashcardGenerator(subj, cfg)
    gen.run(week)

if __name__ == "__main__":
    main()