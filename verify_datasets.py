"""
Verify that morning message datasets are loaded correctly.

Run this script on the server to check:
- Dataset files exist
- JSON structure is valid
- Message pools can be loaded
- Sample messages are displayed
"""

import json
import sys
from pathlib import Path

def check_file_exists(filepath):
    """Check if file exists and return its size."""
    path = Path(filepath)
    if not path.exists():
        return False, 0
    return True, path.stat().st_size

def load_and_validate_json(filepath, expected_key):
    """Load JSON file and validate structure."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if expected_key not in data:
            return False, f"Missing key '{expected_key}'", None

        items = data[expected_key]
        if not isinstance(items, list):
            return False, f"'{expected_key}' is not a list", None

        if len(items) == 0:
            return False, f"'{expected_key}' is empty", None

        return True, None, items

    except json.JSONDecodeError as e:
        return False, f"JSON decode error: {e}", None
    except Exception as e:
        return False, f"Error: {e}", None

def verify_message_structure(messages, message_type):
    """Verify that messages have required fields."""
    required_fields = ['id', 'text']
    issues = []

    for i, msg in enumerate(messages[:5]):  # Check first 5
        if not isinstance(msg, dict):
            issues.append(f"Message {i} is not a dict")
            continue

        for field in required_fields:
            if field not in msg:
                issues.append(f"Message {i} missing field '{field}'")

    return issues

def main():
    print("=" * 70)
    print("Dataset Verification Script")
    print("=" * 70)

    all_ok = True

    # Check compliments dataset
    print("\n1. Checking compliments dataset...")
    compliments_path = "tanya_dataset_generator/output_v2/compliments_final.json"

    exists, size = check_file_exists(compliments_path)
    if not exists:
        print(f"   ❌ File not found: {compliments_path}")
        all_ok = False
    else:
        print(f"   ✅ File exists ({size:,} bytes)")

        success, error, compliments = load_and_validate_json(compliments_path, "compliments")
        if not success:
            print(f"   ❌ Validation failed: {error}")
            all_ok = False
        else:
            print(f"   ✅ Loaded {len(compliments)} compliments")

            issues = verify_message_structure(compliments, "compliment")
            if issues:
                print(f"   ⚠️  Structure issues:")
                for issue in issues:
                    print(f"      - {issue}")
                all_ok = False
            else:
                print(f"   ✅ Structure valid")

            # Show sample
            print(f"\n   Sample compliment:")
            sample = compliments[0]
            print(f"   ID: {sample.get('id')}")
            print(f"   Text: {sample.get('text')[:100]}...")

    # Check psychology dataset
    print("\n2. Checking psychology dataset...")
    psychology_path = "tanya_dataset_generator/output_v2/psychology_final.json"

    exists, size = check_file_exists(psychology_path)
    if not exists:
        print(f"   ❌ File not found: {psychology_path}")
        all_ok = False
    else:
        print(f"   ✅ File exists ({size:,} bytes)")

        success, error, psychology = load_and_validate_json(psychology_path, "quotes")
        if not success:
            print(f"   ❌ Validation failed: {error}")
            all_ok = False
        else:
            print(f"   ✅ Loaded {len(psychology)} psychology quotes")

            issues = verify_message_structure(psychology, "psychology")
            if issues:
                print(f"   ⚠️  Structure issues:")
                for issue in issues:
                    print(f"      - {issue}")
                all_ok = False
            else:
                print(f"   ✅ Structure valid")

            # Show sample
            print(f"\n   Sample psychology quote:")
            sample = psychology[0]
            print(f"   ID: {sample.get('id')}")
            print(f"   Text: {sample.get('text')[:100]}...")

    # Test message pool loading
    print("\n3. Testing message pool loading...")
    try:
        from src.message_pool import MessagePool, load_compliments, load_psychology, format_combined_message

        emotional_messages = load_compliments()
        psychological_messages = load_psychology()

        emotional_pool = MessagePool("emotional", emotional_messages)
        psychological_pool = MessagePool("psychological", psychological_messages)

        print(f"   ✅ Emotional pool: {emotional_pool.total_count} messages")
        print(f"   ✅ Psychological pool: {psychological_pool.total_count} messages")

        # Test getting a message
        emotional_msg, _ = emotional_pool.get_next([])
        psychological_msg, _ = psychological_pool.get_next([])

        combined = format_combined_message(emotional_msg["text"], psychological_msg["text"])

        print(f"\n   Sample combined message:")
        print(f"   {'-' * 66}")
        print(f"   {combined}")
        print(f"   {'-' * 66}")

    except ImportError as e:
        print(f"   ❌ Cannot import message_pool: {e}")
        all_ok = False
    except Exception as e:
        print(f"   ❌ Error loading pools: {e}")
        all_ok = False

    # Final result
    print("\n" + "=" * 70)
    if all_ok:
        print("✅ All checks passed! Datasets are ready.")
        print("=" * 70)
        return 0
    else:
        print("❌ Some checks failed. Fix the issues above.")
        print("=" * 70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
