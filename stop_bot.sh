#!/bin/bash
# Script to safely stop all bot instances

echo "Checking for running bot instances..."

# Find all processes matching the bot
PIDS=$(pgrep -f "python -m src.bot" || true)

if [ -z "$PIDS" ]; then
    echo "✅ No bot instances running"
    exit 0
fi

echo "Found running bot instances:"
ps aux | grep "python -m src.bot" | grep -v grep

echo ""
echo "Stopping all instances..."

# Kill all found processes
for PID in $PIDS; do
    echo "  Killing PID $PID..."
    kill $PID 2>/dev/null || true
done

# Wait a bit
sleep 2

# Check if any are still running
REMAINING=$(pgrep -f "python -m src.bot" || true)

if [ -n "$REMAINING" ]; then
    echo "⚠️  Some processes still running, forcing kill..."
    for PID in $REMAINING; do
        echo "  Force killing PID $PID..."
        kill -9 $PID 2>/dev/null || true
    done
    sleep 1
fi

# Final check
FINAL_CHECK=$(pgrep -f "python -m src.bot" || true)

if [ -z "$FINAL_CHECK" ]; then
    echo "✅ All bot instances stopped successfully"
    exit 0
else
    echo "❌ Failed to stop some instances:"
    ps aux | grep "python -m src.bot" | grep -v grep
    exit 1
fi
