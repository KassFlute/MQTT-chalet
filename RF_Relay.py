import logging

from rpi_rf import RFDevice
import RPi.GPIO as GPIO

logger = logging.getLogger(__name__)


class RFRelay:
    """RF relay controller for controlling wireless relays via GPIO."""

    # ========================================================================
    # CONFIGURATION
    # ========================================================================
    TX_REPEAT = 10
    PROTOCOL = 1
    PULSE_LENGTH = 350
    CODE_LENGTH = 24

    def __init__(self, pin, relays=None):
        """
        Initialize RF relay controller.

        Args:
            pin: GPIO pin for RF transmitter
            relays: Dict with relay names as keys and on_code as values.
                   Example: {"relay1": 101, "relay2": 201}
        """
        GPIO.setmode(GPIO.BCM)
        self.pin = pin
        self.relays = relays or {}
        self.rfdevice = None
        logger.debug(f"RFRelay initialized with pin {pin}")

    def _init_device(self):
        """Initialize the RF device if not already initialized."""
        if not self.rfdevice:
            self.rfdevice = RFDevice(self.pin)
            self.rfdevice.enable_tx()
            self.rfdevice.tx_repeat = self.TX_REPEAT
            logger.debug("RF device initialized and transmitter enabled")

    def _cleanup(self):
        """Clean up RF device resources."""
        if self.rfdevice:
            self.rfdevice.cleanup()
            self.rfdevice = None
            logger.debug("RF device cleaned up")

    def setup_relay(self, relay_name, on_code):
        """
        Pair a new relay and store its on code.

        Args:
            relay_name: Name identifier for the relay
            on_code: Code to send for turning the relay ON
        """
        self._init_device()
        logger.info(f"Starting pairing for relay '{relay_name}'")
        print(f"Put receiver for '{relay_name}' in pairing mode and press enter...")
        input()
        self.rfdevice.tx_code(on_code, self.PROTOCOL, self.PULSE_LENGTH, self.CODE_LENGTH)
        self.relays[relay_name] = on_code
        logger.info(f"Relay '{relay_name}' paired successfully. ON code: {on_code}, OFF code: {on_code + 1}")

    def control(self, relay_name, state):
        """
        Control a relay by name.

        Args:
            relay_name: Name of the relay to control
            state: "on" or "off"
        """
        if relay_name not in self.relays:
            logger.error(f"Relay '{relay_name}' not found in configured relays")
            return

        on_code = self.relays[relay_name]
        off_code = on_code + 1

        self._init_device()
        if state.lower() == "on":
            self.rfdevice.tx_code(on_code)
            logger.info(f"Relay '{relay_name}' turned ON (code: {on_code})")
        elif state.lower() == "off":
            self.rfdevice.tx_code(off_code)
            logger.info(f"Relay '{relay_name}' turned OFF (code: {off_code})")
        else:
            logger.error(f"Invalid state '{state}'. Use 'on' or 'off'")

    def on(self, relay_name):
        """Turn a relay ON."""
        self.control(relay_name, "on")

    def off(self, relay_name):
        """Turn a relay OFF."""
        self.control(relay_name, "off")

    def cleanup(self):
        """Clean up all resources."""
        self._cleanup()

