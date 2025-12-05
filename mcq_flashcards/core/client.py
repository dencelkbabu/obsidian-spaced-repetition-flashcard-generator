"""Ollama API client for LLM interactions.

This module provides the OllamaClient class for communicating with
the Ollama API to generate MCQ content.
"""

import time
from typing import Any, Dict, Optional

import requests

from mcq_flashcards.core.config import Config, MAX_RETRIES, MAX_DELAY, logger
from mcq_flashcards.utils.autotuner import AUTOTUNER


class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(self, config: Config):
        """Initialize the Ollama client.
        
        Args:
            config: Configuration object with model settings
        """
        self.config = config
        self.base_url = "http://localhost:11434/api/generate"

    def check_connection(self) -> bool:
        """Check if Ollama server is reachable.
        
        Returns:
            True if server is accessible, False otherwise
        """
        try:
            requests.get("http://localhost:11434", timeout=2)
            return True
        except requests.exceptions.RequestException:
            return False

    def generate(self, prompt: str, worker_state: Dict[str, Any], system: str = None) -> Optional[Dict]:
        """Generate text with exponential backoff and AutoTuner throttling.
        
        Args:
            prompt: Text prompt for generation
            worker_state: Dictionary tracking worker state (delay, retries)
            system: Optional system prompt
            
        Returns:
            Response dictionary from Ollama API, or None if all retries failed
        """
        if not prompt or not prompt.strip():
            return None

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
                
                if system:
                    payload["system"] = system
                
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
                    logger.error(f"Request failed after {MAX_RETRIES} attempts: {e}")

            # Backoff Logic
            worker_state["retries"] += 1
            delay = min(worker_state["delay"] * (2 ** worker_state["retries"]), MAX_DELAY)
            throttle = AUTOTUNER.recommend_throttle()
            final_sleep = delay * throttle
            
            time.sleep(final_sleep)

        return None
