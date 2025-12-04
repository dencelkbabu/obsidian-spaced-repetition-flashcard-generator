"""Auto-tuning system for dynamic request throttling.

This module provides the AutoTuner class which monitors system health
(GPU utilization, latency, error rates) and dynamically adjusts
request throttling to optimize performance.
"""

import subprocess
import threading
import time
from typing import List

from mcq_flashcards.core.config import GPU_UTIL_HIGH, GPU_UTIL_LOW, LATENCY_TARGET


class AutoTuner:
    """Monitors system health and recommends request throttling."""
    
    def __init__(self):
        """Initialize the auto-tuner with empty metrics."""
        self.latencies: List[float] = []
        self.errors: List[float] = []
        self.lock = threading.Lock()

    def add_latency(self, t: float):
        """Record a request latency.
        
        Args:
            t: Latency in seconds
        """
        with self.lock:
            self.latencies.append(t)
            if len(self.latencies) > 50:
                self.latencies.pop(0)

    def add_error(self):
        """Record an error occurrence with timestamp."""
        with self.lock:
            self.errors.append(time.time())
            if len(self.errors) > 50:
                self.errors.pop(0)

    def avg_latency(self) -> float:
        """Calculate average latency from recent requests.
        
        Returns:
            Average latency in seconds, or 0.0 if no data
        """
        with self.lock:
            return sum(self.latencies) / len(self.latencies) if self.latencies else 0.0

    def error_rate(self) -> int:
        """Calculate error rate in the last minute.
        
        Returns:
            Number of errors in the last 60 seconds
        """
        with self.lock:
            now = time.time()
            self.errors = [e for e in self.errors if now - e < 60]
            return len(self.errors)

    def get_gpu_util(self) -> int:
        """Query nvidia-smi for GPU utilization.
        
        Returns:
            GPU utilization percentage (0-100), or 50 if unavailable
        """
        try:
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
        """Return a multiplier for the delay based on system health.
        
        Analyzes GPU utilization, latency, and error rates to determine
        optimal throttling multiplier.
        
        Returns:
            Throttle multiplier (0.7 to 2.0+)
        """
        gpu = self.get_gpu_util()
        avg_lat = self.avg_latency()
        err_rate = self.error_rate()

        throttle = 1.0

        # GPU Overload Protection
        if gpu > GPU_UTIL_HIGH:
            throttle *= 2.0
        elif gpu < GPU_UTIL_LOW and throttle > 1.0:
            throttle *= 0.7  # Relax if cool

        # Latency Check
        if avg_lat > LATENCY_TARGET:
            throttle *= 1.5

        # Error Spike Check
        if err_rate > 5:
            throttle *= 2.0

        return throttle


# Global singleton instance
AUTOTUNER = AutoTuner()
