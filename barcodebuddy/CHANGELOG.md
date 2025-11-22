# Changelog

All notable changes to Barcode Buddy (Python) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.9.5-beta] - 2025-11-22

### Changed
- Reorganized config.yaml with clear sections (Grocy, Barcode Config, Product Databases, Debug)
- Improved readability of add-on configuration options

## [2.9.4-beta] - 2025-11-22

### Removed
- **EAN-Search.org** database integration (requires paid API key - 401 Unauthorized errors)
- `enable_eansearch` configuration option

### Changed
- Database lookup now only uses OpenFoodFacts and UPC Database (both free)
- "Not found" message updated to reflect available databases

## [2.9.3-beta] - 2025-11-22

### Fixed
- CHANGELOG.md now in correct location for Home Assistant add-on directory
- Fixes "No changelog found for add-on" message in Home Assistant update dialog

## [2.9.2-beta] - 2025-11-22

### Added
- **Configurable Product Databases**: Enable/disable individual online databases via add-on configuration
- Configuration options: `enable_openfoodfacts`, `enable_eansearch`, `enable_upcdatabase`
- All databases enabled by default for maximum barcode coverage

### Changed
- Database queries now respect configuration settings (only enabled databases are queried)
- Improved efficiency by skipping disabled databases

## [2.9.1-beta] - 2025-11-22

### Added
- **EAN-Search.org** database integration (free, no API key needed)
- **UPC Database** integration (free tier, ~100 requests/day)
- Multi-database lookup chain for better barcode coverage

### Changed
- Lookup order: Grocy → OpenFoodFacts → EAN-Search → UPC Database
- UI shows which database product was found in (e.g., "Created from EAN-Search")
- "Not found" message now lists all 4 databases

## [2.9.0-beta] - 2025-11-22

### Changed
- Prepared new_features branch for next development cycle
- Version bump for future features

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

## [2.7.3-beta] - 2025-11-22

### Removed
- Removed unused scanner_device configuration option (fully automatic now)

### Changed
- Startup log message updated to reflect auto-detection

## [2.7.2-beta] - 2025-11-22

### Fixed
- Auto-refresh blocking product name input field
- Allow refresh when input is disabled (creation in progress)

## [2.7.1-beta] - 2025-11-22

### Fixed
- Product creation refresh timing issues

## [2.7.0-beta] - 2025-11-22

### Added
- **Product Creation from UI**: When barcode not found, show input field for product name
- Automatic product creation in Grocy with barcode association
- Automatic stock addition after product creation

## [2.6.2-beta] - 2025-11-22

### Fixed
- UI scanner device display now shows actual active devices instead of config value

## [2.6.1-beta] - 2025-11-22

### Added
- Configurable special barcode texts (barcode_add, barcode_consume, barcode_quantity_prefix)

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
| 2.9.1-beta | 2025-11-22 | EAN-Search & UPC Database |
| 2.8.0 | 2025-11-22 | Product Creation UI & Mode Switching |
| 2.7.0-beta | 2025-11-22 | Manual Product Creation |
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
