#!/bin/bash
# Setup script for MQTT-chalet systemd service
# Run this with sudo on the Raspberry Pi

set -e

# Auto-detect the service user (the user running sudo, or current user if not sudo)
SERVICE_USER="${SUDO_USER:-$(whoami)}"
SERVICE_HOME="/home/${SERVICE_USER}"

SERVICE_NAME="mqtt-chalet"
PROJECT_DIR="${SERVICE_HOME}/MQTT-chalet"
VENV_DIR="${PROJECT_DIR}/venv"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo "=========================================="
echo "Setting up ${SERVICE_NAME} systemd service"
echo "=========================================="
echo "Service user: ${SERVICE_USER}"
echo "Project directory: ${PROJECT_DIR}"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use: sudo ./setup-service.sh)"
   exit 1
fi

# Check if the service user exists
if ! id "${SERVICE_USER}" &>/dev/null; then
    echo "✗ User '${SERVICE_USER}' does not exist"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "${VENV_DIR}" ]; then
    echo "Creating Python virtual environment..."
    sudo -u "${SERVICE_USER}" python3 -m venv "${VENV_DIR}"
    if [ $? -eq 0 ]; then
        echo "✓ Virtual environment created successfully"
    else
        echo "✗ Failed to create virtual environment"
        exit 1
    fi
fi

# Install Python dependencies in virtual environment
echo "Installing Python dependencies from requirements.txt..."
sudo -u "${SERVICE_USER}" "${VENV_DIR}/bin/pip" install -q -r "${PROJECT_DIR}/requirements.txt"
if [ $? -eq 0 ]; then
    echo "✓ Python packages installed successfully"
else
    echo "✗ Failed to install Python packages"
    exit 1
fi

# Generate service file from template with detected user
echo "Generating service file..."
cat > "${SERVICE_FILE}" << EOF
[Unit]
Description=MQTT Chalet - DHT11 & RF Relay Controller
After=network.target mosquitto.service
Wants=mosquitto.service

[Service]
Type=simple
User=${SERVICE_USER}
WorkingDirectory=${PROJECT_DIR}
ExecStart=${VENV_DIR}/bin/python3 ${PROJECT_DIR}/main.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=${SERVICE_NAME}

[Install]
WantedBy=multi-user.target
EOF

chown root:root "${SERVICE_FILE}"
chmod 644 "${SERVICE_FILE}"

# Reload systemd daemon
echo "Reloading systemd daemon..."
systemctl daemon-reload

echo ""
echo "=========================================="
echo "Installation complete!"
echo "=========================================="
echo ""
echo "Available commands:"
echo "  sudo systemctl start ${SERVICE_NAME}      # Start the service now"
echo "  sudo systemctl stop ${SERVICE_NAME}       # Stop the service"
echo "  sudo systemctl restart ${SERVICE_NAME}    # Restart the service"
echo "  sudo systemctl enable ${SERVICE_NAME}     # Enable on system startup"
echo "  sudo systemctl disable ${SERVICE_NAME}    # Disable on system startup"
echo "  sudo systemctl status ${SERVICE_NAME}     # Check service status (shows recent logs)"
echo "  journalctl -u ${SERVICE_NAME} -f          # View live logs"
echo "  journalctl -u ${SERVICE_NAME} -n 100      # View last 100 log lines"
echo ""
