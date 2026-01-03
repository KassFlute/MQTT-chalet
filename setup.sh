#!/bin/bash
# Setup script for MQTT-chalet systemd service
# Run this with sudo on the Raspberry Pi

set -e

SERVICE_NAME="mqtt-chalet"
PROJECT_DIR="/home/pi/MQTT-chalet"
VENV_DIR="${PROJECT_DIR}/venv"
LOG_DIR="/var/log/MQTT-chalet"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo "=========================================="
echo "Setting up ${SERVICE_NAME} systemd service"
echo "=========================================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use: sudo ./setup-service.sh)"
   exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "${VENV_DIR}" ]; then
    echo "Creating Python virtual environment..."
    sudo -u pi python3 -m venv "${VENV_DIR}"
    if [ $? -eq 0 ]; then
        echo "✓ Virtual environment created successfully"
    else
        echo "✗ Failed to create virtual environment"
        exit 1
    fi
fi

# Install Python dependencies in virtual environment
echo "Installing Python dependencies from requirements.txt..."
sudo -u pi "${VENV_DIR}/bin/pip" install -q -r "${PROJECT_DIR}/requirements.txt"
if [ $? -eq 0 ]; then
    echo "✓ Python packages installed successfully"
else
    echo "✗ Failed to install Python packages"
    exit 1
fi

# Create log directory
echo "Creating log directory: ${LOG_DIR}"
mkdir -p "${LOG_DIR}"
chown pi:pi "${LOG_DIR}"
chmod 755 "${LOG_DIR}"

# Copy service file
echo "Installing service file to ${SERVICE_FILE}"
cp "${PROJECT_DIR}/${SERVICE_NAME}.service" "${SERVICE_FILE}"
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
echo "  sudo systemctl status ${SERVICE_NAME}     # Check service status"
echo "  journalctl -u ${SERVICE_NAME} -f          # View live logs"
echo "  tail -f ${LOG_DIR}/output.log             # View application output logs"
echo "  tail -f ${LOG_DIR}/error.log              # View error logs"
echo ""

