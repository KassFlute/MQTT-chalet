# config.example.py - MQTT Configuration Template
# Copy this file to config.py and update with your actual credentials

# MQTT Broker Settings
MQTT_HOST = "your.mqtt.broker.ip"  # e.g., "192.168.1.100" or Tailscale IP
MQTT_PORT = 1883
MQTT_USER = "your_mqtt_username"
MQTT_PASS = "your_mqtt_password"

# MQTT Topics
TEMP_TOPIC = "chalet/temperature"
RELAY_SET_TOPIC = "chalet/relay/set"
RELAY_GET_TOPIC = "chalet/relay/get"

# Hardware Configuration
DHT11_PIN = 12  # GPIO pin for DHT11 sensor
RF_PIN = 18     # GPIO pin for RF transmitter
