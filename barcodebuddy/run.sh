#!/bin/sh
set -e

echo "🚀 Starting Barcode Buddy (Python) v2.0.5"
echo "==========================================="

# Show configuration
if [ -f "/data/options.json" ]; then
    echo "📄 Configuration found"
    cat /data/options.json | python3 -m json.tool
else
    echo "⚠️  No configuration file found"
fi

echo ""
echo "🔍 Available scanner devices:"
ls -la /dev/input/ 2>/dev/null || echo "No /dev/input devices"

echo ""
echo "🔧 Fixing device permissions..."
# Make input devices readable by all (we have full_access)
chmod -R 666 /dev/input/event* 2>/dev/null || echo "⚠️  Could not change permissions"
ls -la /dev/input/ 2>/dev/null

echo ""
echo "▶️  Starting Flask application..."
echo ""

# Start Flask app
cd /app
python3 -u main.py
