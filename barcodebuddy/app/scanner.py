"""USB Scanner handler using hidraw - Multi-device support."""
import threading
import logging
import os
from typing import Callable, Optional, List
import time

logger = logging.getLogger(__name__)


class ScannerHandler:
    """Handle multiple USB barcode scanners via hidraw."""

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
        self.device_path = device_path  # Kept for compatibility, but not used
        self.callback = callback
        self.running = False
        self.threads: List[threading.Thread] = []
        self.active_devices: List[str] = []
        self._barcode_buffers = {}  # One buffer per device

    def start(self):
        """Start listening to all available scanners."""
        self.running = True

        # Find all available scanner devices
        devices = self._find_all_devices()

        if not devices:
            logger.warning("No scanner devices found, will retry...")
            # Start a monitoring thread that looks for devices
            monitor_thread = threading.Thread(target=self._monitor_devices, daemon=True)
            monitor_thread.start()
            self.threads.append(monitor_thread)
        else:
            # Start a thread for each device
            for device in devices:
                thread = threading.Thread(target=self._listen_device, args=(device,), daemon=True)
                thread.start()
                self.threads.append(thread)
                self.active_devices.append(device)
                logger.info(f"📱 Started scanner thread for: {device}")

        logger.info(f"Scanner handler started (monitoring {len(self.active_devices)} devices)")

    def stop(self):
        """Stop listening to all scanners."""
        self.running = False
        for thread in self.threads:
            thread.join(timeout=2)
        logger.info("Scanner stopped")

    def _find_all_devices(self) -> List[str]:
        """Find all accessible scanner devices."""
        devices = []

        # Try all hidraw devices
        for i in range(20):  # Check up to 20 hidraw devices
            hidraw = f"/dev/hidraw{i}"
            if os.path.exists(hidraw):
                try:
                    # Test if we can open it
                    with open(hidraw, 'rb') as f:
                        devices.append(hidraw)
                        logger.info(f"✅ Found accessible device: {hidraw}")
                except Exception as e:
                    logger.debug(f"Cannot access {hidraw}: {e}")
                    continue

        # Fallback: try input event devices if no hidraw found
        if not devices:
            for i in range(10):
                event_dev = f"/dev/input/event{i}"
                if os.path.exists(event_dev):
                    try:
                        with open(event_dev, 'rb') as f:
                            devices.append(event_dev)
                            logger.info(f"✅ Found accessible device: {event_dev}")
                    except:
                        continue

        return devices

    def _monitor_devices(self):
        """Monitor for new scanner devices and start listening to them."""
        logger.info("🔍 Device monitor started")
        while self.running:
            # Check for new devices every 5 seconds
            time.sleep(5)

            current_devices = self._find_all_devices()

            # Start threads for any new devices
            for device in current_devices:
                if device not in self.active_devices:
                    logger.info(f"🆕 New device detected: {device}")
                    thread = threading.Thread(target=self._listen_device, args=(device,), daemon=True)
                    thread.start()
                    self.threads.append(thread)
                    self.active_devices.append(device)

    def _listen_device(self, device: str):
        """Listen to a specific device."""
        logger.info(f"👂 Listening to: {device}")
        self._barcode_buffers[device] = ""

        while self.running:
            try:
                is_hidraw = 'hidraw' in device

                if is_hidraw:
                    self._listen_hidraw(device)
                else:
                    self._listen_input_event(device)

            except PermissionError:
                logger.error(f"❌ Permission denied: {device}")
                break
            except Exception as e:
                logger.error(f"❌ Error on {device}: {e}")
                if self.running:
                    time.sleep(5)

        # Remove from active devices when thread exits
        if device in self.active_devices:
            self.active_devices.remove(device)
        logger.info(f"🛑 Stopped listening to: {device}")

    def _listen_hidraw(self, device: str):
        """Listen to HID raw device."""
        with open(device, 'rb') as f:
            while self.running:
                try:
                    # Read HID report (8 bytes for keyboard)
                    data = f.read(8)
                    if len(data) < 8:
                        break

                    # Parse HID keyboard report
                    modifier = data[0]
                    keys = data[2:8]

                    # Process each key
                    for key_code in keys:
                        if key_code == 0:
                            continue

                        # Check for Enter (HID code 40)
                        if key_code == 40:
                            if self._barcode_buffers[device]:
                                barcode = self._barcode_buffers[device]
                                logger.info(f"📦 Barcode from {device}: {barcode}")
                                self.callback(barcode)
                                self._barcode_buffers[device] = ""
                            continue

                        # Map HID code to character
                        if key_code in self.HID_TO_CHAR:
                            char = self.HID_TO_CHAR[key_code]
                            self._barcode_buffers[device] += char

                except Exception as e:
                    if self.running:
                        logger.debug(f"HID read error on {device}: {e}")
                    break

    def _listen_input_event(self, device: str):
        """Listen to Linux input event device."""
        import struct

        with open(device, 'rb') as f:
            event_size = 24

            while self.running:
                try:
                    data = f.read(event_size)
                    if len(data) < event_size:
                        break

                    # Parse input event
                    _, _, ev_type, code, value = struct.unpack('llHHI', data)

                    # EV_KEY = 1, key down = 1
                    if ev_type == 1 and value == 1:
                        self._handle_input_keycode(device, code)

                except Exception as e:
                    if self.running:
                        logger.debug(f"Input event read error on {device}: {e}")
                    break

    def _handle_input_keycode(self, device: str, code: int):
        """Handle Linux input event keycode."""
        # Enter key (code 28)
        if code == 28:
            if self._barcode_buffers.get(device):
                barcode = self._barcode_buffers[device]
                logger.info(f"📦 Barcode from {device}: {barcode}")
                self.callback(barcode)
                self._barcode_buffers[device] = ""
            return

        # Initialize buffer if needed
        if device not in self._barcode_buffers:
            self._barcode_buffers[device] = ""

        # Number keys (codes 2-11)
        if 2 <= code <= 11:
            num = str((code - 1) % 10)
            self._barcode_buffers[device] += num
            return

        # Letter keys
        letter_map = {
            16: 'Q', 17: 'W', 18: 'E', 19: 'R', 20: 'T', 21: 'Y', 22: 'U', 23: 'I', 24: 'O', 25: 'P',
            30: 'A', 31: 'S', 32: 'D', 33: 'F', 34: 'G', 35: 'H', 36: 'J', 37: 'K', 38: 'L',
            44: 'Z', 45: 'X', 46: 'C', 47: 'V', 48: 'B', 49: 'N', 50: 'M',
            12: '-', 13: '=',
        }

        if code in letter_map:
            self._barcode_buffers[device] += letter_map[code]
