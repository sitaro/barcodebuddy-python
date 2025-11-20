#!/bin/sh
set -e

echo "🚀 Starting Barcode Buddy (Python) v2.0.6"
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
echo "Current user: $(whoami), UID: $(id -u), GID: $(id -g)"
echo "Groups: $(id -G)"
echo ""
echo "Before chmod:"
ls -la /dev/input/ 2>/dev/null

# Make input devices readable by all (we have full_access)
if chmod 666 /dev/input/event3 2>&1; then
    echo "✓ chmod succeeded"
else
    echo "✗ chmod failed: $?"
fi

echo ""
echo "After chmod:"
ls -la /dev/input/ 2>/dev/null

echo ""
echo "Testing direct read access:"
if timeout 1 cat /dev/input/event3 >/dev/null 2>&1; then
    echo "✓ Can read from device"
else
    echo "✗ Cannot read from device (exit code: $?)"
fi

echo ""
echo "▶️  Starting Flask application..."
echo ""

# Start Flask app
cd /app
python3 -u main.py
