"""USB Scanner handler using subprocess."""
import subprocess
import threading
import logging
import struct
import os
from typing import Callable, Optional
import time

logger = logging.getLogger(__name__)


class ScannerHandler:
    """Handle USB barcode scanner input."""

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
        """Find scanner device."""
        # Try specified device first
        if self.device_path and os.path.exists(self.device_path):
            try:
                # Test if we can read from device
                with open(self.device_path, 'rb') as f:
                    logger.info(f"Using scanner device: {self.device_path}")
                    return self.device_path
            except PermissionError as e:
                logger.warning(f"Permission denied for {self.device_path}: {e}")
            except Exception as e:
                logger.warning(f"Could not open {self.device_path}: {e}")

        # Auto-detect: try common event devices
        for i in range(10):
            device = f"/dev/input/event{i}"
            if os.path.exists(device):
                try:
                    with open(device, 'rb') as f:
                        logger.info(f"Auto-detected scanner: {device}")
                        return device
                except:
                    continue

        logger.error("No scanner device found")
        return None

    def _listen(self):
        """Listen for scanner input using raw device read."""
        while self.running:
            device = self._find_device()
            if not device:
                logger.warning("Scanner not found, retrying in 5 seconds...")
                time.sleep(5)
                continue

            try:
                # Open device for reading
                with open(device, 'rb') as f:
                    logger.info(f"Listening to scanner on {device}")

                    # Event format: timestamp (8 bytes) + type (2) + code (2) + value (4)
                    event_size = 24

                    while self.running:
                        try:
                            data = f.read(event_size)
                            if len(data) < event_size:
                                break

                            # Parse event (struct format: llHHI for 64-bit)
                            _, _, ev_type, code, value = struct.unpack('llHHI', data)

                            # EV_KEY = 1, key down = 1
                            if ev_type == 1 and value == 1:
                                self._handle_keycode(code)

                        except Exception as e:
                            if self.running:
                                logger.debug(f"Read error: {e}")
                            break

            except PermissionError:
                logger.error(f"Permission denied accessing {device}")
                time.sleep(5)
            except Exception as e:
                logger.error(f"Scanner error: {e}")
                if self.running:
                    time.sleep(5)

    def _handle_keycode(self, code: int):
        """Handle keyboard input code from scanner."""
        # Enter key (code 28) - barcode complete
        if code == 28:
            if self._barcode_buffer:
                logger.info(f"Barcode scanned: {self._barcode_buffer}")
                self.callback(self._barcode_buffer)
                self._barcode_buffer = ""
            return

        # Number keys (codes 2-11 for 1-9, 0)
        if 2 <= code <= 11:
            num = str((code - 1) % 10)
            self._barcode_buffer += num
            return

        # Letter keys (codes 16-25 for Q-P, 30-38 for A-L, 44-50 for Z-M)
        letter_map = {
            16: 'Q', 17: 'W', 18: 'E', 19: 'R', 20: 'T', 21: 'Y', 22: 'U', 23: 'I', 24: 'O', 25: 'P',
            30: 'A', 31: 'S', 32: 'D', 33: 'F', 34: 'G', 35: 'H', 36: 'J', 37: 'K', 38: 'L',
            44: 'Z', 45: 'X', 46: 'C', 47: 'V', 48: 'B', 49: 'N', 50: 'M',
            12: '-', 13: '=',
        }

        if code in letter_map:
            self._barcode_buffer += letter_map[code]
