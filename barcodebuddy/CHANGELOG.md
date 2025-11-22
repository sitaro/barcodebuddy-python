# Changelog

All notable changes to Barcode Buddy (Python) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.10.0] - 2025-11-22

### Added
- **PDF Barcode Generator**: Download printable control barcodes as PDF
- Mode control barcodes: ADD and CONSUME (BBUDDY-ADD, BBUDDY-CONSUME)
- Quantity control barcodes: 3-10, 20, 30 (BBUDDY-Q-X)
- PDF opens in new browser tab for easy printing
- Code128 barcode format using reportlab's built-in support
- Multi-language support for PDF download button (en/de/fr/es)

## [2.9.0] - 2025-11-22

### Added
- **Multi-Language Support**: UI now available in English, German, French, and Spanish
- Flask-Babel integration for internationalization (i18n)
- Language selection via add-on configuration (en/de/fr/es)
- All UI text now translatable with complete translation files

### Changed
- Default language set to English (en)
- Reorganized config.yaml with clear sections (Grocy, Barcode Config, Product Databases, Language, Debug)

### Removed
- **EAN-Search.org** database integration (requires paid API key)
- `enable_eansearch` configuration option

## [2.8.0] - 2025-11-22

### Added
- **Product Creation UI**: Create products from unknown barcodes directly in the web interface
- **Mode Switching**: Toggle between Add/Consume modes with special barcodes (BBUDDY-ADD / BBUDDY-CONSUME)
- Configurable special barcode texts in add-on configuration
- Input field appears for unknown barcodes to enter product name manually

### Changed
- **Auto-detection** of all scanner devices (hidraw and input/event)
- Active scanner devices now displayed in UI
- Removed unused scanner_device configuration option
- Enhanced UI responsiveness

### Fixed
- Auto-refresh pauses while typing product name
- Product creation refresh issues resolved
- Button state management during product creation

## [2.6.0] - 2025-11-22

### Added
- MIT License
- Initial stable release with all beta features

## [2.5.0] - 2025-11-22

### Added
- **Mode Switching**: BBUDDY-ADD and BBUDDY-CONSUME barcodes
- Persistent mode state (add/consume)
- Mode indicator (🔄) in UI

## [2.4.3] - 2025-11-22

### Fixed
- Quantity calculation off-by-one error (was adding 11 instead of 10)
- Quantity now starts at 0, defaults to 1 if no quantity barcode scanned

## [2.4.2] - 2025-11-22

### Fixed
- Nested product structure handling from Grocy API

## [2.4.1] - 2025-11-22

### Fixed
- Grocy API compatibility issues

## [2.4.0] - 2025-11-20

### Added
- **Quantity Barcodes**: Scan `BBUDDY-Q-X` to set quantity for next product
- Multiple quantity barcodes are automatically summed
- UI shows quantity in parentheses: "Added: Product (3x)"
- Special 🔢 icon for quantity barcode scans

### Changed
- Quantity resets to 1 after successful product addition

### Example
```
1. Scan BBUDDY-Q-3 → "🔢 Quantity set to: 3"
2. Scan BBUDDY-Q-2 → "🔢 Quantity set to: 5"
3. Scan product → "✅ Added: Chester (5x)"
```

## [2.3.0] - 2025-11-20

### Added
- **OpenFoodFacts Integration**: Automatic product lookup and creation
- Unknown barcodes are automatically looked up in OpenFoodFacts database
- Products are created in Grocy with information from OpenFoodFacts
- Dynamic location and quantity unit ID detection from Grocy

### Changed
- Enhanced workflow: Grocy search → OpenFoodFacts lookup → Create product → Add to stock
- Better error messages showing exact Grocy API responses

### Fixed
- Product creation compatibility with different Grocy versions
- NOT NULL constraint errors by querying available locations
- Handling of 400/404 responses from Grocy API

## [2.2.0] - 2025-11-20

### Added
- **Multi-Scanner Support**: Automatic detection and simultaneous use of multiple USB scanners
- Hot-plug detection: New scanners are detected automatically every 5 seconds
- Each scanner works independently with its own buffer
- Support for up to 20 hidraw devices

### Changed
- Scanner handler now uses threading for concurrent device monitoring
- Improved device detection and error handling

## [2.1.0] - 2025-11-20

### Added
- **USB Scanner Support via hidraw**: Switched from evdev to hidraw devices
- HID report parsing for keyboard emulation mode
- Support for `/dev/hidraw0-4` devices

### Fixed
- Scanner device permission issues with `/dev/input/event*`
- Kernel kbd handler conflicts resolved by using hidraw

## [2.0.0] - 2025-11-20

### Added
- **Complete Python Rewrite**: Rebuilt from scratch in Python/Flask
- Modern web UI with real-time updates
- Grocy API integration
- Home Assistant Add-on architecture
- Multi-architecture Docker support (armhf, armv7, aarch64, amd64, i386)
- Scanner device configuration
- Debug mode with detailed logging

### Removed
- Legacy PHP/bash implementation

---

## Version History Summary

| Version | Date | Key Feature |
|---------|------|-------------|
| 2.10.0 | 2025-11-22 | PDF Barcode Generator |
| 2.9.0 | 2025-11-22 | Multi-Language Support |
| 2.8.0 | 2025-11-22 | Product Creation UI & Mode Switching |
| 2.6.0 | 2025-11-22 | Stable Release |
| 2.5.0 | 2025-11-22 | Mode Switching (Add/Consume) |
| 2.4.0 | 2025-11-20 | Quantity Barcodes (BBUDDY-Q-X) |
| 2.3.0 | 2025-11-20 | OpenFoodFacts Integration |
| 2.2.0 | 2025-11-20 | Multi-Scanner Support |
| 2.1.0 | 2025-11-20 | USB Scanner via hidraw |
| 2.0.0 | 2025-11-20 | Python Rewrite |

---

## Migration Notes

### From v1.x (PHP/Bash) to v2.0.0+

The Python version is a complete rewrite with:
- New configuration format (config.yaml)
- Different device paths (/dev/hidraw vs /dev/input)
- Modern web interface
- Better error handling
- OpenFoodFacts integration built-in

### Configuration Changes
- Scanner device now uses hidraw: `/dev/hidraw0` instead of `/dev/input/event3`
- Grocy URL should not include `/api` suffix
- API keys are validated on startup with automatic retry

---

## Contributing

Built with ❤️ using [Claude Code](https://claude.com/claude-code)
