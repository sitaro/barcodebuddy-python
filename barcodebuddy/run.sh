#!/bin/sh
set -e

echo "🚀 Starting Barcode Buddy (Python) v2.3.3"
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
echo "📋 Device by-id:"
ls -la /dev/input/by-id/ 2>/dev/null || echo "No by-id devices"

echo ""
echo "📋 Device by-path:"
ls -la /dev/input/by-path/ 2>/dev/null || echo "No by-path devices"

echo ""
echo "🔍 Checking which devices are readable:"
for dev in /dev/input/event*; do
    if [ -e "$dev" ]; then
        if timeout 0.1 cat "$dev" >/dev/null 2>&1; then
            echo "  ✓ $dev - readable"
        else
            echo "  ✗ $dev - not readable"
        fi
    fi
done

echo ""
echo "🔧 Fixing device permissions..."
echo "Current user: $(whoami), UID: $(id -u), GID: $(id -g)"
echo "Groups before: $(id -G)"

# Get the group ID of the input device
DEVICE_GID=$(stat -c '%g' /dev/input/event3 2>/dev/null || echo "110")
echo "Device group ID: $DEVICE_GID"

# Add root to the input group
if ! grep -q "^input:" /etc/group 2>/dev/null; then
    echo "Creating input group with GID $DEVICE_GID"
    addgroup -g $DEVICE_GID input 2>/dev/null || true
fi

echo "Adding root to input group..."
addgroup root input 2>/dev/null || adduser root input 2>/dev/null || true

# Re-evaluate groups (newgrp doesn't work in scripts, so we'll use sg)
echo "Groups after: $(id -G)"
echo ""

echo "Testing direct read access:"
if timeout 1 sg input -c "cat /dev/input/event3" >/dev/null 2>&1; then
    echo "✓ Can read from device with group access"
else
    echo "✗ Still cannot read from device"
fi

echo ""
echo "▶️  Starting Flask application with input group..."
echo ""

# Start Flask app with input group permissions
cd /app
if command -v sg >/dev/null 2>&1; then
    exec sg input -c "python3 -u main.py"
else
    exec python3 -u main.py
fi
