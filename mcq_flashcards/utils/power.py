"""Power management utilities for Windows.

This module provides the WindowsInhibitor class to prevent
system sleep during long-running operations.
"""

import ctypes


class WindowsInhibitor:
    """Prevent OS sleep/hibernate on Windows."""
    
    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001

    def __init__(self):
        """Initialize the inhibitor."""
        pass

    def inhibit(self):
        """Prevent system from sleeping.
        
        Uses Windows API to keep the system awake during
        long-running flashcard generation operations.
        """
        print("   (preventing sleep)")
        ctypes.windll.kernel32.SetThreadExecutionState(
            self.ES_CONTINUOUS | self.ES_SYSTEM_REQUIRED
        )

    def uninhibit(self):
        """Allow system to sleep normally.
        
        Restores normal power management behavior.
        """
        ctypes.windll.kernel32.SetThreadExecutionState(
            self.ES_CONTINUOUS
        )
