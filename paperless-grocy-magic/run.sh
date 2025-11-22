#!/bin/sh
set -e

echo "🪄 Starting Paperless Grocy Magic v0.2.3-beta"
echo "============================================="

# Show configuration
if [ -f "/data/options.json" ]; then
    echo "📄 Configuration found"
    cat /data/options.json | python3 -m json.tool
else
    echo "⚠️  No configuration file found"
fi

echo ""
echo "🔗 Checking connections..."

# Parse configuration
PAPERLESS_URL=$(jq -r '.paperless_url // ""' /data/options.json)
GROCY_URL=$(jq -r '.grocy_url // ""' /data/options.json)

echo "📋 Paperless: ${PAPERLESS_URL:-not configured}"
echo "🏪 Grocy: ${GROCY_URL:-not configured}"

echo ""
echo "▶️  Starting Flask application..."
echo ""

# Start Flask app
cd /app
exec python3 -u main.py
