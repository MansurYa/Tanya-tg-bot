#!/usr/bin/env python3
"""Test script to verify bot datasets and configuration."""

import json
import sys
from pathlib import Path

def main():
    print("=" * 80)
    print("🔍 BOT CONFIGURATION TEST")
    print("=" * 80)

    # Test 1: Load compliments
    print("\n[1/4] Loading compliments dataset...")
    try:
        with open('tanya_dataset_generator/output_v2/compliments_final.json', 'r', encoding='utf-8') as f:
            comp_data = json.load(f)
        print(f"   ✅ Loaded {len(comp_data['compliments'])} compliments")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

    # Test 2: Load psychology
    print("\n[2/4] Loading psychology dataset...")
    try:
        with open('tanya_dataset_generator/output_v2/psychology_final.json', 'r', encoding='utf-8') as f:
            psy_data = json.load(f)
        print(f"   ✅ Loaded {len(psy_data['quotes'])} psychology quotes")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

    # Test 3: Check data structure
    print("\n[3/4] Validating data structure...")
    try:
        # Check compliments structure
        for i, comp in enumerate(comp_data['compliments'][:5]):
            assert 'id' in comp, f"Compliment {i} missing 'id'"
            assert 'text' in comp, f"Compliment {i} missing 'text'"
            assert 'word_count' in comp, f"Compliment {i} missing 'word_count'"

        # Check psychology structure
        for i, psy in enumerate(psy_data['quotes'][:5]):
            assert 'id' in psy, f"Psychology {i} missing 'id'"
            assert 'text' in psy, f"Psychology {i} missing 'text'"
            assert 'word_count' in psy, f"Psychology {i} missing 'word_count'"

        print(f"   ✅ Data structure valid")
    except AssertionError as e:
        print(f"   ❌ Structure error: {e}")
        return False

    # Test 4: Test message pool imports
    print("\n[4/4] Testing message pool imports...")
    try:
        from src.message_pool import load_compliments, load_psychology, MessagePool

        comps = load_compliments()
        psys = load_psychology()

        pool1 = MessagePool('emotional', comps)
        pool2 = MessagePool('psychological', psys)

        print(f"   ✅ Pools initialized: {pool1.total_count} emotional, {pool2.total_count} psychological")

        # Test getting a message
        msg, shown = pool1.get_next([])
        print(f"   ✅ Sample message retrieved: {msg['text'][:50]}...")

    except Exception as e:
        print(f"   ❌ Import/pool test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED - BOT IS READY")
    print("=" * 80)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
