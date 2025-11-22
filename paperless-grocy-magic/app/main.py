"""Main Flask application for Paperless Grocy Magic."""
import logging
from flask import Flask, render_template, jsonify, request
from config import config
from datetime import datetime
from grocy_client import GrocyClient
from price_updater import PriceUpdateService

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if config.debug else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'paperless-grocy-magic-secret'

# Initialize Grocy client and price updater
grocy_client = None
price_updater = None

if config.grocy_url and config.grocy_api_key:
    try:
        grocy_client = GrocyClient(config.grocy_url, config.grocy_api_key)
        if grocy_client.test_connection():
            price_updater = PriceUpdateService(grocy_client, config.fuzzy_match_threshold)
            logger.info("✅ Grocy client initialized successfully")
        else:
            logger.error("❌ Grocy connection test failed")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Grocy client: {e}")
else:
    logger.warning("⚠️  Grocy not configured")


@app.route('/')
def index():
    """Main dashboard with test UI."""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Paperless Grocy Magic - Test UI</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 20px auto; padding: 20px; }
        h1 { color: #333; }
        .container { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .panel { border: 1px solid #ddd; border-radius: 8px; padding: 20px; }
        textarea { width: 100%; height: 300px; font-family: monospace; font-size: 12px; }
        button { background: #4CAF50; color: white; padding: 12px 24px; border: none;
                 border-radius: 4px; cursor: pointer; font-size: 16px; margin: 10px 5px; }
        button:hover { background: #45a049; }
        button.secondary { background: #2196F3; }
        button.secondary:hover { background: #0b7dda; }
        #result { background: #f5f5f5; padding: 15px; border-radius: 4px;
                  white-space: pre-wrap; font-family: monospace; font-size: 12px;
                  max-height: 500px; overflow-y: auto; }
        .status { margin: 10px 0; padding: 10px; background: #e3f2fd; border-radius: 4px; }
        .success { color: #4CAF50; }
        .error { color: #f44336; }
    </style>
</head>
<body>
    <h1>🪄 Paperless Grocy Magic - Test UI</h1>

    <div class="status" id="status">Loading status...</div>

    <div class="container">
        <div class="panel">
            <h2>📄 Receipt Text</h2>
            <textarea id="receiptText">REWE MARKT
Homburger Landstr. 340-352
60433 Frankfurter-Berg
UID Nr.: DE812706034
EUR
SW-VORDERHAXE 7,98 B
BIERSCHINKEN 1,29 B
SCHUPFNUDELN 1,79 B
KARTOFFEL FESTK 1,99 B
GELBE ZWIEBELN 1,09 B
Deutschland / Hk 0,44 B
 0,340 kg x 1,29 EUR/kg
BW SENFK 2,79 B
GAULOISES ROT 23,00 A *
--------------------------------------
SUMME EUR 40,37
Datum: 22.11.2025</textarea>

            <div>
                <button onclick="processReceipt()">🚀 Process Receipt</button>
                <button onclick="clearResult()" class="secondary">🗑️ Clear</button>
            </div>
        </div>

        <div class="panel">
            <h2>📊 Result</h2>
            <div id="result">Click "Process Receipt" to test...</div>
        </div>
    </div>

    <script>
        // Get base URL (works with Ingress and direct access)
        const baseUrl = window.location.pathname.replace(/\/$/, '');

        // Load status on page load
        fetch(baseUrl + '/api/status')
            .then(r => r.json())
            .then(data => {
                const grocy = data.grocy.connected ? '✅ Connected' : '❌ Not connected';
                const products = data.grocy.product_count ? ` (${data.grocy.product_count} products)` : '';
                document.getElementById('status').innerHTML =
                    `<strong>Status:</strong> ${data.status} |
                     <strong>Version:</strong> ${data.version} |
                     <strong>Grocy:</strong> ${grocy}${products}`;
            })
            .catch(e => {
                document.getElementById('status').innerHTML =
                    '<span class="error">Error loading status</span>';
            });

        function processReceipt() {
            const text = document.getElementById('receiptText').value;
            const resultDiv = document.getElementById('result');

            resultDiv.innerHTML = '⏳ Processing receipt...';

            fetch(baseUrl + '/api/process-receipt', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    text: text,
                    store: 'rewe'
                })
            })
            .then(r => {
                if (!r.ok) {
                    return r.text().then(text => {
                        throw new Error(`HTTP ${r.status}: ${text}`);
                    });
                }
                return r.json();
            })
            .then(data => {
                // Format result nicely
                let output = '';

                if (data.success) {
                    output += `<span class="success">✅ SUCCESS!</span>\\n\\n`;
                } else {
                    output += `<span class="error">❌ FAILED</span>\\n\\n`;
                }

                output += `📍 Store: ${data.store || 'N/A'}\\n`;
                output += `📅 Date: ${data.date || 'N/A'}\\n`;
                output += `📦 Total Items: ${data.total_items || 0}\\n`;
                output += `✅ Updated: ${data.updated || 0}\\n`;
                output += `✨ Created: ${data.created || 0}\\n`;
                output += `❌ Failed: ${data.failed || 0}\\n`;
                output += `⚠️  Unmatched: ${data.unmatched || 0}\\n\\n`;

                if (data.matches && data.matches.length > 0) {
                    output += '📋 Matches:\\n';
                    output += '─'.repeat(60) + '\\n';

                    data.matches.forEach((m, i) => {
                        let status = '❌';
                        if (m.created) {
                            status = '✨';  // Created new product
                        } else if (m.matched) {
                            status = '✅';  // Updated existing
                        }

                        output += `${i+1}. ${status} ${m.receipt_item}\\n`;

                        if (m.created) {
                            output += `   ✨ Created new product: ${m.grocy_product}\\n`;
                            output += `   💰 Price: ${m.price.toFixed(2)}€\\n`;
                        } else if (m.matched) {
                            output += `   → ${m.grocy_product} (score: ${m.score})\\n`;
                            output += `   💰 Price: ${m.price.toFixed(2)}€\\n`;
                        } else {
                            output += `   ⚠️  No match found in Grocy\\n`;
                        }
                        output += '\\n';
                    });
                }

                if (data.errors && data.errors.length > 0) {
                    output += '\\n🚨 Errors:\\n';
                    data.errors.forEach(e => output += `  - ${e}\\n`);
                }

                output += '\\n' + '─'.repeat(60) + '\\n';
                output += 'Raw JSON:\\n' + JSON.stringify(data, null, 2);

                resultDiv.innerHTML = output;
            })
            .catch(e => {
                resultDiv.innerHTML = `<span class="error">❌ Error: ${e.message}</span>`;
            });
        }

        function clearResult() {
            document.getElementById('result').innerHTML = 'Click "Process Receipt" to test...';
        }
    </script>
</body>
</html>
"""


@app.route('/api/status')
def status():
    """API status endpoint."""
    grocy_status = {
        'url': config.grocy_url if config.grocy_url else 'not configured',
        'configured': bool(config.grocy_url and config.grocy_api_key),
        'connected': grocy_client is not None and price_updater is not None
    }

    # Test Grocy connection
    if grocy_client:
        try:
            products = grocy_client.get_all_products()
            grocy_status['product_count'] = len(products)
        except Exception as e:
            grocy_status['error'] = str(e)

    return jsonify({
        'status': 'ok',
        'paperless': {
            'url': config.paperless_url if config.paperless_url else 'not configured',
            'configured': bool(config.paperless_url and config.paperless_api_key)
        },
        'grocy': grocy_status,
        'settings': {
            'auto_process': config.auto_process_receipts,
            'interval_hours': config.process_interval_hours,
            'fuzzy_threshold': config.fuzzy_match_threshold,
            'supported_stores': config.supported_stores
        }
    })


@app.route('/api/process-receipt', methods=['POST'])
def process_receipt():
    """Process receipt text and update Grocy prices."""
    logger.info("Received receipt processing request")

    if not price_updater:
        logger.error("Price updater not initialized")
        return jsonify({
            'success': False,
            'error': 'Grocy not configured or connection failed'
        }), 503

    try:
        data = request.get_json()
        if not data or 'text' not in data:
            logger.warning("Missing receipt text in request")
            return jsonify({
                'success': False,
                'error': 'Missing receipt text in request body'
            }), 400

        receipt_text = data.get('text')
        store_hint = data.get('store', None)

        logger.info(f"Processing receipt for store: {store_hint}")

        result = price_updater.process_receipt_text(receipt_text, store_hint)

        logger.info(f"Receipt processed: {result.updated_count} updated, {result.unmatched_count} unmatched")

        return jsonify(result.to_dict())

    except Exception as e:
        logger.error(f"Error processing receipt: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    logger.info("🪄 Paperless Grocy Magic starting...")
    logger.info(f"Paperless: {'✓' if config.paperless_url else '✗'}")
    logger.info(f"Grocy: {'✓' if config.grocy_url else '✗'}")

    app.run(
        host='0.0.0.0',
        port=5001,
        debug=config.debug
    )
