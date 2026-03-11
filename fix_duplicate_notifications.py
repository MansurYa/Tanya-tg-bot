"""
Fix duplicate notifications issue.

This script disables old notification system for users who have
the new morning messages system enabled.

SAFE TO RUN MULTIPLE TIMES - idempotent operation.
"""

import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

DB_PATH = "data.db"

def create_backup():
    """Create a backup of the database before making changes."""
    if not Path(DB_PATH).exists():
        print(f"❌ Database not found at {DB_PATH}")
        return False

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"data.db.backup_{timestamp}"

    try:
        shutil.copy2(DB_PATH, backup_path)
        print(f"✅ Backup created: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to create backup: {e}")
        return False

def fix_notifications():
    """Disable old notifications for users with new morning messages."""

    # Create backup first
    if not create_backup():
        print("⚠️  Proceeding without backup...")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Find users with both systems enabled
        cursor.execute("""
            SELECT telegram_id, morning_messages_enabled, notifications_enabled, state
            FROM users
            WHERE morning_messages_enabled = 1 AND notifications_enabled = 1
        """)

        affected_users = cursor.fetchall()

        if not affected_users:
            print("✅ No users need fixing. All good!")
            conn.close()
            return

        print(f"\nFound {len(affected_users)} users with duplicate notifications:")
        for user_id, morning, notif, state in affected_users:
            print(f"  - User {user_id}: state={state}, morning_messages={morning}, notifications={notif}")

        # Fix: disable old notification system
        cursor.execute("""
            UPDATE users
            SET notifications_enabled = 0
            WHERE morning_messages_enabled = 1 AND notifications_enabled = 1
        """)

        conn.commit()
        rows_updated = cursor.rowcount

        # Verify the fix
        cursor.execute("""
            SELECT COUNT(*) FROM users
            WHERE morning_messages_enabled = 1 AND notifications_enabled = 1
        """)
        remaining = cursor.fetchone()[0]

        conn.close()

        print(f"\n✅ Fixed {rows_updated} users. Old notification system disabled.")
        print("Now only the new morning messages system will send messages.")

        if remaining > 0:
            print(f"⚠️  Warning: {remaining} users still have both systems enabled!")
        else:
            print("✅ Verification passed: no users have duplicate notifications.")

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        raise

if __name__ == "__main__":
    print("=" * 60)
    print("Fix Duplicate Notifications Script")
    print("=" * 60)

    try:
        fix_notifications()
        print("\n" + "=" * 60)
        print("✅ Script completed successfully!")
        print("=" * 60)
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ Script failed: {e}")
        print("=" * 60)
        exit(1)
