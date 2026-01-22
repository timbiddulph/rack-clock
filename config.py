"""
Rack Clock Configuration
"""

# NTP Configuration
NTP_SERVERS = [
    "pool.ntp.org",
    "time.google.com",
    "time.cloudflare.com",
    "time.nist.gov",
]
NTP_SYNC_INTERVAL = 60  # seconds between NTP queries
NTP_TIMEOUT = 5  # seconds to wait for NTP response

# Display Configuration
DISPLAY_BRIGHTNESS = 8  # 0-15 (0 = dimmest, 15 = brightest)
DISPLAY_DIGITS = 8

# GPIO Configuration (directly from Pi GPIO header)
SPI_PORT = 0
SPI_DEVICE = 0  # CE0 = GPIO8

# Timing
UPDATE_RATE_HZ = 100  # Display refresh rate
UPDATE_INTERVAL = 1.0 / UPDATE_RATE_HZ  # 10ms
