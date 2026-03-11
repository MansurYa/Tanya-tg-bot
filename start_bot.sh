#!/bin/bash
# Script to start the bot safely

echo "Starting bot..."

# Check if already running
if pgrep -f "python -m src.bot" > /dev/null; then
    echo "❌ Bot is already running!"
    echo "Running instances:"
    ps aux | grep "python -m src.bot" | grep -v grep
    echo ""
    echo "Stop them first with: ./stop_bot.sh"
    exit 1
fi

# Start bot in background
nohup python -m src.bot > bot.log 2>&1 &
BOT_PID=$!

# Wait a moment for it to start
sleep 2

# Check if it's running
if pgrep -f "python -m src.bot" > /dev/null; then
    echo "✅ Bot started successfully"
    echo "PID: $(pgrep -f 'python -m src.bot')"
    echo "Logs: tail -f bot.log"
    exit 0
else
    echo "❌ Bot failed to start"
    echo "Check logs: tail bot.log"
    exit 1
fi
