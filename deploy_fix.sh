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
echo "Stopping bot..."
pkill -f "python -m src.bot" || echo "Bot was not running"

sleep 2

echo "Starting bot..."
nohup python -m src.bot > bot.log 2>&1 &

sleep 2

# 4. Verify bot is running
if pgrep -f "python -m src.bot" > /dev/null; then
    echo ""
    echo "=========================================="
    echo "✅ Deployment successful!"
    echo "Bot is running with PID: $(pgrep -f 'python -m src.bot')"
    echo "=========================================="
else
    echo ""
    echo "=========================================="
    echo "❌ Warning: Bot may not be running"
    echo "Check bot.log for errors"
    echo "=========================================="
    exit 1
fi
