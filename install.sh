#!/bin/bash
#
# Rack Clock Installation Script
# Run with: sudo bash install.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="rack-clock"

echo "=== Rack Clock Installer ==="
echo

# Check for root
if [ "$EUID" -ne 0 ]; then
    echo "Error: Please run with sudo"
    exit 1
fi

# Enable SPI if not already enabled
echo "Checking SPI configuration..."
if ! grep -q "^dtparam=spi=on" /boot/config.txt 2>/dev/null; then
    echo "Enabling SPI in /boot/config.txt..."
    echo "dtparam=spi=on" >> /boot/config.txt
    SPI_CHANGED=1
fi

# Install system dependencies
echo "Installing system dependencies..."
apt-get update
apt-get install -y python3-pip python3-dev python3-venv chrony

# Configure chrony as NTP server
echo "Configuring NTP server (chrony)..."
cp "$SCRIPT_DIR/chrony.conf" /etc/chrony/chrony.conf
systemctl enable chrony
systemctl restart chrony

# Create virtual environment
echo "Creating Python virtual environment..."
VENV_DIR="$SCRIPT_DIR/venv"
python3 -m venv "$VENV_DIR"

# Install Python dependencies
echo "Installing Python dependencies..."
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"

# Create systemd service
echo "Installing systemd service..."
cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=Rack Clock NTP Display
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=${VENV_DIR}/bin/python ${SCRIPT_DIR}/clock.py
WorkingDirectory=${SCRIPT_DIR}
Restart=always
RestartSec=5
User=root

# Environment
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
systemctl daemon-reload
systemctl enable ${SERVICE_NAME}

echo
echo "=== Installation Complete ==="
echo
echo "Clock Commands:"
echo "  Start:   sudo systemctl start ${SERVICE_NAME}"
echo "  Stop:    sudo systemctl stop ${SERVICE_NAME}"
echo "  Status:  sudo systemctl status ${SERVICE_NAME}"
echo "  Logs:    sudo journalctl -u ${SERVICE_NAME} -f"
echo
echo "NTP Server:"
echo "  Status:  chronyc tracking"
echo "  Clients: chronyc clients"
echo "  The Pi now serves NTP on port 123 to local networks"
echo "  (192.168.x.x, 10.x.x.x, 172.16-31.x.x)"
echo
echo "Timezone: $(timedatectl show -p Timezone --value) (uses OS setting)"
echo

if [ -n "$SPI_CHANGED" ]; then
    echo "IMPORTANT: SPI was enabled. Please reboot before starting the service:"
    echo "  sudo reboot"
else
    echo "Start the clock now with:"
    echo "  sudo systemctl start ${SERVICE_NAME}"
fi
