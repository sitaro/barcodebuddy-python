"""USB Scanner handler using evdev."""
import evdev
import threading
import logging
from typing import Callable, Optional
import time

logger = logging.getLogger(__name__)


class ScannerHandler:
    """Handle USB barcode scanner input."""

    def __init__(self, device_path: str, callback: Callable[[str], None]):
        self.device_path = device_path
        self.callback = callback
        self.device: Optional[evdev.InputDevice] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self._barcode_buffer = ""

    def start(self):
        """Start listening to scanner."""
        self.running = True
        self.thread = threading.Thread(target=self._listen, daemon=True)
        self.thread.start()
        logger.info(f"Scanner started on {self.device_path}")

    def stop(self):
        """Stop listening to scanner."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        logger.info("Scanner stopped")

    def _find_device(self) -> Optional[evdev.InputDevice]:
        """Find and open scanner device."""
        try:
            # Try specified device first
            if self.device_path:
                try:
                    device = evdev.InputDevice(self.device_path)
                    logger.info(f"Using scanner device: {device.name} ({self.device_path})")
                    return device
                except (FileNotFoundError, PermissionError) as e:
                    logger.warning(f"Could not open {self.device_path}: {e}")

            # Auto-detect: find first keyboard-like device
            devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
            for device in devices:
                if 'keyboard' in device.name.lower() or 'barcode' in device.name.lower():
                    logger.info(f"Auto-detected scanner: {device.name} ({device.path})")
                    return device

            logger.error("No scanner device found")
            return None
        except Exception as e:
            logger.error(f"Error finding scanner device: {e}")
            return None

    def _listen(self):
        """Listen for scanner input."""
        while self.running:
            try:
                if not self.device:
                    self.device = self._find_device()
                    if not self.device:
                        logger.warning("Scanner not found, retrying in 5 seconds...")
                        time.sleep(5)
                        continue

                # Read events from device
                for event in self.device.read_loop():
                    if not self.running:
                        break

                    if event.type == evdev.ecodes.EV_KEY:
                        key_event = evdev.categorize(event)
                        if key_event.keystate == key_event.key_down:
                            self._handle_key(key_event.keycode)

            except (OSError, IOError) as e:
                logger.error(f"Scanner error: {e}")
                self.device = None
                if self.running:
                    time.sleep(5)
            except Exception as e:
                logger.error(f"Unexpected scanner error: {e}")
                if self.running:
                    time.sleep(5)

    def _handle_key(self, keycode: str):
        """Handle keyboard input from scanner."""
        # Enter key - barcode complete
        if keycode in ['KEY_ENTER', 'KEY_KPENTER']:
            if self._barcode_buffer:
                logger.info(f"Barcode scanned: {self._barcode_buffer}")
                self.callback(self._barcode_buffer)
                self._barcode_buffer = ""
            return

        # Convert keycode to character
        key_map = {
            'KEY_0': '0', 'KEY_1': '1', 'KEY_2': '2', 'KEY_3': '3',
            'KEY_4': '4', 'KEY_5': '5', 'KEY_6': '6', 'KEY_7': '7',
            'KEY_8': '8', 'KEY_9': '9',
            'KEY_A': 'A', 'KEY_B': 'B', 'KEY_C': 'C', 'KEY_D': 'D',
            'KEY_E': 'E', 'KEY_F': 'F', 'KEY_G': 'G', 'KEY_H': 'H',
            'KEY_I': 'I', 'KEY_J': 'J', 'KEY_K': 'K', 'KEY_L': 'L',
            'KEY_M': 'M', 'KEY_N': 'N', 'KEY_O': 'O', 'KEY_P': 'P',
            'KEY_Q': 'Q', 'KEY_R': 'R', 'KEY_S': 'S', 'KEY_T': 'T',
            'KEY_U': 'U', 'KEY_V': 'V', 'KEY_W': 'W', 'KEY_X': 'X',
            'KEY_Y': 'Y', 'KEY_Z': 'Z',
            'KEY_MINUS': '-', 'KEY_EQUAL': '=',
        }

        if keycode in key_map:
            self._barcode_buffer += key_map[keycode]
