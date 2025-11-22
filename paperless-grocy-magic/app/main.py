"""Main Flask application for Paperless Grocy Magic."""
import logging
from flask import Flask, render_template, jsonify, request
from config import config
from datetime import datetime
from grocy_client import GrocyClient
from paperless_client import PaperlessClient
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

# Initialize Paperless client
paperless_client = None

if config.paperless_url and config.paperless_api_key:
    try:
        logger.info(f"Initializing Paperless client with URL: {config.paperless_url}")
        paperless_client = PaperlessClient(config.paperless_url, config.paperless_api_key)

        logger.info("Testing Paperless connection...")
        if paperless_client.test_connection():
            logger.info("✅ Paperless client initialized successfully")
        else:
            logger.error("❌ Paperless connection test failed")
            paperless_client = None
    except Exception as e:
        logger.error(f"❌ Failed to initialize Paperless client: {e}", exc_info=True)
        paperless_client = None
else:
    logger.warning("⚠️  Paperless not configured")

# Initialize Grocy client and price updater
grocy_client = None
price_updater = None

if config.grocy_url and config.grocy_api_key:
    try:
        logger.info(f"Initializing Grocy client with URL: {config.grocy_url}")
        grocy_client = GrocyClient(config.grocy_url, config.grocy_api_key)

        logger.info("Testing Grocy connection...")
        if grocy_client.test_connection():
            logger.info("Grocy connection successful, creating PriceUpdateService...")
            price_updater = PriceUpdateService(grocy_client, config.fuzzy_match_threshold)
            logger.info("✅ Grocy client initialized successfully")
        else:
            logger.error("❌ Grocy connection test failed")
            logger.error(f"   URL: {config.grocy_url}")
            logger.error(f"   API Key: {config.grocy_api_key[:10]}..." if config.grocy_api_key else "   API Key: None")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Grocy client: {e}", exc_info=True)
else:
    logger.warning("⚠️  Grocy not configured")
    logger.warning(f"   grocy_url: {config.grocy_url}")
    logger.warning(f"   grocy_api_key: {'set' if config.grocy_api_key else 'not set'}")


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
            <h2>📄 Receipt Input</h2>

            <div style="margin-bottom: 20px; padding: 15px; background: #e8f5e9; border-radius: 4px;">
                <strong>🔄 Auto-Process from Paperless:</strong><br>
                <button onclick="processPaperless()" style="margin-top: 10px; background: #4CAF50;">🚀 Process Paperless Receipts</button>
                <p style="font-size: 12px; margin: 10px 0 0 0; color: #666;">
                    Processes all unprocessed receipts with tag "{{ config.paperless_tag }}"
                </p>
            </div>

            <div style="margin-bottom: 20px; padding: 15px; background: #fff3cd; border-radius: 4px;">
                <strong>📤 Upload PDF Receipt:</strong><br>
                <input type="file" id="pdfFile" accept=".pdf" style="margin: 10px 0;">
                <button onclick="uploadPDF()" class="secondary">📄 Extract Text from PDF</button>
            </div>

            <strong>Or paste receipt text manually:</strong>
            <textarea id="receiptText" style="margin-top: 10px;">REWE MARKT
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

        function uploadPDF() {
            const fileInput = document.getElementById('pdfFile');
            const file = fileInput.files[0];

            if (!file) {
                alert('Please select a PDF file first!');
                return;
            }

            if (!file.name.toLowerCase().endsWith('.pdf')) {
                alert('Please select a PDF file!');
                return;
            }

            const resultDiv = document.getElementById('result');
            resultDiv.innerHTML = '⏳ Extracting text from PDF...';

            const formData = new FormData();
            formData.append('file', file);

            fetch(baseUrl + '/api/extract-pdf', {
                method: 'POST',
                body: formData
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
                if (data.success) {
                    // Put extracted text into textarea
                    document.getElementById('receiptText').value = data.text;
                    resultDiv.innerHTML = `<span class="success">✅ Text extracted successfully!</span>\n\n` +
                                        `📄 Extracted ${data.text.length} characters\n\n` +
                                        `Now click "Process Receipt" to parse it.`;
                } else {
                    resultDiv.innerHTML = `<span class="error">❌ Error: ${data.error}</span>`;
                }
            })
            .catch(e => {
                resultDiv.innerHTML = `<span class="error">❌ Error: ${e.message}</span>`;
            });
        }

        function processPaperless() {
            const resultDiv = document.getElementById('result');
            resultDiv.innerHTML = '⏳ Processing Paperless receipts...';

            fetch(baseUrl + '/api/process-paperless', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'}
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
                let output = '';

                if (data.success) {
                    output += `<span class="success">✅ Paperless Processing Complete!</span>\n\n`;
                } else {
                    output += `<span class="error">❌ Paperless Processing Failed</span>\n\n`;
                }

                output += `📊 Summary:\n`;
                output += `  Total receipts found: ${data.total || 0}\n`;
                output += `  ✅ Successfully processed: ${data.processed || 0}\n`;
                output += `  ❌ Failed: ${data.failed || 0}\n\n`;

                if (data.results && data.results.length > 0) {
                    output += '📋 Results:\n';
                    output += '─'.repeat(60) + '\n';
                    data.results.forEach((r, i) => {
                        output += `${i+1}. Document ${r.document_id}: ${r.title}\n`;
                        if (r.success) {
                            output += `   ✅ Success - Updated: ${r.updated || 0}, Created: ${r.created || 0}\n`;
                        } else {
                            output += `   ❌ Failed: ${r.error}\n`;
                        }
                        if (r.warning) {
                            output += `   ⚠️  ${r.warning}\n`;
                        }
                        output += '\n';
                    });
                } else if (data.message) {
                    output += `\n${data.message}\n`;
                }

                output += '─'.repeat(60) + '\n';
                output += 'Raw JSON:\n' + JSON.stringify(data, null, 2);

                resultDiv.innerHTML = output;
            })
            .catch(e => {
                resultDiv.innerHTML = `<span class="error">❌ Error: ${e.message}</span>`;
            });
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


@app.route('/api/extract-pdf', methods=['POST'])
def extract_pdf():
    """Extract text from uploaded PDF file."""
    logger.info("Received PDF extraction request")

    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        if not file.filename.lower().endswith('.pdf'):
            return jsonify({
                'success': False,
                'error': 'Only PDF files are supported'
            }), 400

        # Extract text from PDF using PyPDF2 (lighter than pdfplumber)
        import io
        from PyPDF2 import PdfReader

        pdf_bytes = file.read()
        text_content = ""

        pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
        num_pages = len(pdf_reader.pages)
        logger.info(f"PDF has {num_pages} pages")

        for page_num, page in enumerate(pdf_reader.pages, 1):
            page_text = page.extract_text()
            if page_text:
                text_content += page_text + "\n"
                logger.debug(f"Page {page_num}: {len(page_text)} chars")

        if not text_content.strip():
            return jsonify({
                'success': False,
                'error': 'No text found in PDF. It might be a scanned image without OCR.'
            }), 400

        logger.info(f"Extracted {len(text_content)} characters from PDF")

        return jsonify({
            'success': True,
            'text': text_content,
            'pages': num_pages,
            'chars': len(text_content)
        })

    except Exception as e:
        logger.error(f"Error extracting PDF: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Failed to extract PDF: {str(e)}'
        }), 500


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


@app.route('/api/process-paperless', methods=['POST'])
def process_paperless():
    """Process unprocessed receipts from Paperless-ngx."""
    logger.info("Received Paperless processing request")

    if not paperless_client:
        logger.error("Paperless client not initialized")
        return jsonify({
            'success': False,
            'error': 'Paperless not configured or connection failed'
        }), 503

    if not price_updater:
        logger.error("Price updater not initialized")
        return jsonify({
            'success': False,
            'error': 'Grocy not configured or connection failed'
        }), 503

    try:
        # Get configuration
        tag_name = config.paperless_tag
        field_name = config.paperless_processed_field

        logger.info(f"Querying Paperless for unprocessed receipts (tag: '{tag_name}', field: '{field_name}')")

        # Get unprocessed documents
        documents = paperless_client.get_documents_by_tag(tag_name, field_name)

        if not documents:
            logger.info("No unprocessed receipts found")
            return jsonify({
                'success': True,
                'message': 'No unprocessed receipts found',
                'processed': 0,
                'failed': 0,
                'results': []
            })

        logger.info(f"Found {len(documents)} unprocessed receipts")

        # Process each document
        results = []
        processed_count = 0
        failed_count = 0

        for doc in documents:
            logger.info(f"Processing document {doc.id}: {doc.title}")

            try:
                # Download PDF
                pdf_bytes = paperless_client.download_document(doc.id)
                if not pdf_bytes:
                    logger.error(f"Failed to download document {doc.id}")
                    results.append({
                        'document_id': doc.id,
                        'title': doc.title,
                        'success': False,
                        'error': 'Failed to download PDF'
                    })
                    failed_count += 1
                    continue

                # Extract text from PDF
                import io
                from PyPDF2 import PdfReader

                pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
                text_content = ""

                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n"

                if not text_content.strip():
                    logger.error(f"No text extracted from document {doc.id}")
                    results.append({
                        'document_id': doc.id,
                        'title': doc.title,
                        'success': False,
                        'error': 'No text found in PDF'
                    })
                    failed_count += 1
                    continue

                logger.info(f"Extracted {len(text_content)} characters from document {doc.id}")

                # Process receipt
                result = price_updater.process_receipt_text(text_content)

                if result.success:
                    # Mark as processed in Paperless
                    if paperless_client.update_custom_field(doc.id, field_name, True):
                        logger.info(f"✅ Processed document {doc.id} successfully")
                        processed_count += 1
                        results.append({
                            'document_id': doc.id,
                            'title': doc.title,
                            'success': True,
                            'updated': result.updated_count,
                            'created': result.created_count,
                            'failed': result.failed_count
                        })
                    else:
                        logger.warning(f"Processed {doc.id} but failed to mark as processed")
                        results.append({
                            'document_id': doc.id,
                            'title': doc.title,
                            'success': True,
                            'warning': 'Could not mark as processed in Paperless',
                            'updated': result.updated_count,
                            'created': result.created_count
                        })
                        processed_count += 1
                else:
                    logger.error(f"❌ Failed to process document {doc.id}")
                    results.append({
                        'document_id': doc.id,
                        'title': doc.title,
                        'success': False,
                        'error': f"Processing failed: {', '.join(result.errors)}"
                    })
                    failed_count += 1

            except Exception as e:
                logger.error(f"Error processing document {doc.id}: {e}", exc_info=True)
                results.append({
                    'document_id': doc.id,
                    'title': doc.title,
                    'success': False,
                    'error': str(e)
                })
                failed_count += 1

        logger.info(f"Paperless processing complete: {processed_count} processed, {failed_count} failed")

        return jsonify({
            'success': True,
            'processed': processed_count,
            'failed': failed_count,
            'total': len(documents),
            'results': results
        })

    except Exception as e:
        logger.error(f"Error processing Paperless receipts: {e}", exc_info=True)
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
