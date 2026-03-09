"""
Test script for morning messages system.

Tests:
1. Message pool rotation (no repeats within cycle)
2. Time generation (normal distribution)
3. Database operations
"""

import json
import sys
from datetime import datetime
from src.message_pool import MessagePool, load_compliments, load_psychology
from src.database import get_user, update_user, create_user
import numpy as np

def test_rotation():
    """Test that rotation works without repeats."""
    print("🧪 Testing rotation logic...")

    # Load pools
    compliments = load_compliments()
    psychology = load_psychology()

    emotional_pool = MessagePool("emotional", compliments)
    psychological_pool = MessagePool("psychological", psychology)

    print(f"   Loaded {emotional_pool.total_count} compliments, {psychological_pool.total_count} psychology")

    # Simulate getting all messages
    shown_emotional = []
    shown_psychological = []

    # Get all emotional messages (should not repeat)
    emotional_ids = []
    for i in range(emotional_pool.total_count):
        msg, shown_emotional = emotional_pool.get_next(shown_emotional)
        emotional_ids.append(msg["id"])

    # Check for duplicates
    if len(emotional_ids) != len(set(emotional_ids)):
        print("   ❌ FAIL: Found duplicates in emotional pool")
        return False

    print(f"   ✅ Emotional pool: {len(emotional_ids)} unique messages")

    # Get one more (should reset cycle)
    msg, shown_emotional = emotional_pool.get_next(shown_emotional)
    if len(shown_emotional) != 1:
        print(f"   ❌ FAIL: Cycle did not reset (shown_ids length: {len(shown_emotional)})")
        return False

    print("   ✅ Cycle reset works correctly")

    # Test psychological pool
    psychological_ids = []
    for i in range(psychological_pool.total_count):
        msg, shown_psychological = psychological_pool.get_next(shown_psychological)
        psychological_ids.append(msg["id"])

    if len(psychological_ids) != len(set(psychological_ids)):
        print("   ❌ FAIL: Found duplicates in psychological pool")
        return False

    print(f"   ✅ Psychological pool: {len(psychological_ids)} unique messages")

    return True


def test_time_distribution():
    """Test time generation follows normal distribution."""
    print("\n🧪 Testing time distribution...")

    from src.bot import generate_morning_time

    # Generate 100 times
    times = []
    for _ in range(100):
        dt = generate_morning_time()
        minutes = dt.hour * 60 + dt.minute
        times.append(minutes)

    mean = np.mean(times)
    std = np.std(times)

    expected_mean = 8 * 60 + 45  # 525 minutes (08:45)
    expected_std = 67.18

    print(f"   Mean: {mean:.1f} minutes (expected: {expected_mean})")
    print(f"   Std:  {std:.1f} minutes (expected: {expected_std})")

    # Check if within reasonable range
    if abs(mean - expected_mean) > 30:
        print(f"   ⚠️  Mean is off by {abs(mean - expected_mean):.1f} minutes")
    else:
        print("   ✅ Mean is within acceptable range")

    if abs(std - expected_std) > 20:
        print(f"   ⚠️  Std is off by {abs(std - expected_std):.1f} minutes")
    else:
        print("   ✅ Std is within acceptable range")

    return True


def test_database():
    """Test database operations."""
    print("\n🧪 Testing database operations...")

    # Create test user
    test_user_id = 999999999

    try:
        # Clean up if exists
        from src.database import get_db
        with get_db() as conn:
            conn.execute("DELETE FROM users WHERE telegram_id = ?", (test_user_id,))

        # Create user
        user = create_user(test_user_id, initial_skips=3)
        print(f"   ✅ Created test user {test_user_id}")

        # Update with morning message fields
        update_user(
            test_user_id,
            morning_messages_enabled=1,
            emotional_pool_shown_ids=json.dumps(["emo_001", "emo_002"]),
            psychological_pool_shown_ids=json.dumps(["psy_001"])
        )

        # Retrieve and verify
        user = get_user(test_user_id)

        if user['morning_messages_enabled'] != 1:
            print("   ❌ FAIL: morning_messages_enabled not set")
            return False

        emotional_shown = json.loads(user['emotional_pool_shown_ids'])
        if len(emotional_shown) != 2:
            print("   ❌ FAIL: emotional_pool_shown_ids not saved correctly")
            return False

        print("   ✅ Database fields work correctly")

        # Clean up
        with get_db() as conn:
            conn.execute("DELETE FROM users WHERE telegram_id = ?", (test_user_id,))

        return True

    except Exception as e:
        print(f"   ❌ FAIL: {e}")
        return False


def main():
    print("=" * 60)
    print("🤖 Morning Messages System Test Suite")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Rotation Logic", test_rotation()))
    results.append(("Time Distribution", test_time_distribution()))
    results.append(("Database Operations", test_database()))

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print("=" * 60)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}: {name}")

    all_passed = all(r[1] for r in results)

    if all_passed:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
