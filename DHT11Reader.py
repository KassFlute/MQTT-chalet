import logging
import time

import RPi.GPIO as GPIO
import dht11

logger = logging.getLogger(__name__)


class DHT11Reader:
    """DHT11 temperature and humidity sensor reader with reliable retry logic."""

    def __init__(self, pin):
        """
        Initialize the DHT11 sensor reader.

        Args:
            pin: GPIO pin number connected to the DHT11 sensor
        """
        self.pin = pin
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        self.instance = dht11.DHT11(pin=self.pin)
        self.last_valid = (0.0, 0.0)
        logger.debug(f"DHT11Reader initialized on GPIO pin {pin}")

    def read(self):
        """
        Read the sensor once.

        Returns:
            Tuple of (temperature, humidity) if valid, else (None, None)
        """
        result = self.instance.read()
        if result.is_valid():
            # Store last valid reading for fallback
            self.last_valid = (result.temperature, result.humidity)
            logger.debug(f"Valid sensor read: {result.temperature}°C, {result.humidity}%")
            return result.temperature, result.humidity
        else:
            logger.debug("Invalid sensor read, will retry")
            return None, None

    def read_reliable(self, retries=10, delay=2.0):
        """
        Read the sensor with retry logic.

        Args:
            retries: Number of times to retry if reading fails
            delay: Delay in seconds between retries

        Returns:
            Tuple of (temperature, humidity) if successful, else last cached values
        """
        for attempt in range(retries):
            temp, hum = self.read()
            if temp is not None and hum is not None:
                logger.debug(f"Good reading after {attempt + 1} attempt(s): {temp:.2f}°C, {hum:.1f}%")
                return temp, hum
            time.sleep(delay)
        
        # If all retries failed, return the last known valid reading
        logger.debug(f"All {retries} read attempts failed, returning cached values: {self.last_valid}")
        return self.last_valid

    def cleanup(self):
        """Clean up GPIO resources."""
        GPIO.cleanup()
        logger.debug("GPIO cleanup completed")
