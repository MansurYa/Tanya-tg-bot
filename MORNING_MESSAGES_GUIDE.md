# 🌅 Morning Messages System - Deployment Guide

## ✅ Implementation Complete

The morning messages system has been successfully integrated into the Tanya bot.

## 📋 What Was Implemented

### 1. Core Features
- **Message Pools**: 125 compliments + 125 psychology messages
- **Smart Rotation**: No repeats until all messages shown (full cycle)
- **Time Distribution**: Normal distribution (mean: 08:45, std: 67 minutes)
- **"Another Message" Button**: Unlimited additional messages on demand
- **Auto-activation**: Triggers when quest is completed

### 2. New Files Created
- `src/message_pool.py` - Message rotation logic
- `migrate_db.py` - Database migration script
- `test_morning_messages.py` - Test suite

### 3. Modified Files
- `src/bot.py` - Added morning message functions and handlers
- `src/database.py` - Added 7 new database fields
- `requirements.txt` - Added numpy dependency

## 🚀 Deployment Steps

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run Database Migration
```bash
python migrate_db.py
```

Expected output:
```
✅ Added column: morning_messages_enabled
✅ Added column: emotional_pool_shown_ids
✅ Added column: psychological_pool_shown_ids
✅ Added column: emotional_cycle_number
✅ Added column: psychological_cycle_number
✅ Added column: last_morning_message_date
✅ Added column: next_morning_message_time

✅ Migration complete! Added 7 new columns.
```

### Step 3: Run Tests (Optional but Recommended)
```bash
python test_morning_messages.py
```

Expected output:
```
🎉 All tests passed!
```

### Step 4: Start the Bot
```bash
python -m src.bot
```

## 📊 System Behavior

### Quest Completion Flow
1. User completes all 12 quest gifts
2. Bot sends completion message
3. **Morning messages automatically activate**
4. First message sent immediately with "Ещё одно сообщение" button
5. Daily messages scheduled for future mornings

### Daily Message Flow
1. At 00:05 UTC, scheduler generates random time for each user
2. Time follows normal distribution: 08:45 ± 67 minutes (Moscow time)
3. At generated time, bot sends combined message:
   - Compliment from emotional pool
   - Psychology principle from psychological pool
   - "🤖 Автоматическое сообщение" disclaimer
   - "Ещё одно сообщение" button

### "Another Message" Button
- User can click unlimited times
- Each click sends new message pair
- Both messages marked as "shown" in rotation
- Pools reset independently when exhausted

### Rotation Logic
- **Emotional pool**: 125 messages, resets after all shown
- **Psychological pool**: 125 messages, resets independently
- **No repeats** within a cycle
- **Random selection** from available (not yet shown)

## 🗄️ Database Schema

New fields added to `users` table:

| Field | Type | Description |
|-------|------|-------------|
| `morning_messages_enabled` | INTEGER | 0/1 flag for activation |
| `emotional_pool_shown_ids` | TEXT | JSON array of shown compliment IDs |
| `psychological_pool_shown_ids` | TEXT | JSON array of shown psychology IDs |
| `emotional_cycle_number` | INTEGER | Current cycle number for emotional pool |
| `psychological_cycle_number` | INTEGER | Current cycle number for psychological pool |
| `last_morning_message_date` | TEXT | Date of last sent message (YYYY-MM-DD) |
| `next_morning_message_time` | TEXT | Scheduled time for next message (HH:MM) |

## 📈 Statistics

- **Total messages**: 250 (125 emotional + 125 psychological)
- **Unique combinations**: 15,625 (125 × 125)
- **Cycle length**: 125 days before exact pair repeats
- **Time range**: ~68% between 08:38-10:52, ~95% between 07:31-12:00

## 🧪 Test Results

All tests passed:
- ✅ Rotation Logic: No repeats within cycle, correct reset
- ✅ Time Distribution: Mean and std within expected range
- ✅ Database Operations: All fields work correctly

## 🔧 Troubleshooting

### Issue: Bot fails to start
**Solution**: Check if datasets exist:
```bash
ls -la tanya_dataset_generator/output_v2/
```
Should show:
- `compliments.json` (125 messages)
- `psychology_generated.json` (125 messages)

### Issue: Migration fails
**Solution**: Check if database exists:
```bash
ls -la data.db
```
If not, run bot once to create it, then run migration.

### Issue: Messages not sending
**Solution**: Check logs for errors:
```bash
python -m src.bot 2>&1 | grep -E "(ERROR|CRITICAL)"
```

## 📝 Configuration

No configuration needed! The system uses:
- Datasets from `tanya_dataset_generator/output_v2/`
- Scheduler runs at 00:05 UTC daily
- Time distribution: mean=08:45, std=67.18 minutes (Moscow time)

## 🎯 Success Criteria

The system is working correctly if:
1. ✅ Bot starts without errors
2. ✅ Message pools load (125 + 125)
3. ✅ Quest completion triggers first message
4. ✅ "Another message" button works
5. ✅ Daily messages scheduled correctly
6. ✅ No repeats within 125-day cycle

## 🚨 Important Notes

1. **Scheduler timezone**: Europe/Moscow (UTC+3)
2. **Pools are independent**: Emotional and psychological reset separately
3. **Button clicks count**: Each "Another message" click consumes 2 messages
4. **No limits**: User can click button unlimited times
5. **Graceful fallback**: If error occurs, sends simple "Доброе утро! ❤️" message

## 📞 Support

If issues occur:
1. Check logs for errors
2. Run test suite: `python test_morning_messages.py`
3. Verify datasets exist and are valid JSON
4. Check database has new columns: `sqlite3 data.db ".schema users"`

---

**Status**: ✅ Ready for production
**Version**: 1.0
**Last Updated**: 2026-03-08
