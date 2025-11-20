# Barcode Buddy (Python) - Home Assistant Add-on

Modern Python-based barcode scanner with Grocy integration.

## Features

✅ **Simple & Clean** - Minimal Python implementation
✅ **USB Scanner Support** - Automatic device detection
✅ **Grocy Integration** - Direct API integration
✅ **Web UI** - Beautiful, responsive interface
✅ **Manual Entry** - Keyboard input supported
✅ **Real-time Updates** - Live scan feed
✅ **Extensible** - Easy to add features

## Configuration

```yaml
scanner_device: "/dev/input/event3"  # USB scanner device
grocy_url: "http://your-grocy-url"   # Grocy instance URL
grocy_api_key: "your-api-key"        # Grocy API key
debug: false                          # Enable debug logging
```

## Usage

1. Install add-on from repository
2. Configure Grocy URL and API key (optional)
3. Start add-on
4. Open Web UI
5. Scan barcodes or enter manually

## Without Grocy

The add-on works standalone without Grocy - just leave the Grocy fields empty. Scans will be logged but not sent to Grocy.

## Development

Built with:
- Python 3.11
- Flask (Web Framework)
- evdev (USB Scanner)
- requests (Grocy API)

## Version 2.0.0

Complete rewrite in Python for better maintainability and extensibility.
