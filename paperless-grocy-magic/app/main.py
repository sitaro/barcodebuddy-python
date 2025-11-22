"""Main Flask application for Paperless Grocy Magic."""
import logging
from flask import Flask, render_template, jsonify
from config import config
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if config.debug else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'paperless-grocy-magic-secret'


@app.route('/')
def index():
    """Main dashboard."""
    return jsonify({
        'name': 'Paperless Grocy Magic',
        'version': '0.1.0-beta',
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
    return jsonify({
        'status': 'ok',
        'paperless': {
            'url': config.paperless_url if config.paperless_url else 'not configured',
            'configured': bool(config.paperless_url and config.paperless_api_key)
        },
        'grocy': {
            'url': config.grocy_url if config.grocy_url else 'not configured',
            'configured': bool(config.grocy_url and config.grocy_api_key)
        }
    })


@app.route('/api/process-receipts', methods=['POST'])
def process_receipts():
    """Manually trigger receipt processing."""
    # TODO: Implement receipt processing logic
    return jsonify({
        'success': False,
        'message': 'Not yet implemented - coming soon!'
    })


if __name__ == '__main__':
    logger.info("🪄 Paperless Grocy Magic starting...")
    logger.info(f"Paperless: {'✓' if config.paperless_url else '✗'}")
    logger.info(f"Grocy: {'✓' if config.grocy_url else '✗'}")

    app.run(
        host='0.0.0.0',
        port=5001,
        debug=config.debug
    )
