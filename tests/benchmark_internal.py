"""
Internal benchmark script using test fixtures and GPU logging.

This script:
1. Sets up a temporary test environment with duplicated fixture files.
2. Runs FlashcardGenerator with 1 worker and 4 workers.
3. Logs GPU utilization to a CSV file during execution.
4. Compares performance and resource usage.
"""

import csv
import shutil
import tempfile
import threading
import time
import sys
import logging
from pathlib import Path
from typing import List, Tuple

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from mcq_flashcards.core.config import Config
from mcq_flashcards.core.generator import FlashcardGenerator
from mcq_flashcards.utils.autotuner import AUTOTUNER

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GPUMonitor:
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.running = False
        self.data: List[Tuple[float, int]] = []
        self.thread = None

    def start(self):
        self.running = True
        self.data = []
        self.thread = threading.Thread(target=self._monitor_loop)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        self._save_data()

    def _monitor_loop(self):
        start_time = time.time()
        while self.running:
            gpu_util = AUTOTUNER.get_gpu_util()
            elapsed = time.time() - start_time
            self.data.append((elapsed, gpu_util))
            time.sleep(0.5)  # Poll every 0.5 seconds

    def _save_data(self):
        with open(self.log_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Time', 'GPU_Util'])
            writer.writerows(self.data)

def setup_test_env(base_dir: Path, num_files: int = 20):
    """Create a temporary test environment with duplicated fixtures."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    lecture_note = fixtures_dir / "sample_lecture_note.md"
    
    # Create structure: Academics/BCom/Semester One/TEST101/Recorded Lectures/W01 - Test
    subject_dir = base_dir / "Academics" / "BCom" / "Semester One" / "TEST101"
    lectures_dir = subject_dir / "Recorded Lectures" / "W01 - Test"
    lectures_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy fixture multiple times
    for i in range(1, num_files + 1):
        shutil.copy(lecture_note, lectures_dir / f"W01 L{i:02d} TEST101 - Topic {i}.md")
        
    return subject_dir

def run_benchmark(workers: int, test_env: Path, output_dir: Path):
    """Run benchmark for a specific worker count."""
    logger.info(f"Starting benchmark with {workers} worker(s)...")
    
    config = Config(
        workers=workers,
        start_week=1,
        end_week=1,
        dev_mode=True
    )
    
    # Setup GPU monitor
    gpu_log = output_dir / f"gpu_log_{workers}_workers.csv"
    monitor = GPUMonitor(gpu_log)
    
    # Initialize generator
    # Note: FlashcardGenerator expects class_root to be the semester directory
    subject_dir = test_env / "Academics" / "BCom" / "Semester One" / "TEST101"
    generator = FlashcardGenerator("TEST101", config, subject_dir.parent, output_dir)
    
    # Run
    monitor.start()
    start_time = time.time()
    try:
        generator.run(target_week=1, limit=0)
    finally:
        monitor.stop()
    duration = time.time() - start_time
    
    # Calculate stats
    avg_gpu = sum(d[1] for d in monitor.data) / len(monitor.data) if monitor.data else 0
    max_gpu = max(d[1] for d in monitor.data) if monitor.data else 0
    
    return {
        'workers': workers,
        'duration': duration,
        'avg_gpu': avg_gpu,
        'max_gpu': max_gpu,
        'throughput': generator.stats.questions_per_minute
    }

def main():
    # Create temp directory for test environment
    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir)
        test_env = setup_test_env(base_dir)
        
        # Setup temp cache
        temp_cache = base_dir / "_cache"
        temp_cache.mkdir()
        
        # Patch CACHE_DIR in generator module
        from mcq_flashcards.core import generator as generator_module
        generator_module.CACHE_DIR = temp_cache
        
        # Output directory for logs and results
        output_dir = Path(__file__).parent / "_benchmark_internal"
        output_dir.mkdir(exist_ok=True)
        
        print(f"Test environment created at {test_env}")
        print(f"Temp cache at {temp_cache}")
        print(f"Logs will be saved to {output_dir.absolute()}")
        
        # Run benchmarks
        # Clear cache before run 1
        for f in temp_cache.glob("*"):
            f.unlink()
        results_1 = run_benchmark(1, base_dir, output_dir)
        
        # Cool down
        logger.info("Cooling down for 5 seconds...")
        time.sleep(5)
        
        # Clear cache before run 2
        for f in temp_cache.glob("*"):
            f.unlink()
        results_4 = run_benchmark(4, base_dir, output_dir)
        
        # Print comparison
        print("\n" + "="*60)
        print("INTERNAL BENCHMARK RESULTS (20 Files)")
        print("="*60)
        print(f"{'Metric':<20} {'1 Worker':<15} {'4 Workers':<15} {'Diff'}")
        print("-" * 60)
        print(f"{'Duration (s)':<20} {results_1['duration']:<15.2f} {results_4['duration']:<15.2f} {results_4['duration'] - results_1['duration']:+.2f}s")
        print(f"{'Throughput (Q/m)':<20} {results_1['throughput']:<15.2f} {results_4['throughput']:<15.2f} {results_4['throughput'] - results_1['throughput']:+.2f}")
        print(f"{'Avg GPU Util (%)':<20} {results_1['avg_gpu']:<15.1f} {results_4['avg_gpu']:<15.1f} {results_4['avg_gpu'] - results_1['avg_gpu']:+.1f}%")
        print(f"{'Max GPU Util (%)':<20} {results_1['max_gpu']:<15} {results_4['max_gpu']:<15} {results_4['max_gpu'] - results_1['max_gpu']:+d}%")
        print("="*60)
        print(f"GPU logs saved to: {output_dir}")

if __name__ == "__main__":
    main()
