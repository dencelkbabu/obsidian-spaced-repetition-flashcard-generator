"""Unit tests for AutoTuner functionality.

These tests verify that the AutoTuner correctly monitors system health
and recommends appropriate throttling.
"""

import unittest
from pathlib import Path
import sys
import time
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcq_flashcards.utils.autotuner import AutoTuner


class TestAutoTuner(unittest.TestCase):
    """Test AutoTuner logic."""
    
    def setUp(self):
        """Create a fresh AutoTuner instance for each test."""
        self.tuner = AutoTuner()
    
    def test_add_latency(self):
        """Test that latencies are tracked correctly."""
        self.tuner.add_latency(1.0)
        self.tuner.add_latency(2.0)
        self.tuner.add_latency(3.0)
        
        avg = self.tuner.avg_latency()
        self.assertEqual(avg, 2.0,
                        "Average latency should be 2.0")
    
    def test_latency_history_limit(self):
        """Test that latency history is capped at MAX_METRICS_HISTORY."""
        # Add more than MAX_METRICS_HISTORY items
        for i in range(60):
            self.tuner.add_latency(float(i))
        
        # Should only keep last 50 (MAX_METRICS_HISTORY)
        self.assertEqual(len(self.tuner.latencies), 50,
                        "Should cap latency history at 50")
    
    def test_add_error(self):
        """Test that errors are tracked with timestamps."""
        self.tuner.add_error()
        self.tuner.add_error()
        
        self.assertEqual(len(self.tuner.errors), 2,
                        "Should track 2 errors")
    
    def test_error_rate_recent_only(self):
        """Test that error rate only counts recent errors (last 60s)."""
        # Add old error (simulated by manually setting timestamp)
        old_time = time.time() - 120  # 2 minutes ago
        self.tuner.errors.append(old_time)
        
        # Add recent error
        self.tuner.add_error()
        
        # Error rate should only count recent error
        rate = self.tuner.error_rate()
        self.assertEqual(rate, 1,
                        "Should only count errors from last 60 seconds")
    
    def test_avg_latency_empty(self):
        """Test that avg_latency returns 0.0 when no data."""
        avg = self.tuner.avg_latency()
        self.assertEqual(avg, 0.0,
                        "Should return 0.0 when no latency data")
    
    @patch('subprocess.run')
    def test_get_gpu_util_success(self, mock_run):
        """Test GPU utilization query when nvidia-smi succeeds."""
        # Mock successful nvidia-smi response
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "75\n"
        mock_run.return_value = mock_result
        
        util = self.tuner.get_gpu_util()
        self.assertEqual(util, 75,
                        "Should return GPU utilization from nvidia-smi")
    
    @patch('subprocess.run')
    def test_get_gpu_util_failure(self, mock_run):
        """Test GPU utilization fallback when nvidia-smi fails."""
        # Mock failed nvidia-smi
        mock_run.side_effect = Exception("nvidia-smi not found")
        
        util = self.tuner.get_gpu_util()
        self.assertEqual(util, 50,
                        "Should return fallback value of 50 when nvidia-smi fails")
    
    @patch.object(AutoTuner, 'get_gpu_util')
    def test_throttle_high_gpu(self, mock_gpu):
        """Test that high GPU utilization increases throttle."""
        mock_gpu.return_value = 85  # Above GPU_UTIL_HIGH (80)
        
        throttle = self.tuner.recommend_throttle()
        self.assertGreater(throttle, 1.0,
                          "High GPU should increase throttle")
    
    @patch.object(AutoTuner, 'get_gpu_util')
    def test_throttle_low_gpu(self, mock_gpu):
        """Test that low GPU utilization decreases throttle."""
        mock_gpu.return_value = 30  # Below GPU_UTIL_LOW (35)
        
        throttle = self.tuner.recommend_throttle()
        self.assertLessEqual(throttle, 1.0,
                            "Low GPU should decrease or maintain throttle")
    
    @patch.object(AutoTuner, 'get_gpu_util')
    def test_throttle_high_latency(self, mock_gpu):
        """Test that high latency increases throttle."""
        mock_gpu.return_value = 50  # Normal GPU
        
        # Add high latencies
        for _ in range(10):
            self.tuner.add_latency(3.0)  # Above LATENCY_TARGET (1.5)
        
        throttle = self.tuner.recommend_throttle()
        self.assertGreater(throttle, 1.0,
                          "High latency should increase throttle")
    
    @patch.object(AutoTuner, 'get_gpu_util')
    def test_throttle_high_errors(self, mock_gpu):
        """Test that high error rate increases throttle."""
        mock_gpu.return_value = 50  # Normal GPU
        
        # Add many errors
        for _ in range(10):
            self.tuner.add_error()
        
        throttle = self.tuner.recommend_throttle()
        self.assertGreater(throttle, 1.0,
                          "High error rate should increase throttle")
    
    @patch.object(AutoTuner, 'get_gpu_util')
    def test_throttle_normal_conditions(self, mock_gpu):
        """Test throttle under normal conditions."""
        mock_gpu.return_value = 50  # Normal GPU
        
        # Add normal latencies
        for _ in range(5):
            self.tuner.add_latency(1.0)  # Below LATENCY_TARGET
        
        throttle = self.tuner.recommend_throttle()
        self.assertEqual(throttle, 1.0,
                        "Normal conditions should have throttle of 1.0")


if __name__ == '__main__':
    unittest.main()
