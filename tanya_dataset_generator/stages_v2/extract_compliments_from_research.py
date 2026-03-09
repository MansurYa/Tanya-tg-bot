"""Extract compliments from DEEP_RESEARCH.md Part A"""

import json
import re

def extract_compliments():
    """Extract ПЕРЕВОД field from Part A compliments"""
    
    with open('data/DEEP_RESEARCH.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find Part A section
    part_a_start = content.find('ЧАСТЬ A: ЭМОЦИОНАЛЬНЫЙ КОНТЕНТ')
    part_b_start = content.find('ЧАСТЬ B: ПСИХОЛОГИЧЕСКИЙ КОНТЕНТ')
    
    if part_a_start == -1 or part_b_start == -1:
        print("❌ Could not find Part A boundaries")
        return []
    
    part_a = content[part_a_start:part_b_start]
    
    # Extract compliments using pattern: ПЕРЕВОД: "..."
    pattern = r'ПЕРЕВОД:\s*"([^"]+)"'
    matches = re.findall(pattern, part_a, re.DOTALL)
    
    print(f"Found {len(matches)} compliments in Part A")
    
    compliments = []
    for i, text in enumerate(matches, 1):
        # Clean up
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)
        
        word_count = len(text.split())
        
        compliments.append({
            "id": f"comp_{i:03d}",
            "text": text,
            "word_count": word_count,
            "source": "DEEP_RESEARCH_Part_A"
        })
        
        print(f"  [{i}] {word_count} words: {text[:70]}...")
    
    return compliments


if __name__ == "__main__":
    compliments = extract_compliments()
    
    output = {
        "version": "1.0",
        "type": "compliments",
        "total": len(compliments),
        "source": "DEEP_RESEARCH.md Part A (curated from Reddit/research)",
        "compliments": compliments
    }
    
    with open('output_v2/compliments_extracted.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Saved {len(compliments)} compliments to output_v2/compliments_extracted.json")
    
    # Show statistics
    word_counts = [c['word_count'] for c in compliments]
    print(f"\nWord count stats:")
    print(f"  Min: {min(word_counts)}")
    print(f"  Max: {max(word_counts)}")
    print(f"  Avg: {sum(word_counts)/len(word_counts):.1f}")
