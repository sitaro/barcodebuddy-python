"""Main Flask application."""
from flask import Flask, render_template, jsonify, request, session, send_file
from flask_babel import Babel, gettext
import logging
import sys
import os
import requests
from config import Config
from grocy import GrocyClient
from scanner import ScannerHandler
from openfoodfacts import OpenFoodFactsClient
from upcdatabase import UPCDatabaseClient
from pdf_generator import generate_quantity_barcodes_pdf
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
app.config['SECRET_KEY'] = 'barcode-buddy-secret-key'  # For session management
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'

# Initialize Babel (will be configured after defining locale_selector)
babel = Babel()

def get_locale():
    """Get the configured language from config."""
    # Simply return the configured language (always set, no auto-detection)
    return config.language

# Load config first (before Babel, since get_locale() uses config)
config = Config()

# Set debug mode
if config.debug:
    logging.getLogger().setLevel(logging.DEBUG)
    app.debug = True

# Initialize Babel with locale selector (after config is loaded)
babel.init_app(app, locale_selector=get_locale)

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

# Initialize product database clients
openfoodfacts_client = OpenFoodFactsClient()
upcdatabase_client = UPCDatabaseClient()

# Store recent scans
recent_scans = []

# Current quantity for next product scan (reset after each product)
# Starts at 0, defaults to 1 if no quantity barcode scanned
current_quantity = 0.0

# Current mode: 'add' or 'consume'
current_mode = 'add'

def handle_barcode(barcode: str):
    """Handle scanned barcode with automatic product creation."""
    global current_quantity, current_mode

    logger.info(f"📦 Processing barcode: {barcode}")

    scan_result = {
        'barcode': barcode,
        'timestamp': datetime.now().isoformat(),
        'status': 'unknown',
        'message': ''
    }

    # Check if this is a mode switch barcode
    if barcode == config.barcode_add:
        current_mode = 'add'
        scan_result['status'] = 'mode'
        scan_result['message'] = f"➕ Mode: ADD (adding to stock)"
        logger.info(f"➕ Mode switched to: ADD")
        # Store and return
        recent_scans.insert(0, scan_result)
        if len(recent_scans) > 50:
            recent_scans.pop()
        return
    elif barcode == config.barcode_consume:
        current_mode = 'consume'
        scan_result['status'] = 'mode'
        scan_result['message'] = f"➖ Mode: CONSUME (removing from stock)"
        logger.info(f"➖ Mode switched to: CONSUME")
        # Store and return
        recent_scans.insert(0, scan_result)
        if len(recent_scans) > 50:
            recent_scans.pop()
        return

    # Check if this is a quantity barcode
    if barcode.startswith(config.barcode_quantity_prefix):
        try:
            quantity_str = barcode[len(config.barcode_quantity_prefix):]
            quantity_to_add = float(quantity_str)
            current_quantity += quantity_to_add
            scan_result['status'] = 'quantity'
            scan_result['message'] = f"🔢 Quantity set to: {current_quantity}"
            logger.info(f"🔢 Quantity updated: {current_quantity} (added {quantity_to_add})")
        except (IndexError, ValueError) as e:
            scan_result['status'] = 'error'
            scan_result['message'] = f"❌ Invalid quantity barcode format"
            logger.error(f"Invalid quantity barcode: {barcode} - {e}")

        # Store scan result and return
        recent_scans.insert(0, scan_result)
        if len(recent_scans) > 50:
            recent_scans.pop()
        return

    # Regular product barcode handling
    if grocy_client:
        # Step 1: Try to find product in Grocy
        product = grocy_client.find_product_by_barcode(barcode)

        if product:
            # Product exists in Grocy
            logger.debug(f"Product data from Grocy: {product}")

            # Grocy API returns nested structure: {'product': {'id': ...}}
            if 'product' in product and isinstance(product['product'], dict):
                product_id = product['product'].get('id')
                product_name = product['product'].get('name', 'Unknown')
                # Product info is already included in the response
                product_info = product['product']
            else:
                # Fallback for different API formats
                product_id = product.get('product_id') or product.get('id')
                product_info = None

            if not product_id:
                logger.error(f"No product_id found in response: {product}")
                scan_result['status'] = 'error'
                scan_result['message'] = f"❌ Invalid product data from Grocy"
                # Store and return
                recent_scans.insert(0, scan_result)
                if len(recent_scans) > 50:
                    recent_scans.pop()
                return

            # If product info wasn't in the barcode response, fetch it separately
            if not product_info:
                product_info = grocy_client.get_product_info(product_id)

            if product_info:
                product_name = product_info.get('name', 'Unknown')
                # Use current quantity, or default to 1 if no quantity barcode was scanned
                amount = current_quantity if current_quantity > 0 else 1.0

                # Add or consume based on current mode
                if current_mode == 'add':
                    success = grocy_client.add_product(product_id, amount)
                    action_emoji = "➕"
                    action_text = "Added"
                else:  # consume mode
                    success = grocy_client.consume_product(product_id, amount)
                    action_emoji = "➖"
                    action_text = "Removed"

                if success:
                    quantity_text = f" ({amount}x)" if amount != 1 else ""
                    scan_result['status'] = 'success'
                    scan_result['message'] = f"{action_emoji} {action_text}: {product_name}{quantity_text}"
                    logger.info(f"{action_emoji} {action_text} product: {product_name} (quantity: {amount})")
                    current_quantity = 0.0  # Reset after successful operation
                else:
                    scan_result['status'] = 'error'
                    scan_result['message'] = f"❌ Failed to {action_text.lower()}: {product_name}"
            else:
                scan_result['status'] = 'error'
                scan_result['message'] = f"❌ Error reading product info"
        else:
            # Step 2: Product not in Grocy - try external databases
            logger.info(f"🔍 Product not in Grocy, checking external databases...")

            # Try databases in order: OpenFoodFacts → UPC Database
            # Only query databases that are enabled in configuration
            external_product = None
            database_name = None

            if config.enable_openfoodfacts and not external_product:
                external_product = openfoodfacts_client.lookup_barcode(barcode)
                if external_product:
                    database_name = "OpenFoodFacts"

            if config.enable_upcdatabase and not external_product:
                external_product = upcdatabase_client.lookup_barcode(barcode)
                if external_product:
                    database_name = "UPC Database"

            if external_product:
                # Step 3: Found in external database - create in Grocy
                product_name = external_product['name']
                description = f"{external_product.get('brand', '')} - {external_product.get('quantity', '')}".strip(' -')

                logger.info(f"🆕 Creating new product from {database_name}: {product_name}")
                product_id = grocy_client.create_product(product_name, description)

                if product_id:
                    # Step 4: Add barcode to new product
                    if grocy_client.add_barcode_to_product(product_id, barcode):
                        # Step 5: Add to stock with current quantity (only makes sense in add mode)
                        amount = current_quantity if current_quantity > 0 else 1.0

                        if current_mode == 'add':
                            success = grocy_client.add_product(product_id, amount)
                            action_text = "Added"
                        else:
                            # Note: Consuming a just-created product is unusual, but supported
                            success = grocy_client.consume_product(product_id, amount)
                            action_text = "Removed"

                        if success:
                            quantity_text = f" ({amount}x)" if amount != 1 else ""
                            scan_result['status'] = 'success'
                            scan_result['message'] = f"🆕 Created from {database_name} & {action_text}: {product_name}{quantity_text}"
                            logger.info(f"🆕 Successfully created from {database_name} and {action_text.lower()}: {product_name} (quantity: {amount})")
                            current_quantity = 0.0  # Reset after successful operation
                        else:
                            scan_result['status'] = 'warning'
                            scan_result['message'] = f"⚠️ Created {product_name}, but failed to {action_text.lower()}"
                    else:
                        scan_result['status'] = 'warning'
                        scan_result['message'] = f"⚠️ Created {product_name}, but failed to add barcode"
                else:
                    scan_result['status'] = 'error'
                    scan_result['message'] = f"❌ Failed to create product in Grocy"
            else:
                # Not found anywhere
                scan_result['status'] = 'not_found'
                scan_result['message'] = f"❓ Barcode not found in Grocy, OpenFoodFacts, or UPC Database"
                logger.warning(f"❓ Barcode {barcode} not found in any database")
    else:
        scan_result['status'] = 'no_grocy'
        scan_result['message'] = f"📦 Scanned (no Grocy configured)"

    # Store in recent scans (keep last 50)
    recent_scans.insert(0, scan_result)
    if len(recent_scans) > 50:
        recent_scans.pop()

# Initialize scanner (auto-detects all available devices)
scanner = ScannerHandler(None, handle_barcode)
scanner.start()

@app.route('/')
def index():
    """Main page."""
    return render_template('index.html',
                         has_grocy=config.has_grocy,
                         scanner_devices=scanner.active_devices,
                         current_locale=get_locale())

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
        'scanner_devices': scanner.active_devices,
        'scanner_active': scanner.running,
        'scan_count': len(recent_scans)
    })

@app.route('/api/create-product', methods=['POST'])
def create_product():
    """Create a new product with barcode and add to stock."""
    global current_quantity, current_mode

    data = request.get_json()
    barcode = data.get('barcode', '').strip()
    product_name = data.get('product_name', '').strip()

    if not barcode or not product_name:
        return jsonify({'success': False, 'error': 'Barcode and product name required'}), 400

    if not grocy_client:
        return jsonify({'success': False, 'error': 'Grocy not configured'}), 400

    try:
        # Create product in Grocy
        product_id = grocy_client.create_product(product_name, description=f"Created via Barcode Buddy")
        if not product_id:
            return jsonify({'success': False, 'error': 'Failed to create product in Grocy'}), 500

        # Add barcode to product
        if not grocy_client.add_barcode_to_product(product_id, barcode):
            logger.warning(f"Product created but failed to add barcode")

        # Add to stock based on current mode
        amount = current_quantity if current_quantity > 0 else 1.0

        if current_mode == 'add':
            success = grocy_client.add_product(product_id, amount)
            action_text = "Added"
        else:  # consume mode
            success = grocy_client.consume_product(product_id, amount)
            action_text = "Removed"

        if success:
            # Reset quantity after successful operation
            current_quantity = 0.0

            # Create scan result
            scan_result = {
                'barcode': barcode,
                'timestamp': __import__('datetime').datetime.now().isoformat(),
                'status': 'success',
                'message': f"✨ Created '{product_name}' and {action_text.lower()} {amount}x to stock"
            }

            # Store in recent scans
            recent_scans.insert(0, scan_result)
            if len(recent_scans) > 50:
                recent_scans.pop()

            logger.info(f"✨ Created product '{product_name}' (ID: {product_id}) and {action_text.lower()} {amount}x")

            return jsonify({'success': True, 'product_id': product_id, 'product_name': product_name})
        else:
            return jsonify({'success': False, 'error': f'Product created but failed to {action_text.lower()} to stock'}), 500

    except Exception as e:
        logger.error(f"Error creating product: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/download-quantity-barcodes')
def download_quantity_barcodes():
    """View PDF with quantity barcodes in browser."""
    try:
        pdf_buffer = generate_quantity_barcodes_pdf(barcode_format=config.barcode_format)
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=False
        )
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("🚀 Starting Barcode Buddy (Python)")
    logger.info(f"📱 Scanner: Auto-detecting all available devices")
    logger.info(f"🔗 Grocy: {'✅ Configured' if config.has_grocy else '❌ Not configured'}")

    app.run(host='0.0.0.0', port=5000)
