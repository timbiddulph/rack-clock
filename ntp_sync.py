"""
NTP Synchronization Module

Provides accurate time by querying NTP servers and calculating offset from system time.
"""

import time
import threading
from typing import Optional, Tuple
import sys

try:
    import ntplib
    NTP_AVAILABLE = True
except ImportError:
    NTP_AVAILABLE = False

import config


class NTPSync:
    """
    NTP synchronization handler.

    Periodically queries NTP servers and maintains an offset from system time
    for accurate timekeeping between syncs.
    """

    def __init__(self):
        self._offset: float = 0.0  # Offset from system time in seconds
        self._last_sync: Optional[float] = None
        self._sync_successful: bool = False
        self._lock = threading.Lock()
        self._running = False
        self._sync_thread: Optional[threading.Thread] = None

        if not NTP_AVAILABLE:
            print("Warning: ntplib not available, using system time only",
                  file=sys.stderr)

    @property
    def is_synced(self) -> bool:
        """Check if NTP sync has been successful."""
        with self._lock:
            return self._sync_successful

    @property
    def offset(self) -> float:
        """Get current NTP offset from system time."""
        with self._lock:
            return self._offset

    @property
    def last_sync_time(self) -> Optional[float]:
        """Get timestamp of last successful sync."""
        with self._lock:
            return self._last_sync

    def get_time(self) -> Tuple[int, int, int, int]:
        """
        Get current NTP-corrected time as (hours, minutes, seconds, centiseconds).

        Returns time in 24-hour format.
        """
        with self._lock:
            offset = self._offset

        # Get current time with NTP offset applied
        current_time = time.time() + offset

        # Use system timezone
        time_struct = time.localtime(current_time)

        # Extract components
        hours = time_struct.tm_hour
        minutes = time_struct.tm_min
        seconds = time_struct.tm_sec

        # Calculate centiseconds from fractional part
        fractional = current_time - int(current_time)
        centiseconds = int(fractional * 100)

        return hours, minutes, seconds, centiseconds

    def sync_once(self) -> bool:
        """
        Perform a single NTP sync attempt.

        Returns True if sync was successful.
        """
        if not NTP_AVAILABLE:
            return False

        client = ntplib.NTPClient()

        for server in config.NTP_SERVERS:
            try:
                response = client.request(server, timeout=config.NTP_TIMEOUT)

                with self._lock:
                    self._offset = response.offset
                    self._last_sync = time.time()
                    self._sync_successful = True

                print(f"NTP sync successful: {server}, offset: {response.offset:.6f}s",
                      file=sys.stderr)
                return True

            except Exception as e:
                print(f"NTP sync failed for {server}: {e}", file=sys.stderr)
                continue

        return False

    def start_background_sync(self) -> None:
        """Start background thread for periodic NTP sync."""
        if self._running:
            return

        self._running = True
        self._sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self._sync_thread.start()

    def stop_background_sync(self) -> None:
        """Stop background sync thread."""
        self._running = False
        if self._sync_thread:
            self._sync_thread.join(timeout=config.NTP_TIMEOUT + 1)

    def _sync_loop(self) -> None:
        """Background sync loop."""
        # Initial sync attempt
        self.sync_once()

        while self._running:
            # Wait for next sync interval
            for _ in range(config.NTP_SYNC_INTERVAL):
                if not self._running:
                    return
                time.sleep(1)

            # Perform sync
            self.sync_once()


def main():
    """Test NTP synchronization."""
    print("NTP Sync Test")
    print(f"NTP library available: {NTP_AVAILABLE}")

    ntp = NTPSync()

    print("\nAttempting NTP sync...")
    success = ntp.sync_once()

    print(f"\nSync successful: {success}")
    print(f"Offset: {ntp.offset:.6f} seconds")

    print("\nCurrent NTP time:")
    for _ in range(50):
        h, m, s, cs = ntp.get_time()
        print(f"\r  {h:02d}:{m:02d}:{s:02d}.{cs:02d}", end="", flush=True)
        time.sleep(0.1)

    print("\n\nDone.")


if __name__ == "__main__":
    main()
