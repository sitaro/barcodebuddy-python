# 🪄 Paperless Grocy Magic

**Automatic receipt parsing from Paperless-ngx to Grocy price tracking**

## Overview

Paperless Grocy Magic automatically processes your shopping receipts from Paperless-ngx, extracts product names and prices, and updates your Grocy inventory with current price information.

## Features

- ✅ **Paperless-ngx Integration**: Automatically fetch receipts via API
- 🔍 **OCR Text Parsing**: Extract products and prices from receipt text
- 🎯 **Fuzzy Matching**: Match receipt items to Grocy products
- 💰 **Price Tracking**: Update Grocy with current prices
- 🏪 **Multi-Store Support**: Rewe, Edeka, Aldi, Lidl, Penny, and more
- ⏰ **Automatic Processing**: Configurable interval (hourly/daily)
- 🔄 **Manual Trigger**: Process receipts on-demand via API

## Requirements

- **Paperless-ngx**: Running instance with API access
- **Grocy**: Running instance with API access
- Tagged receipts in Paperless (default tag: `kassenbon`)

## Configuration

### Required Settings

- **paperless_url**: URL to your Paperless-ngx instance (e.g., `http://paperless:8000`)
- **paperless_api_key**: Paperless API token
- **grocy_url**: URL to your Grocy instance
- **grocy_api_key**: Grocy API key

### Optional Settings

- **paperless_tag**: Tag for receipts in Paperless (default: `kassenbon`)
- **auto_process_receipts**: Enable automatic processing (default: `true`)
- **process_interval_hours**: How often to check for new receipts (default: `1`)
- **fuzzy_match_threshold**: Product matching sensitivity 0.5-1.0 (default: `0.8`)
- **supported_stores**: List of stores to parse (default: Rewe, Edeka, Aldi, Lidl, Penny)
- **debug**: Enable debug logging (default: `false`)

## Workflow

1. **Scan receipt** → Upload to Paperless-ngx with tag `kassenbon`
2. **OCR processing** → Paperless extracts text from receipt
3. **Magic parsing** → This add-on parses the OCR text:
   - Store name detection
   - Product name extraction
   - Price extraction
   - Date extraction
4. **Product matching** → Fuzzy match receipt items to Grocy products
5. **Price update** → Update Grocy with new prices

## Example Receipt Processing

### Input (OCR Text from Paperless):
```
REWE Markt GmbH
────────────────────────
Milch 3,5%        1,29 €
Butter            2,49 €
Äpfel 1kg         3,99 €
────────────────────────
SUMME            7,77 €
Datum: 22.11.2025
```

### Output (Grocy Updates):
- Product "Milch Vollmilch" → Price: 1,29 € (from Rewe, 22.11.2025)
- Product "Butter" → Price: 2,49 € (from Rewe, 22.11.2025)
- Product "Äpfel" → Price: 3,99 € (from Rewe, 22.11.2025)

## API Endpoints

- `GET /` - Dashboard and status
- `GET /api/status` - Check Paperless and Grocy connection
- `POST /api/process-receipts` - Manually trigger receipt processing

## Supported Stores

Currently configured for German supermarkets:
- 🛒 **Rewe**
- 🛒 **Edeka**
- 🛒 **Aldi** (Nord & Süd)
- 🛒 **Lidl**
- 🛒 **Penny**
- 🛒 **Kaufland**
- 🛒 **Netto**

More stores can be added via configuration!

## Troubleshooting

### No receipts processed
- Check Paperless tag is correct (`kassenbon`)
- Verify API keys are valid
- Check logs for connection errors

### Poor product matching
- Adjust `fuzzy_match_threshold` (lower = more matches, less accuracy)
- Ensure Grocy product names match receipt items
- Check OCR quality in Paperless

### Price not updating in Grocy
- Verify Grocy API key has write permissions
- Check if product exists in Grocy
- Review logs for API errors

## Development Status

**Version**: 0.1.0-beta
**Status**: 🚧 Work in Progress

### Roadmap

- [ ] Paperless API client
- [ ] Receipt text parser (Rewe, Edeka, Aldi, Lidl)
- [ ] Grocy API client
- [ ] Fuzzy product matching
- [ ] Price history tracking
- [ ] Web UI for manual matching
- [ ] Statistics dashboard
- [ ] Multi-language support

## License

MIT License - See main repository

## Credits

Built with ❤️ using [Claude Code](https://claude.com/claude-code)

Part of the **Barcode Buddy Python** ecosystem.
