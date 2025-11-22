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
    """Main dashboard."""
    return jsonify({
        'name': 'Paperless Grocy Magic',
        'version': '0.2.0-beta',
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'config': {
            'paperless_configured': bool(config.paperless_url and config.paperless_api_key),
            'grocy_configured': bool(config.grocy_url and config.grocy_api_key),
            'auto_process': config.auto_process_receipts,
            'interval_hours': config.process_interval_hours
        }
    })


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
    if not price_updater:
        return jsonify({
            'success': False,
            'error': 'Grocy not configured or connection failed'
        }), 503

    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing receipt text in request body'
        }), 400

    receipt_text = data.get('text')
    store_hint = data.get('store', None)

    try:
        result = price_updater.process_receipt_text(receipt_text, store_hint)
        return jsonify(result.to_dict())
    except Exception as e:
        logger.error(f"Error processing receipt: {e}")
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
