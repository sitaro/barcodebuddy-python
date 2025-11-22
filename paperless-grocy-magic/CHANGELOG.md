# Changelog - Paperless Grocy Magic

All notable changes to Paperless Grocy Magic will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.3-beta] - 2025-11-22

### Fixed
- **Enhanced error reporting** - Shows actual Grocy API error messages
- Functions now return detailed error messages instead of boolean failures
- `update_product_price()` returns `(success, error_message)` tuple
- `create_product()` returns `(product, error_message)` tuple
- Error messages include full exception details and API responses
- Easier debugging when product updates or creation fails

### Technical Details
- Added exception handling with traceback logging in grocy_client.py
- Debug logging for locations and quantity_units fetch during product creation
- Error messages now propagate from Grocy API → Service → UI/Logs
- User-visible errors show actual failure reasons (permissions, missing fields, etc.)

## [0.3.2-beta] - 2025-11-22

### Fixed
- **Grocy connection test** - Fixed "Expecting value" error with /system/info
- Added fallback to /objects/products for connection testing
- Works with Grocy instances that don't have /system/info endpoint
- More robust connection detection

### Technical Details
- Some Grocy versions/configurations don't return valid JSON from /system/info
- Now tries /system/info first, falls back to /objects/products
- Both methods validate Grocy API is accessible
- Logs which method was successful

## [0.3.1-beta] - 2025-11-22

### Fixed
- Enhanced debugging for Grocy initialization failures
- Detailed logging shows exact step where initialization fails
- Shows Grocy URL and API key prefix in error logs
- Full exception traceback for easier troubleshooting

## [0.3.0-beta] - 2025-11-22

### Added
- **Automatic Product Creation** - Unknown products are now automatically created in Grocy!
- New products get proper price and name from receipt
- UI shows ✨ icon for newly created products
- Created count in statistics (✨ Created: X)
- Separate tracking for updated vs created products

### Changed
- Unmatched products are now attempted to be created
- Success if items were updated OR created (not just updated)
- Better logging: "Created: Product (1.29€)"

### How it works
1. Parse receipt → Extract products
2. Match to existing Grocy products (fuzzy matching)
3. Update prices for matched products ✅
4. **Create new products for unmatched items** ✨ NEW!
5. Report results with created/updated/failed stats

Example:
- Receipt has "Vorderhaxe" (not in Grocy)
- ✨ Creates new Grocy product "Vorderhaxe" with price 7.98€
- Next time: Will match and update price instead

## [0.2.6-beta] - 2025-11-22

### Fixed
- **Ingress Support** - Fixed 404 error when accessing via Home Assistant Ingress
- JavaScript now uses dynamic base URL detection
- Works with both Ingress and direct port access
- API calls now use relative paths

## [0.2.5-beta] - 2025-11-22

### Fixed
- Better error handling in JavaScript (shows actual HTTP errors)
- Improved logging in receipt processing endpoint
- Full exception tracebacks in logs for easier debugging
- Clearer error messages when Grocy not configured

## [0.2.4-beta] - 2025-11-22

### Added
- **Web Test UI** - Interactive HTML interface for testing receipt processing
- Pre-filled with real REWE receipt example
- Real-time status display (Grocy connection, product count)
- Beautiful formatted results with match details
- One-click testing from browser
- No need for curl or Postman anymore!

## [0.2.3-beta] - 2025-11-22

### Changed
- **Removed python-Levenshtein** - Was causing very slow Docker builds (compilation)
- Removed build tools (gcc, musl-dev, python3-dev) - no longer needed
- Using pure Python fuzzywuzzy (slightly slower but builds in seconds)
- Drastically faster build times, especially on ARM architectures

## [0.2.2-beta] - 2025-11-22

### Fixed
- **Flask installation** - Changed from `py3-flask` (Alpine package) to `pip install flask`
- All Python packages now installed via pip for better compatibility
- Added `--break-system-packages` flag for pip3 in Alpine

## [0.2.1-beta] - 2025-11-22

### Fixed
- **Missing `jq` package** in Dockerfile - run.sh requires jq for JSON parsing
- **Missing build tools** for python-Levenshtein compilation (gcc, musl-dev, python3-dev)
- Version number in run.sh startup message

## [0.2.0-beta] - 2025-11-22

### Added
- **Receipt Parser**: Parse REWE receipts from OCR text
- **Grocy API Client**: Full integration with Grocy for product management
- **Fuzzy Product Matching**: Match receipt items to Grocy products using fuzzywuzzy
- **Price Update Service**: Automatically update Grocy product prices from receipts
- **API Endpoint**: `/api/process-receipt` for manual receipt processing
- **Example Receipt**: Real REWE receipt for testing (examples/)
- **Test Script**: Verify parser with real data

### Features
- Extract products and prices from REWE receipts
- Handle weight-based items (kg pricing)
- Match receipt items to Grocy products (configurable threshold)
- Update Grocy prices with store and date information
- Detailed API responses with match scores and statistics

### Technical
- Receipt parsing with regex patterns
- Multi-strategy fuzzy matching (ratio, partial, token sort, token set)
- Product cleaning and normalization
- Comprehensive logging and error handling

## [0.1.0-beta] - 2025-11-22

### Added
- **Initial Release**: Basic add-on structure
- Paperless-ngx API integration (configuration)
- Grocy API integration (configuration)
- Flask web application framework
- Configuration management system
- Status API endpoints
- Multi-architecture Docker support (armhf, armv7, aarch64, amd64, i386)
- Configurable store support (Rewe, Edeka, Aldi, Lidl, Penny)
- Fuzzy matching configuration

### Planned Features
- Receipt text parsing logic
- Product matching algorithm
- Price update functionality
- Automatic processing scheduler
- Web UI for manual matching
- Statistics dashboard

---

## Contributing

Built with ❤️ using [Claude Code](https://claude.com/claude-code)
