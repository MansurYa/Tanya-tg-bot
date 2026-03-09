#!/usr/bin/env python3
"""Verify support messages are correctly loaded."""

import re

# Read bot.py and extract the responses dictionary
with open('src/bot.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the responses dictionary
match = re.search(r'responses = \{(.*?)\n    \}', content, re.DOTALL)
if not match:
    print("❌ Could not find responses dictionary")
    exit(1)

responses_text = match.group(0)

# Count messages in each category by counting string literals
sad_section = responses_text[responses_text.find('"support_sad"'):responses_text.find('"support_hug"')]
hug_section = responses_text[responses_text.find('"support_hug"'):responses_text.rfind(']')]

# Count actual message strings using regex
import re
sad_messages = re.findall(r'"[^"]*[❤️💕💗💖💝💓🫂🤗😌🥰🫶⚓][^"]*"', sad_section)
hug_messages = re.findall(r'"[^"]*[❤️💕💗💖💝💓🫂🤗😌🥰🫶⚓💋🪺][^"]*"', hug_section)

sad_count = len(sad_messages)
hug_count = len(hug_messages)

print("✅ Support Messages Verification")
print(f"\n📊 Message Counts:")
print(f"  😢 Мне грустно: {sad_count} variants")
print(f"  🤗 Хочу на ручки: {hug_count} variants")

if sad_count == 10 and hug_count == 10:
    print("\n✅ PASS: All 20 messages loaded correctly")
else:
    print(f"\n❌ FAIL: Expected 10+10, got {sad_count}+{hug_count}")
    exit(1)

# Verify messages use contextual emojis (not just 💙)
emoji_count = len([c for c in responses_text if ord(c) > 0x1F300])
if emoji_count >= 20:  # At least one emoji per message
    print(f"\n✅ Messages use contextual emojis ({emoji_count} total)")
else:
    print(f"\n⚠️  WARNING: Not enough emojis ({emoji_count} found, expected 20+)")

# Check for forbidden phrases
forbidden = ['всё будет хорошо', 'навсегда', 'моя собственность']
found_forbidden = []
for phrase in forbidden:
    if phrase.lower() in responses_text.lower():
        found_forbidden.append(phrase)

if found_forbidden:
    print(f"\n⚠️  WARNING: Found forbidden phrases: {found_forbidden}")
else:
    print("✅ No forbidden phrases detected")

print("\n✅ Verification complete")
