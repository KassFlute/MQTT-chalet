import logging
import threading
import time
from typing import Dict, Optional

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

import DHT11Reader
import RF_Relay
import config

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# ============================================================================
# MQTT CONFIGURATION (from config.py)
# ============================================================================

MQTT_HOST = config.MQTT_HOST
MQTT_PORT = config.MQTT_PORT
MQTT_USER = config.MQTT_USER
MQTT_PASS = config.MQTT_PASS
TEMP_TOPIC = config.TEMP_TOPIC
RELAY_SET_TOPIC = config.RELAY_SET_TOPIC
RELAY_GET_TOPIC = config.RELAY_GET_TOPIC

# ============================================================================
# HARDWARE CONFIGURATION (from config.py)
# ============================================================================

DHT11_PIN = config.DHT11_PIN
RF_PIN = config.RF_PIN

# ============================================================================
# MQTT CALLBACKS
# ============================================================================

def on_connect(client, userdata, flags, reason_code, properties):
    """Called when the client connects to the broker."""
    if reason_code == 0:
        logger.info(f"Connected to MQTT broker successfully (result code: {reason_code})")
        client.subscribe(RELAY_SET_TOPIC)
    else:
        logger.error(f"Failed to connect to MQTT broker with result code: {reason_code}")


def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    """Called when the client disconnects from the broker."""
    if reason_code == 0:
        logger.info(f"Disconnected from MQTT broker (reason code: {reason_code})")
    else:
        logger.error(f"Unexpected disconnection from MQTT broker (reason code: {reason_code})")


def on_socket_connect_fail(client, userdata):
    """Called when a socket connection attempt fails."""
    logger.error("Failed to establish socket connection to MQTT broker")


def on_socket_close(client, userdata):
    """Called when a socket is closed."""
    logger.warning("Socket connection to MQTT broker closed")


def on_message(client, userdata, msg):
    """Called when a message is received on a subscribed topic."""
    logger.debug(f"Message received on {msg.topic}: {msg.payload.decode('utf-8')}")
    
    if msg.topic == RELAY_SET_TOPIC:
        payload = msg.payload.decode("utf-8").lower()
        
        # Check cooldown
        with relay_lock:
            current_time = time.time()
            if current_time - last_relay_switch[0] < RELAY_COOLDOWN:
                cooldown_remaining = RELAY_COOLDOWN - (current_time - last_relay_switch[0])
                logger.warning(
                    f"Relay command ignored due to cooldown. "
                    f"Please wait {cooldown_remaining:.1f} more seconds."
                )
                return
            
            # Process the command
            if payload == "on":
                rf_relay.on("mazout_outlet")
                logger.info("Relay turned ON from MQTT")
            elif payload == "off":
                rf_relay.off("mazout_outlet")
                logger.info("Relay turned OFF from MQTT")
            else:
                logger.warning(f"Unknown relay command: {payload}")
                return
            
            # Update last switch time
            last_relay_switch[0] = current_time
        
        client.publish(RELAY_GET_TOPIC, "ON" if payload == "on" else "OFF", retain=True)

# ============================================================================
# SENSOR WORKER THREAD
# ============================================================================

def sensor_worker(poll_interval_seconds=5):
    """Continuously read the sensor in the background and cache the last value."""
    while not stop_event.is_set():
        try:
            temp, hum = dht11Reader.read_reliable(retries=1)
            logger.debug(f"Sensor read: Temp={temp:.2f} °C, Hum={hum:.1f} %")
            with reading_lock:
                latest_reading["temp"] = temp
                latest_reading["hum"] = hum
        except Exception as exc:
            logger.error(f"Sensor read error: {exc}")
        
        # Pace the sensor to avoid hammering it
        stop_event.wait(poll_interval_seconds)

# ============================================================================
# INITIALIZATION
# ============================================================================

# Relay cooldown configuration
RELAY_COOLDOWN = 5.0  # seconds

# Setup states
latest_reading: Dict[str, Optional[float]] = {"temp": None, "hum": None}
reading_lock = threading.Lock()
stop_event = threading.Event()
relay_lock = threading.Lock()
last_relay_switch = [0.0]  # Use list to allow modification in nested scope

# Set up MQTT client
logger.info("Setting up MQTT client...")
mqttc = mqtt.Client(CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_disconnect = on_disconnect
mqttc.on_socket_connect_fail = on_socket_connect_fail
mqttc.on_socket_close = on_socket_close
mqttc.on_message = on_message
mqttc.username_pw_set(MQTT_USER, MQTT_PASS)

try:
    logger.info(f"Attempting to connect to MQTT broker at {MQTT_HOST}:{MQTT_PORT}...")
    mqttc.connect(MQTT_HOST, MQTT_PORT, 60)
except OSError as e:
    logger.error(f"Failed to connect to MQTT broker: {e}")
    raise

# Setup DHT11
logger.info("Initializing DHT11 sensor...")
dht11Reader = DHT11Reader.DHT11Reader(DHT11_PIN)

# Setup RF Relay
logger.info("Initializing RF relay controller...")
rf_relay = RF_Relay.RFRelay(relays={"mazout_outlet": 101}, pin=RF_PIN)
rf_relay.off("mazout_outlet")
mqttc.publish(RELAY_GET_TOPIC, "OFF", retain=True)

# Start background sensor thread
logger.info("Starting sensor read thread...")
with reading_lock:
    latest_reading["temp"], latest_reading["hum"] = dht11Reader.read_reliable(
        retries=50, delay=1.0
    )  # Force a first valid read
sensor_thread = threading.Thread(target=sensor_worker, daemon=True)
sensor_thread.start()

# Start MQTT loop
logger.info("Starting MQTT loop...")
mqttc.loop_start()

# ============================================================================
# MAIN LOOP
# ============================================================================

time.sleep(2)
try:
    logger.info("Application started successfully")
    while True:
        with reading_lock:
            temp = latest_reading["temp"]
            humidity = latest_reading["hum"]
        
        if temp is None:
            logger.warning("No temperature reading available; skipping publish")
        else:
            mqttc.publish(TEMP_TOPIC, f"{temp:.2f}", retain=True)
            logger.debug(f"Published temperature: {temp:.2f} °C")
        
        if humidity is None:
            logger.warning("No humidity reading available; skipping publish")
        else:
            mqttc.publish(config.HUMIDITY_TOPIC, f"{humidity:.1f}", retain=True)
            logger.debug(f"Published humidity: {humidity:.1f} %")
        
        time.sleep(60)

except KeyboardInterrupt:
    logger.info("Keyboard interrupt received, shutting down...")
finally:
    logger.info("Cleaning up resources...")
    stop_event.set()
    sensor_thread.join(timeout=2)
    mqttc.loop_stop()
    dht11Reader.cleanup()
    logger.info("Application stopped")
