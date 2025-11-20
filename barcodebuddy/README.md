# Barcode Buddy (Python) - Home Assistant Add-on

Modern Python-based barcode scanner with Grocy integration, OpenFoodFacts automatic product lookup, and multi-scanner support.

![Version](https://img.shields.io/badge/version-2.4.0-blue.svg)

## 🎯 Key Features

### 🔢 **Quantity Barcodes** (v2.4.0)
Scan `BBUDDY-Q-X` to set quantity for the next product:
- `BBUDDY-Q-5` → Next scan adds 5 items
- Multiple quantities sum up: `BBUDDY-Q-2` + `BBUDDY-Q-3` = 5

### 🌐 **OpenFoodFacts Integration** (v2.3.0)
Automatic product creation from 2.5M+ products:
- Unknown barcodes → OpenFoodFacts lookup
- Automatic product creation in Grocy
- No manual data entry needed!

### 📱 **Multi-Scanner Support** (v2.2.0)
- Use multiple USB scanners simultaneously
- Automatic hot-plug detection
- Each scanner works independently

### 💻 **Modern Web UI**
- Real-time scan updates
- Manual barcode entry
- Recent scans history
- Status indicators

## 📋 Configuration

```yaml
scanner_device: "/dev/input/event3"
grocy_url: "http://homeassistant.local:9192"
grocy_api_key: "your-api-key-here"
debug: false
```

### Getting Your Grocy API Key

1. Open Grocy
2. Go to **Settings** → **Manage API Keys**
3. Click **Add** to create new key
4. Name it "Barcode Buddy"
5. Copy the key to your add-on configuration

### Scanner Device

Your USB scanner usually appears as `/dev/hidraw0`. To find yours:
- Check logs after starting the add-on
- Look for "Found accessible device" messages

## 🚀 Quick Start

### Basic Usage

1. **Start the add-on**
2. **Open Web UI** (click "Open Web UI" button)
3. **Scan a product barcode**
4. **Done!** Product is added to Grocy

### With Quantity Barcodes

1. Type `BBUDDY-Q-5` in manual input (or scan it)
2. Scan your product barcode
3. → 5 items added to Grocy

## 📖 How It Works

```
Scan Barcode
    │
    ├─ Is BBUDDY-Q-X? ──Yes──> Set quantity
    │
    └─ No
        │
        ▼
   Search in Grocy
        │
        ├─ Found ──────────────> Add to stock
        │
        └─ Not found
            │
            ▼
       Search OpenFoodFacts
            │
            ├─ Found ──> Create product ──> Add to stock
            │
            └─ Not found ──> Show error
```

## 🎨 UI Status Icons

| Icon | Meaning |
|------|---------|
| ✅ | Product added successfully |
| 🆕 | New product created & added |
| 🔢 | Quantity set for next scan |
| ❓ | Barcode not found anywhere |
| ❌ | Error occurred |

## 🔧 Troubleshooting

### Scanner Not Working

**Check device path:**
- Try `/dev/hidraw0` instead of `/dev/input/event3`
- Check add-on logs for "Found accessible device" messages

**Enable debug mode:**
```yaml
debug: true
```
Restart and check logs for detailed error messages.

### Grocy Connection Issues

**Common problems:**
- Don't include `/api` in Grocy URL
- Use port number: `http://homeassistant.local:9192`
- Verify API key in Grocy settings
- Check Grocy is running and accessible

**302 Redirect errors:**
- System automatically retries after 2 seconds
- Check logs for "Grocy connection successful"

### Products Not Created

**Check:**
1. OpenFoodFacts has the product (search on openfoodfacts.org)
2. Barcode is valid EAN/UPC format
3. Grocy locations exist (add-on uses first available)
4. Debug logs show exact error from Grocy

## 📝 Version History

| Version | Key Feature |
|---------|-------------|
| 2.4.0 | Quantity Barcodes |
| 2.3.0 | OpenFoodFacts Integration |
| 2.2.0 | Multi-Scanner Support |
| 2.1.0 | USB Scanner via hidraw |
| 2.0.0 | Python Rewrite |

See [CHANGELOG.md](../CHANGELOG.md) for detailed history.

## 🏗️ Technical Details

**Built with:**
- Python 3.11 (Alpine Linux)
- Flask 3.0 (Web Framework)
- hidraw (USB Scanner access)
- requests (API communication)

**Architecture:**
- Multi-threaded scanner handling
- Session-based Grocy API client
- Automatic retry logic for API calls
- Dynamic location/quantity unit detection

## 🤝 Support

**Getting Help:**
- Check this README and CHANGELOG
- Enable debug mode and check logs
- Report issues on GitHub

**Providing Logs:**
1. Set `debug: true`
2. Restart add-on
3. Reproduce issue
4. Copy logs from Home Assistant

## 📜 License

This add-on is provided as-is for Home Assistant users.

## 🙏 Acknowledgments

- **Original BarcodeBuddy**: [Forceu/barcodebuddy](https://github.com/Forceu/barcodebuddy)
- **OpenFoodFacts**: [World's largest open food database](https://world.openfoodfacts.org/)
- **Grocy**: [ERP beyond your fridge](https://grocy.info/)

---

Built with ❤️ using [Claude Code](https://claude.com/claude-code)
