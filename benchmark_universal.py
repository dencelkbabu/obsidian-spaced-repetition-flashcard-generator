"""Universal Benchmark Script for MCQ Flashcard Generator

Works on both old versions (v2.6) and new versions (v3.24.0+).
Automatically detects version and uses appropriate command.

Usage:
    python benchmark_universal.py --version v2.6
    python benchmark_universal.py --version v3.24.0
"""

import argparse
import json
import subprocess
import sys
import time
import os
from datetime import datetime
from pathlib import Path

# Try to import psutil, but make it optional
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("⚠️  psutil not installed. Memory tracking disabled.")
    print("   Install with: pip install psutil")

class UniversalBenchmark:
    """Universal benchmark that works across versions."""
    
    def __init__(self, version_label: str):
        self.version_label = version_label
        self.results = {
            "version": version_label,
            "timestamp": datetime.now().isoformat(),
            "test_case": "COMM1001 Week 02",
            "command": "TBD",
            "metrics": {},
            "system_info": self._get_system_info()
        }
        self.start_time = None
        self.has_dev_mode = self._check_dev_mode()
    
    def _get_system_info(self):
        """Collect system information."""
        info = {
            "python_version": sys.version,
            "platform": os.name
        }
        if HAS_PSUTIL:
            info["cpu_count"] = psutil.cpu_count()
            info["total_memory_gb"] = round(psutil.virtual_memory().total / (1024**3), 2)
        return info
    
    def _check_dev_mode(self) -> bool:
        """Check if this version has dev mode (-d flag)."""
        try:
            result = subprocess.run(
                [sys.executable, "mcq_flashcards.py", "--help"],
                capture_output=True,
                text=True,
                timeout=5,
                encoding='utf-8',
                errors='replace'
            )
            return "-d" in result.stdout or "--dev" in result.stdout
        except:
            return False
    
    def clear_cache(self):
        """Clear cache directory."""
        cache_dir = Path("_cache")
        if cache_dir.exists():
            # Clear files inside cache dir
            for item in cache_dir.glob("*"):
                try:
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        import shutil
                        shutil.rmtree(item)
                except Exception as e:
                    print(f"⚠️  Could not delete {item}: {e}")
            print(f"✅ Cache cleared: {cache_dir}")
        else:
            cache_dir.mkdir(exist_ok=True)
            print(f"✅ Cache directory created: {cache_dir}")
    
    def run_benchmark(self):
        """Run the benchmark test."""
        print(f"\n{'='*60}")
        print(f"🚀 BENCHMARK: {self.version_label}")
        print(f"{'='*60}")
        print(f"Test: COMM1001 Week 02")
        
        # Determine command based on version
        if self.has_dev_mode:
            command = ["python", "mcq_flashcards.py", "-d", "COMM1001", "2"]
            self.results["command"] = "python mcq_flashcards.py -d COMM1001 2"
            print(f"Mode: Dev Mode (non-interactive)")
        else:
            # Old version - use automated input
            command = ["python", "mcq_flashcards.py"]
            self.results["command"] = "python mcq_flashcards.py (interactive with automated input)"
            print(f"Mode: Interactive (automated)")
        
        print(f"Command: {self.results['command']}")
        print(f"{'='*60}\n")
        
        # Clear cache
        self.clear_cache()
        
        # Start monitoring
        self.start_time = time.time()
        start_memory = psutil.virtual_memory().used / (1024**2) if HAS_PSUTIL else 0
        
        # Run command
        try:
            # Set UTF-8 encoding to handle emojis
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            if self.has_dev_mode:
                # Dev mode - direct execution
                result = subprocess.run(
                    [sys.executable, "mcq_flashcards.py", "-d", "COMM1001", "2"],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=600,
                    env=env
                )
            else:
                # Interactive mode - provide automated inputs
                # Format: Subject + Week + Overwrite confirmation
                inputs = "COMM1001\n2\ny\n"
                result = subprocess.run(
                    [sys.executable, "mcq_flashcards.py"],
                    input=inputs,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=600,
                    env=env
                )
            
            # End monitoring
            end_time = time.time()
            end_memory = psutil.virtual_memory().used / (1024**2) if HAS_PSUTIL else 0
            
            # Collect metrics
            duration = end_time - self.start_time
            
            self.results["metrics"] = {
                "duration_seconds": round(duration, 2),
                "duration_minutes": round(duration / 60, 2),
                "exit_code": result.returncode,
                "stdout_lines": len(result.stdout.split('\n')),
                "stderr_lines": len(result.stderr.split('\n'))
            }
            
            if HAS_PSUTIL:
                self.results["metrics"]["memory_delta_mb"] = round(end_memory - start_memory, 2)
            
            # Parse output for additional metrics
            self._parse_output(result.stdout)
            
            # Check output file
            self._check_output_file()
            
            # Print results
            self._print_results()
            
            return True
            
        except subprocess.TimeoutExpired:
            print("❌ Benchmark timed out (10 minutes)")
            self.results["metrics"]["error"] = "Timeout"
            return False
        except Exception as e:
            print(f"❌ Benchmark failed: {e}")
            self.results["metrics"]["error"] = str(e)
            return False
    
    def _parse_output(self, stdout: str):
        """Parse stdout for metrics."""
        metrics = self.results["metrics"]
        
        for line in stdout.split('\n'):
            if "Files:" in line:
                try:
                    parts = line.split("Files:")[1].strip().split("/")
                    metrics["files_processed"] = int(parts[0])
                except:
                    pass
            
            if "Concepts:" in line:
                try:
                    parts = line.split("Concepts:")[1].strip().split("/")
                    metrics["concepts_processed"] = int(parts[0])
                except:
                    pass
            
            if "Success:" in line:
                try:
                    parts = line.split("Success:")[1].split("|")[0].strip()
                    metrics["mcqs_generated"] = int(parts)
                except:
                    pass
            
            if "Cache Hits:" in line:
                try:
                    parts = line.split("Cache Hits:")[1].strip()
                    metrics["cache_hits"] = int(parts)
                except:
                    pass
            
            if "Q/min" in line or "questions/min" in line:
                try:
                    # Try to extract number before Q/min
                    import re
                    match = re.search(r'(\d+\.?\d*)\s*Q/min', line)
                    if match:
                        metrics["questions_per_minute"] = float(match.group(1))
                except:
                    pass
    
    def _check_output_file(self):
        """Check if output file was created and get stats."""
        # Try multiple possible output locations
        possible_paths = [
            Path("tests/_dev/COMM1001_W02_MCQ_dev.md"),  # v3.2.0+
            Path("D:/Obsidian Vault/Academics/BCom/Flashcards/COMM1001_W02_MCQ.md"),  # v2.6
            Path("D:/Obsidian Vault/Academics/BCom/Flashcards/_dev/COMM1001_W02_MCQ_dev.md"),  # v3.0-3.1
        ]
        
        output_file = None
        for path in possible_paths:
            if path.exists():
                output_file = path
                break
        
        if output_file and output_file.exists():
            stats = output_file.stat()
            content = output_file.read_text(encoding='utf-8')
            
            self.results["output"] = {
                "file_exists": True,
                "file_path": str(output_file),
                "file_size_bytes": stats.st_size,
                "file_size_kb": round(stats.st_size / 1024, 2),
                "line_count": len(content.split('\n')),
                "char_count": len(content)
            }
            
            # Count MCQs
            mcq_count = content.count("**Answer:**")
            self.results["output"]["mcq_count"] = mcq_count
        else:
            self.results["output"] = {
                "file_exists": False,
                "error": "Output file not found in any expected location"
            }
    
    def _print_results(self):
        """Print benchmark results."""
        print(f"\n{'='*60}")
        print(f"📊 BENCHMARK RESULTS: {self.version_label}")
        print(f"{'='*60}")
        
        metrics = self.results["metrics"]
        output = self.results.get("output", {})
        
        print(f"⏱️  Duration: {metrics.get('duration_seconds', 0)}s ({metrics.get('duration_minutes', 0):.1f} min)")
        print(f"📝 MCQs Generated: {metrics.get('mcqs_generated', output.get('mcq_count', 'N/A'))}")
        print(f"📁 Files Processed: {metrics.get('files_processed', 'N/A')}")
        print(f"🎯 Concepts: {metrics.get('concepts_processed', 'N/A')}")
        print(f"💾 Cache Hits: {metrics.get('cache_hits', 'N/A')}")
        print(f"⚡ Speed: {metrics.get('questions_per_minute', 'N/A')} Q/min")
        if HAS_PSUTIL:
            print(f"💻 Memory Delta: {metrics.get('memory_delta_mb', 'N/A')} MB")
        print(f"📄 Output Size: {output.get('file_size_kb', 'N/A')} KB")
        print(f"📂 Output Path: {output.get('file_path', 'N/A')}")
        print(f"{'='*60}\n")
    
    def save_results(self):
        """Save results to JSON file."""
        filename = f"benchmark_results_{self.version_label}.json"
        output_dir = Path("_benchmark_data")
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / filename
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved to: {output_file}")
        return output_file


def main():
    parser = argparse.ArgumentParser(description="Universal Performance Benchmark Tool")
    parser.add_argument("--version", required=True, 
                       help="Version label (e.g., 'v2.6', 'v3.24.0')")
    
    args = parser.parse_args()
    
    # Run benchmark
    benchmark = UniversalBenchmark(args.version)
    success = benchmark.run_benchmark()
    
    if success:
        benchmark.save_results()
        print("\n✅ Benchmark completed successfully!")
        return 0
    else:
        print("\n❌ Benchmark failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
