# Rack Clock

NTP-synchronized clock with 8-digit 7-segment LED display for 10" rack mounting.
Also serves as an NTP server for local network devices.

## Features

- **Accurate time** - Syncs from multiple NTP servers (pool.ntp.org, time.google.com, etc.)
- **High refresh rate** - 100Hz display update for smooth centisecond display
- **NTP server** - Serves time to other devices on your local network via chrony
- **24-hour format** - Display format: `HH:MM:SS.mm` (centiseconds)
- **Auto-start** - systemd service starts on boot
- **Resilient** - Falls back to system time if NTP unavailable, auto-reconnects

## How It Works

1. **NTP Client** (`ntp_sync.py`) - Queries upstream NTP servers every 60 seconds and calculates offset from system time
2. **Display Driver** (`display.py`) - Controls MAX7219 8-digit 7-segment display via SPI
3. **Main Loop** (`clock.py`) - Updates display at 100Hz with NTP-corrected time
4. **NTP Server** (`chrony`) - Allows other network devices to sync from this clock

## Hardware Requirements

| Component | Description | Quantity |
|-----------|-------------|----------|
| Raspberry Pi 1/2 | With Ethernet | 1 |
| MAX7219 8-digit module | 0.36" green 7-segment LED | 1 |
| Jumper wires | Female-to-female | 5 |
| 5V power supply | For Pi (2.5A recommended) | 1 |

**Display Module:** [MAX7219 8-digit 7-segment display (green)](https://www.aliexpress.com/item/1005004869898587.html) - select green option. Also available in red, blue, yellow, and white.

## Wiring Diagram

```
Raspberry Pi                          MAX7219 Module
    GPIO Header                         (8-digit 7-seg)
   ┌───────────┐                       ┌─────────────┐
   │  ·  ·  1  │ (3.3V)               │             │
   │  2  ·  ·  │────────────────────► │ VCC (5V)    │
   │  ·  ·  ·  │                       │             │
   │  6  ·  ·  │────────────────────► │ GND         │
   │  ·  ·  ·  │                       │             │
   │  ·  ·  ·  │                       │             │
   │  ·  ·  ·  │                       │             │
   │  ·  ·  ·  │                       │             │
   │  ·  · 19  │────────────────────► │ DIN (Data)  │
   │  ·  ·  ·  │                       │             │
   │  ·  · 23  │────────────────────► │ CLK (Clock) │
   │ 24  ·  ·  │────────────────────► │ CS (Chip Sel│
   │  ·  ·  ·  │                       │             │
   └───────────┘                       └─────────────┘

Pin Reference:
   Pi Pin 2  (5V)         → VCC
   Pi Pin 6  (GND)        → GND
   Pi Pin 19 (GPIO10/MOSI)→ DIN
   Pi Pin 23 (GPIO11/SCLK)→ CLK
   Pi Pin 24 (GPIO8/CE0)  → CS
```

## Installation

1. **Clone the repository to Pi:**
   ```bash
   cd ~
   git clone https://github.com/timbiddulph/rack-clock.git
   cd rack-clock
   ```

2. **Run the installer:**
   ```bash
   cd ~/rack-clock
   sudo bash install.sh
   ```

3. **Reboot if SPI was just enabled:**
   ```bash
   sudo reboot
   ```

4. **Start the service:**
   ```bash
   sudo systemctl start rack-clock
   ```

## Usage

### Service Commands

```bash
# Start the clock
sudo systemctl start rack-clock

# Stop the clock
sudo systemctl stop rack-clock

# Check status
sudo systemctl status rack-clock

# View logs
sudo journalctl -u rack-clock -f

# Disable auto-start on boot
sudo systemctl disable rack-clock

# Re-enable auto-start
sudo systemctl enable rack-clock
```

### NTP Server

The Pi runs `chrony` as an NTP server, allowing other devices on your network to sync time from it.

```bash
# Check NTP sync status
chronyc tracking

# View connected NTP clients
chronyc clients

# Check NTP sources
chronyc sources -v
```

**Client Configuration:** Point your network devices to the Pi's IP address as their NTP server.

**Allowed Networks:** By default, the following private networks can query NTP:
- 192.168.0.0/16
- 10.0.0.0/8
- 172.16.0.0/12

Edit `/etc/chrony/chrony.conf` to adjust allowed networks.

### Manual Testing

```bash
cd ~/rack-clock

# Test display only
./venv/bin/python display.py

# Test NTP sync only
./venv/bin/python ntp_sync.py

# Run clock manually (Ctrl+C to stop)
./venv/bin/python clock.py
```

## Configuration

Edit `config.py` to customize:

```python
# NTP servers (in order of preference)
NTP_SERVERS = [
    "pool.ntp.org",
    "time.google.com",
    ...
]

# Display brightness (0-15)
DISPLAY_BRIGHTNESS = 8

# Update rate (Hz)
UPDATE_RATE_HZ = 100
```

**Timezone:** The clock uses the OS timezone. Change with:
```bash
sudo timedatectl set-timezone Europe/London
```

## 3D Printed Enclosure

### 10" Rack Mount Dimensions

- **Total Width:** 254mm (10" / half-rack standard)
- **Mounting Width:** 222.25mm (between rack ears)
- **Height:** 1U = 44.45mm
- **Depth:** 100mm minimum

### Display Module Dimensions

![Module dimensions](https://ae01.alicdn.com/kf/Sef9a7510af8f4908b2061173710f37cd6.jpg)

- **PCB dimensions:** 71.57mm x 16.75mm
- **Display area:** 56.87mm x ~8.4mm
- **Cutout (recommended):** 60mm x 12mm (with ~1mm clearance)
- **Mounting holes:** 3.0mm from edges, ~3.3mm diameter
- **Position:** Centered horizontally and vertically

### Rack Ear Mounting Holes

- Hole diameter: 6.35mm (1/4")
- Horizontal: 15.875mm from panel edge
- Vertical: 15.875mm from top/bottom edges

### Rear Panel Openings

- Ethernet: 16mm x 14mm
- Power (micro USB): 8mm x 3mm
- Ventilation slots recommended

## Troubleshooting

### Display shows nothing
1. Check wiring connections
2. Verify SPI is enabled: `ls /dev/spi*` should show devices
3. Check service logs: `sudo journalctl -u rack-clock`

### Display shows `--:--:--:--`
- Clock is waiting for NTP sync
- Check network connection
- Verify NTP servers are reachable: `ntpdate -q pool.ntp.org`

### Time is wrong
1. Check timezone settings on Pi: `timedatectl`
2. Change timezone: `sudo timedatectl set-timezone Europe/London`
3. List all timezones: `timedatectl list-timezones`

### Service won't start
```bash
# Check for errors
sudo systemctl status rack-clock
sudo journalctl -u rack-clock --no-pager

# Test manually
cd ~/rack-clock
sudo ./venv/bin/python clock.py
```

### NTP server not working
```bash
# Check chrony status
sudo systemctl status chrony

# Verify chrony is listening
sudo ss -ulnp | grep chronyd

# Test from another device
ntpdate -q <pi-ip-address>
```

## Files

```
rack-clock/
├── clock.py           # Main application
├── display.py         # MAX7219 display driver
├── ntp_sync.py        # NTP synchronization (client)
├── config.py          # Configuration settings
├── chrony.conf        # NTP server configuration
├── requirements.txt   # Python dependencies
├── install.sh         # Setup script
├── rack-clock.service # systemd service (template)
├── LICENSE            # MIT License
└── README.md          # This file
```

## License

MIT License - see [LICENSE](LICENSE) file for details.
