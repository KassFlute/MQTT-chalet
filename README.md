# MQTT Chalet

Remote control system for my chalet's heater. The chalet has no internet connection, so this uses a Raspberry Pi with a data-only SIM card to connect to my home MQTT broker via Tailscale VPN. This lets me turn the heating on/off remotely through Home Assistant and monitor the temperature.

## What It Does

- **Remote heater control** via 433MHz RF relay - turn heating on/off from anywhere at anytime
- **Temperature monitoring** via DHT11 sensor
- **Works with celluar connectivity** to work where no internet line is present

## Hardware Needed

- Raspberry Pi (with 4G/LTE USB modem + data capable SIM)
- DHT11 temperature/humidity sensor
- 433MHz RF transmitter
- 433MHz RF controlled relay
- Sufficient power supply for the Raspberry pi

## Installation

### 1. Setup on Raspberry Pi

```bash
# Clone the repo
git clone https://github.com/KassFlute/MQTT-chalet.git
cd MQTT-chalet

# Configure settings
cp config.example.py config.py
nano config.py  # Update MQTT host (Tailscale IP), credentials, and GPIO pins
```

### 2. Install Tailscale

Install and run Tailscale on the Raspberry Pi using exit node to have access to the MQTT broker in the exit node's network:

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
sudo tailscale set --exit-node=<exit-node-ip>
```

### 3. Install and Run

```bash
# Run setup script (installs dependencies and systemd service)
sudo bash setup-service.sh

# Enable and start the service
chmod +x manage-service.sh
./manage-service.sh enable
./manage-service.sh start

# Check status
./manage-service.sh status
```

## Configuration

Edit `config.py` with your settings:

```python
MQTT_HOST = "100.x.x.x"  # MQTT broker's IP running on tailscale exit node's network
MQTT_USER = "your_user"
MQTT_PASS = "your_pass"
DHT11_PIN = 12  # GPIO pin for sensor
RF_PIN = 18     # GPIO pin for RF transmitter
```

## Home Assistant Integration

Use GUI to setup a temprerature sensor and switch 
or add to your `configuration.yaml`:

```yaml
mqtt:
  sensor:
    - name: "Chalet Temperature"
      state_topic: "chalet/temperature"
      unit_of_measurement: "°C"
      value_template: "{{ value_json.temperature }}"

  switch:
    - name: "Chalet Heating"
      state_topic: "chalet/relay/get"
      command_topic: "chalet/relay/set"
      payload_on: "ON"
      payload_off: "OFF"
```

## Managing the Service

```bash
./manage-service.sh start    # Start service
./manage-service.sh stop     # Stop service
./manage-service.sh restart  # Restart service
./manage-service.sh logs     # View logs
./manage-service.sh status   # Check status
```

## Troubleshooting

**Can't connect to MQTT?**
- Check Tailscale: `sudo tailscale status`
- Test connectivity: `ping <mqtt-broker-tailscale-ip>`

**Sensor not working?**
- Verify wiring and GPIO pins in `config.py`
- Check logs: `./manage-service.sh logs`
