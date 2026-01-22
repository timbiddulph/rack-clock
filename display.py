"""
MAX7219 Display Driver Wrapper

Handles the 8-digit 7-segment LED display for showing time in HH:MM:SS.mm format.
"""

import sys
from typing import Optional

# Try to import luma libraries, fall back to mock for testing
try:
    from luma.led_matrix.device import max7219
    from luma.core.interface.serial import spi, noop
    from luma.core.virtual import sevensegment
    HARDWARE_AVAILABLE = True
except ImportError:
    HARDWARE_AVAILABLE = False

import config


class Display:
    """Wrapper for MAX7219 8-digit 7-segment display."""

    def __init__(self, brightness: int = config.DISPLAY_BRIGHTNESS):
        self.brightness = brightness
        self.device = None
        self.seg = None
        self._last_text = None

        if HARDWARE_AVAILABLE:
            self._init_hardware()
        else:
            print("Warning: Display hardware not available, running in mock mode",
                  file=sys.stderr)

    def _init_hardware(self) -> None:
        """Initialize the MAX7219 hardware."""
        serial = spi(port=config.SPI_PORT, device=config.SPI_DEVICE, gpio=noop())
        self.device = max7219(serial, cascaded=1)
        self.device.contrast(self.brightness * 16)  # Scale 0-15 to 0-255
        self.seg = sevensegment(self.device)

    def set_brightness(self, level: int) -> None:
        """Set display brightness (0-15)."""
        self.brightness = max(0, min(15, level))
        if self.device:
            self.device.contrast(self.brightness * 16)

    def show_time(self, hours: int, minutes: int, seconds: int,
                  centiseconds: int) -> None:
        """
        Display time in HH:MM:SS.mm format.

        The decimal point after seconds separates the centiseconds.
        """
        # Format: HH.MM.SS.mm (dots act as colons, last dot before centiseconds)
        text = f"{hours:02d}.{minutes:02d}.{seconds:02d}.{centiseconds:02d}"
        self._show_text(text)

    def show_waiting(self) -> None:
        """Display waiting pattern while NTP sync is pending."""
        self._show_text("--.--.--.--")

    def show_error(self, code: str = "Err") -> None:
        """Display error indicator."""
        self._show_text(f"  {code:>6}")

    def clear(self) -> None:
        """Clear the display."""
        self._show_text("        ")

    def _show_text(self, text: str) -> None:
        """Show text on the display, avoiding unnecessary updates."""
        if text == self._last_text:
            return

        self._last_text = text

        if self.seg:
            self.seg.text = text
        else:
            # Mock mode: print to console
            # Convert dots to colons for readable output
            display_text = text.replace(".", ":")
            print(f"\r[DISPLAY] {display_text}", end="", flush=True)

    def test_pattern(self) -> None:
        """Run a test pattern across all digits."""
        import time

        # Show all 8s (all segments lit)
        self._show_text("88.88.88.88")
        time.sleep(1)

        # Count up
        for i in range(100):
            self.show_time(12, 34, 56, i)
            time.sleep(0.05)

        self.clear()


def main():
    """Test the display module."""
    print("Display Test")
    print(f"Hardware available: {HARDWARE_AVAILABLE}")

    display = Display()

    print("\nRunning test pattern...")
    display.test_pattern()

    print("\n\nShowing waiting pattern...")
    display.show_waiting()

    import time
    time.sleep(2)

    print("\n\nDone.")
    display.clear()


if __name__ == "__main__":
    main()
