"""USB Scanner handler using hidraw."""
import threading
import logging
import os
from typing import Callable, Optional
import time

logger = logging.getLogger(__name__)


class ScannerHandler:
    """Handle USB barcode scanner input via hidraw."""

    # HID Usage codes to characters mapping (US Keyboard layout)
    HID_TO_CHAR = {
        4: 'A', 5: 'B', 6: 'C', 7: 'D', 8: 'E', 9: 'F', 10: 'G', 11: 'H',
        12: 'I', 13: 'J', 14: 'K', 15: 'L', 16: 'M', 17: 'N', 18: 'O', 19: 'P',
        20: 'Q', 21: 'R', 22: 'S', 23: 'T', 24: 'U', 25: 'V', 26: 'W', 27: 'X',
        28: 'Y', 29: 'Z',
        30: '1', 31: '2', 32: '3', 33: '4', 34: '5',
        35: '6', 36: '7', 37: '8', 38: '9', 39: '0',
        40: '\n',  # Enter
        45: '-', 46: '=', 47: '[', 48: ']',
    }

    def __init__(self, device_path: str, callback: Callable[[str], None]):
        self.device_path = device_path
        self.callback = callback
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

    def _find_device(self) -> Optional[str]:
        """Find scanner device - try hidraw first, then input events."""
        # Try hidraw devices first (they work better!)
        for i in range(10):
            hidraw = f"/dev/hidraw{i}"
            if os.path.exists(hidraw):
                try:
                    with open(hidraw, 'rb') as f:
                        logger.info(f"Found accessible hidraw device: {hidraw}")
                        return hidraw
                except:
                    continue

        # Fallback to specified device
        if self.device_path and os.path.exists(self.device_path):
            try:
                with open(self.device_path, 'rb') as f:
                    logger.info(f"Using specified device: {self.device_path}")
                    return self.device_path
            except PermissionError:
                logger.warning(f"Permission denied for {self.device_path}")
            except Exception as e:
                logger.warning(f"Could not open {self.device_path}: {e}")

        # Try input event devices
        for i in range(10):
            device = f"/dev/input/event{i}"
            if os.path.exists(device):
                try:
                    with open(device, 'rb') as f:
                        logger.info(f"Found accessible event device: {device}")
                        return device
                except:
                    continue

        logger.error("No accessible scanner device found")
        return None

    def _listen(self):
        """Listen for scanner input."""
        while self.running:
            device = self._find_device()
            if not device:
                logger.warning("Scanner not found, retrying in 5 seconds...")
                time.sleep(5)
                continue

            try:
                is_hidraw = 'hidraw' in device

                if is_hidraw:
                    self._listen_hidraw(device)
                else:
                    self._listen_input_event(device)

            except PermissionError:
                logger.error(f"Permission denied accessing {device}")
                time.sleep(5)
            except Exception as e:
                logger.error(f"Scanner error: {e}")
                if self.running:
                    time.sleep(5)

    def _listen_hidraw(self, device: str):
        """Listen to HID raw device."""
        logger.info(f"Listening to HID device: {device}")

        with open(device, 'rb') as f:
            while self.running:
                try:
                    # Read HID report (8 bytes for keyboard)
                    data = f.read(8)
                    if len(data) < 8:
                        continue

                    # Parse HID keyboard report
                    # Byte 0: Modifier keys
                    # Byte 1: Reserved
                    # Bytes 2-7: Key codes
                    modifier = data[0]
                    keys = data[2:8]

                    # Process each key
                    for key_code in keys:
                        if key_code == 0:
                            continue

                        # Check for Enter (HID code 40)
                        if key_code == 40:
                            if self._barcode_buffer:
                                logger.info(f"Barcode scanned (HID): {self._barcode_buffer}")
                                self.callback(self._barcode_buffer)
                                self._barcode_buffer = ""
                            continue

                        # Map HID code to character
                        if key_code in self.HID_TO_CHAR:
                            char = self.HID_TO_CHAR[key_code]
                            self._barcode_buffer += char
                            logger.debug(f"HID key: {key_code} -> {char}")

                except Exception as e:
                    if self.running:
                        logger.debug(f"HID read error: {e}")
                    break

    def _listen_input_event(self, device: str):
        """Listen to Linux input event device."""
        logger.info(f"Listening to input event device: {device}")

        with open(device, 'rb') as f:
            # Event format: timestamp (16 bytes) + type (2) + code (2) + value (4)
            event_size = 24

            while self.running:
                try:
                    data = f.read(event_size)
                    if len(data) < event_size:
                        break

                    # Parse input event
                    import struct
                    _, _, ev_type, code, value = struct.unpack('llHHI', data)

                    # EV_KEY = 1, key down = 1
                    if ev_type == 1 and value == 1:
                        self._handle_input_keycode(code)

                except Exception as e:
                    if self.running:
                        logger.debug(f"Input event read error: {e}")
                    break

    def _handle_input_keycode(self, code: int):
        """Handle Linux input event keycode."""
        # Enter key (code 28)
        if code == 28:
            if self._barcode_buffer:
                logger.info(f"Barcode scanned (input): {self._barcode_buffer}")
                self.callback(self._barcode_buffer)
                self._barcode_buffer = ""
            return

        # Number keys (codes 2-11)
        if 2 <= code <= 11:
            num = str((code - 1) % 10)
            self._barcode_buffer += num
            return

        # Letter keys
        letter_map = {
            16: 'Q', 17: 'W', 18: 'E', 19: 'R', 20: 'T', 21: 'Y', 22: 'U', 23: 'I', 24: 'O', 25: 'P',
            30: 'A', 31: 'S', 32: 'D', 33: 'F', 34: 'G', 35: 'H', 36: 'J', 37: 'K', 38: 'L',
            44: 'Z', 45: 'X', 46: 'C', 47: 'V', 48: 'B', 49: 'N', 50: 'M',
            12: '-', 13: '=',
        }

        if code in letter_map:
            self._barcode_buffer += letter_map[code]
