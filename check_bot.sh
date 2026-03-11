#!/bin/bash
# Check bot status

echo "Bot Status Check"
echo "================"

# Check if bot is running
PIDS=$(pgrep -f "python -m src.bot" || true)

if [ -z "$PIDS" ]; then
    echo "Status: ❌ NOT RUNNING"
    exit 1
fi

# Count instances
COUNT=$(echo "$PIDS" | wc -l | tr -d ' ')

if [ "$COUNT" -gt 1 ]; then
    echo "Status: ⚠️  MULTIPLE INSTANCES RUNNING (CONFLICT!)"
    echo "Count: $COUNT instances"
    echo ""
    echo "Running processes:"
    ps aux | grep "python -m src.bot" | grep -v grep
    echo ""
    echo "⚠️  This will cause Telegram API conflicts!"
    echo "Fix: ./stop_bot.sh && ./start_bot.sh"
    exit 2
else
    echo "Status: ✅ RUNNING"
    echo "PID: $PIDS"
    echo ""
    ps aux | grep "python -m src.bot" | grep -v grep
    echo ""
    echo "Logs: tail -f bot.log"
    exit 0
fi
