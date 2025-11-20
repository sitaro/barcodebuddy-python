"""Main Flask application."""
from flask import Flask, render_template, jsonify, request
import logging
import sys
from config import Config
from grocy import GrocyClient
from scanner import ScannerHandler
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
config = Config()

# Set debug mode
if config.debug:
    logging.getLogger().setLevel(logging.DEBUG)
    app.debug = True

# Initialize Grocy client
grocy_client = None
if config.has_grocy:
    grocy_client = GrocyClient(config.grocy_url, config.grocy_api_key)
    if grocy_client.test_connection():
        logger.info("✅ Grocy connection successful")
    else:
        logger.warning("⚠️  Grocy connection failed")
        grocy_client = None
else:
    logger.info("ℹ️  No Grocy configuration - running in standalone mode")

# Store recent scans
recent_scans = []

def handle_barcode(barcode: str):
    """Handle scanned barcode."""
    logger.info(f"📦 Processing barcode: {barcode}")

    scan_result = {
        'barcode': barcode,
        'timestamp': datetime.now().isoformat(),
        'status': 'unknown',
        'message': ''
    }

    if grocy_client:
        # Try to find product in Grocy
        product = grocy_client.find_product_by_barcode(barcode)
        if product:
            product_id = product.get('product_id')
            product_info = grocy_client.get_product_info(product_id)

            if product_info:
                product_name = product_info.get('name', 'Unknown')
                # Add to stock
                if grocy_client.add_product(product_id):
                    scan_result['status'] = 'success'
                    scan_result['message'] = f"✅ Added: {product_name}"
                    logger.info(f"✅ Added product: {product_name}")
                else:
                    scan_result['status'] = 'error'
                    scan_result['message'] = f"❌ Failed to add: {product_name}"
            else:
                scan_result['status'] = 'not_found'
                scan_result['message'] = f"❓ Product not found in Grocy"
        else:
            scan_result['status'] = 'not_found'
            scan_result['message'] = f"❓ Barcode not found in Grocy"
    else:
        scan_result['status'] = 'no_grocy'
        scan_result['message'] = f"📦 Scanned (no Grocy configured)"

    # Store in recent scans (keep last 50)
    recent_scans.insert(0, scan_result)
    if len(recent_scans) > 50:
        recent_scans.pop()

# Initialize scanner
scanner = ScannerHandler(config.scanner_device, handle_barcode)
scanner.start()

@app.route('/')
def index():
    """Main page."""
    return render_template('index.html',
                         has_grocy=config.has_grocy,
                         scanner_device=config.scanner_device)

@app.route('/api/scans')
def get_scans():
    """Get recent scans."""
    return jsonify(recent_scans)

@app.route('/api/scan', methods=['POST'])
def manual_scan():
    """Manual barcode entry."""
    data = request.get_json()
    barcode = data.get('barcode', '').strip()

    if barcode:
        handle_barcode(barcode)
        return jsonify({'success': True})

    return jsonify({'success': False, 'error': 'No barcode provided'}), 400

@app.route('/api/status')
def status():
    """System status."""
    return jsonify({
        'grocy_configured': config.has_grocy,
        'grocy_connected': grocy_client is not None,
        'scanner_device': config.scanner_device,
        'scanner_active': scanner.running,
        'scan_count': len(recent_scans)
    })

if __name__ == '__main__':
    logger.info("🚀 Starting Barcode Buddy (Python)")
    logger.info(f"📱 Scanner device: {config.scanner_device}")
    logger.info(f"🔗 Grocy: {'✅ Configured' if config.has_grocy else '❌ Not configured'}")

    app.run(host='0.0.0.0', port=5000)
