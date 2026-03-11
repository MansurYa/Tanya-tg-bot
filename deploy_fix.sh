#!/bin/bash
# Deployment script for server
# Run this on your server to apply the fix

set -e  # Exit on error

echo "=========================================="
echo "Deploying duplicate notifications fix"
echo "=========================================="

# 1. Pull latest changes
echo ""
echo "Step 1: Pulling latest code from GitHub..."
git pull origin main

# 2. Fix database
echo ""
echo "Step 2: Fixing database (disabling old notifications)..."
python fix_duplicate_notifications.py

# 3. Restart bot
echo ""
echo "Step 3: Restarting bot..."

# Use the safe stop script
chmod +x stop_bot.sh start_bot.sh check_bot.sh
./stop_bot.sh

if [ $? -ne 0 ]; then
    echo "⚠️  Warning: Failed to stop all instances"
fi

sleep 2

# Start bot
./start_bot.sh

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ Deployment successful!"
    ./check_bot.sh
    echo "=========================================="
else
    echo ""
    echo "=========================================="
    echo "❌ Deployment failed"
    echo "Check bot.log for errors: tail bot.log"
    echo "=========================================="
    exit 1
fi
