"""
Database migration script to add morning messages fields.

Run this once to update existing database with new columns.
"""

import sqlite3
import sys

DB_PATH = "data.db"

def migrate():
    """Add new columns for morning messages feature."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if columns already exist
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]

    new_columns = [
        ("morning_messages_enabled", "INTEGER DEFAULT 0"),
        ("emotional_pool_shown_ids", "TEXT DEFAULT '[]'"),
        ("psychological_pool_shown_ids", "TEXT DEFAULT '[]'"),
        ("emotional_cycle_number", "INTEGER DEFAULT 1"),
        ("psychological_cycle_number", "INTEGER DEFAULT 1"),
        ("last_morning_message_date", "TEXT"),
        ("next_morning_message_time", "TEXT"),
    ]

    added_count = 0

    for col_name, col_type in new_columns:
        if col_name not in columns:
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                print(f"✅ Added column: {col_name}")
                added_count += 1
            except sqlite3.OperationalError as e:
                print(f"⚠️  Could not add {col_name}: {e}")
        else:
            print(f"⏭  Column {col_name} already exists")

    conn.commit()
    conn.close()

    if added_count > 0:
        print(f"\n✅ Migration complete! Added {added_count} new columns.")
    else:
        print(f"\n✅ Database already up to date.")

if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)
