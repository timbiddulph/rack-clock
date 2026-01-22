#!/usr/bin/env python3
"""
Rack Clock - Main Application

NTP-synchronized clock with 8-digit 7-segment LED display.
Display format: HH:MM:SS.mm (hours, minutes, seconds, centiseconds)
"""

import signal
import sys
import time
from typing import Optional

import config
from display import Display
from ntp_sync import NTPSync


class RackClock:
    """Main clock application."""

    def __init__(self):
        self.display: Optional[Display] = None
        self.ntp: Optional[NTPSync] = None
        self._running = False

    def setup(self) -> None:
        """Initialize hardware and NTP sync."""
        print("Rack Clock starting...", file=sys.stderr)

        # Initialize display
        self.display = Display(brightness=config.DISPLAY_BRIGHTNESS)
        self.display.show_waiting()

        # Initialize NTP sync
        self.ntp = NTPSync()
        self.ntp.start_background_sync()

        # Wait briefly for initial sync
        print("Waiting for NTP sync...", file=sys.stderr)
        sync_wait = 0
        while not self.ntp.is_synced and sync_wait < 10:
            time.sleep(0.5)
            sync_wait += 0.5

        if self.ntp.is_synced:
            print("NTP sync complete.", file=sys.stderr)
        else:
            print("Warning: NTP sync not yet complete, using system time.",
                  file=sys.stderr)

    def run(self) -> None:
        """Main display loop at 100Hz."""
        self._running = True

        # Track timing for consistent updates
        next_update = time.monotonic()

        while self._running:
            # Get current NTP-corrected time
            hours, minutes, seconds, centiseconds = self.ntp.get_time()

            # Update display
            if self.ntp.is_synced:
                self.display.show_time(hours, minutes, seconds, centiseconds)
            else:
                # Show time but indicate not synced (could add indicator)
                self.display.show_time(hours, minutes, seconds, centiseconds)

            # Wait for next update interval
            next_update += config.UPDATE_INTERVAL
            sleep_time = next_update - time.monotonic()

            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                # We're behind, reset timing
                next_update = time.monotonic()

    def stop(self) -> None:
        """Stop the clock gracefully."""
        print("\nShutting down...", file=sys.stderr)
        self._running = False

        if self.ntp:
            self.ntp.stop_background_sync()

        if self.display:
            self.display.clear()

    def handle_signal(self, signum, frame) -> None:
        """Handle termination signals."""
        self.stop()
        sys.exit(0)


def main():
    """Entry point."""
    clock = RackClock()

    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, clock.handle_signal)
    signal.signal(signal.SIGTERM, clock.handle_signal)

    try:
        clock.setup()
        clock.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if clock.display:
            clock.display.show_error()
        raise
    finally:
        clock.stop()


if __name__ == "__main__":
    main()
