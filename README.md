# MQTT Chalet

Remote control system for my chalet's heater. The chalet has no internet connection, so this uses a Raspberry Pi with a data-only SIM card to connect to my home MQTT broker via Tailscale VPN. This lets me turn the heating on/off remotely through Home Assistant and monitor the temperature.

## What It Does

- **Remote heater control** via 433MHz RF relay - turn heating on/off from anywhere at anytime
- **Temperature (and Humidity) monitoring** via DHT11 sensor
- **Works with celluar connectivity** to work where no internet line is present

## Hardware Needed

- Raspberry Pi (with 4G/LTE USB modem (like Huawei E3372-325) + data capable SIM)
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
```

## Configuration

Edit `config.py` with your settings:

```python
MQTT_HOST = "100.x.x.x"  # MQTT broker's tailscale IP
MQTT_USER = "your_user"
MQTT_PASS = "your_pass"
DHT11_PIN = 12  # GPIO pin for sensor
RF_PIN = 18     # GPIO pin for RF transmitter
```

First, copy the example config and update it with your settings:

```bash
cp config.example.py config.py
nano config.py  # Update MQTT host, credentials, and GPIO pins
```

### 2. Install and Run

```bash
# Run setup script (installs dependencies and systemd service)
sudo bash setup-service.sh

# Enable service to start on boot
sudo systemctl enable mqtt-chalet

# Start the service
sudo systemctl start mqtt-chalet

# Check status
sudo systemctl status mqtt-chalet
```

## Tailscale Setup

In order for the Raspberry Pi to communicate with the MQTT broker without exposing my broker to the internet I use tailscale.
Tailscale also needs to run on the MQTT broker

Install and run Tailscale on the Raspberry Pi:
```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
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

After installation, the service is managed like a normal linux service:

```bash
sudo systemctl start mqtt-chalet    # Start service
sudo systemctl stop mqtt-chalet     # Stop service
sudo systemctl restart mqtt-chalet  # Restart service
sudo systemctl status mqtt-chalet   # Check status
sudo journalctl -u mqtt-chalet -f   # View live logs
```

## Troubleshooting

**Can't connect to MQTT?**
- Check Tailscale: `sudo tailscale status`
- Test connectivity to MQTT broker: `ping <mqtt-broker-tailscale-ip>`

**Sensor or relay not working?**
- Verify wiring and GPIO pins in `config.py`
- Check logs: `sudo journalctl -u mqtt-chalet -f`
- DHT11 sensors can be broken or wrong
- DHT11 sensors don't go bellow 0 degree
- Check Raspberry Pi power supply amps (smartphone chargers often lie)
- Test with relay really close to emitter to aliminate poor signal or broken antenna
