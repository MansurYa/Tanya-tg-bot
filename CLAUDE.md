# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run bot locally
python -m src.bot

# Run bot on server (background)
nohup python -m src.bot > bot.log 2>&1 &

# Run bot scripts
./start_bot.sh    # Start
./stop_bot.sh     # Stop all instances
./check_bot.sh    # Check status
./deploy_fix.sh   # Deploy with fixes

# Database migration
python migrate_db.py

# Verification
python verify_datasets.py   # Check dataset loading
python verify_datasets.py   # Check morning messages
```

## Architecture

**Core Bot** (`src/`):
- `bot.py` - Main entry point, ConversationHandler for quest flow (states: QUEST_Q1, QUEST_Q2, COMPLETED), morning message scheduler via APScheduler
- `database.py` - SQLite wrapper with row-level locking for atomic read-select-write operations on user state
- `message_pool.py` - Full-cycle message rotation (no repeats until all shown) for emotional/psychological pools

**Quest System**: 12 gifts with 2 questions each, LLM-based answer validation via OpenRouter (configurable model/temperature in config.json)

**Morning Messages**: Scheduled daily at randomized time (mean 08:45, std 67min), combines compliment + psychology quote, tracked via `emotional_pool_shown_ids`/`psychological_pool_shown_ids` in DB

**Data Flow**: `tanya_dataset_generator/` generates JSON datasets → loaded by `message_pool.py` → scheduled by APScheduler → sent via Telegram Bot API

**Config**: `config.json` contains bot_token, openrouter API key, quest definitions, unlock_sequence. Never committed.

**Database**: `data.db` (SQLite) - users table tracks quest progress, message pool state, notification preferences. Backups created automatically by migration scripts.
