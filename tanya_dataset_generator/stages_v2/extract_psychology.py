"""Extract psychology quotes from DEEP_RESEARCH.md"""

import json
import re
from pathlib import Path

def extract_psychology_quotes():
    """Extract Russian translations of psychology quotes from Part B"""

    with open('data/DEEP_RESEARCH.md', 'r', encoding='utf-8') as f:
        content = f.read()

    # Find Part B section
    part_b_start = content.find('ЧАСТЬ B: ПСИХОЛОГИЧЕСКИЙ КОНТЕНТ')
    part_c_start = content.find('ЧАСТЬ C: АНТИ-ПРИМЕРЫ')

    if part_b_start == -1 or part_c_start == -1:
        print("❌ Could not find Part B boundaries")
        return []

    part_b = content[part_b_start:part_c_start]

    # Extract quotes using pattern matching
    quotes = []

    # Pattern: ПЕРЕВОД НА РУССКИЙ: "..."
    pattern = r'ПЕРЕВОД НА РУССКИЙ:\s*"([^"]+)"'
    matches = re.findall(pattern, part_b, re.DOTALL)

    print(f"Found {len(matches)} psychology quotes")

    for i, text in enumerate(matches, 1):
        # Clean up text
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace

        # Count words
        word_count = len(text.split())

        quotes.append({
            "id": f"psy_{i:03d}",
            "text": text,
            "word_count": word_count,
            "source": "DEEP_RESEARCH_Part_B"
        })

        print(f"  [{i}] {word_count} words: {text[:60]}...")

    return quotes


if __name__ == "__main__":
    quotes = extract_psychology_quotes()

    output = {
        "version": "1.0",
        "type": "psychology",
        "total": len(quotes),
        "source": "DEEP_RESEARCH.md Part B (CBT/BA/ACT)",
        "quotes": quotes
    }

    with open('output_v2/psychology_extracted.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Saved {len(quotes)} psychology quotes to output_v2/psychology_extracted.json")
