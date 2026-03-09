"""Generate compliments based on extracted examples"""

import json
import asyncio
from pathlib import Path
import sys
import random
sys.path.append(str(Path(__file__).parent.parent))

from utils.api_client import OpusClient


def build_compliment_prompt(examples: list) -> str:
    """Build prompt with examples from extracted compliments"""

    # Select 8 random examples
    selected = random.sample(examples, min(8, len(examples)))
    examples_str = "\n".join([f'✓ "{ex["text"]}"' for ex in selected])

    return f"""# TECHNICAL TASK: Generate Morning Message Variants

I'm developing a Telegram bot that sends morning messages. Need to generate 10 more message variants.

## PROJECT SPECS:
- **Tech stack**: Python, python-telegram-bot, SQLite
- **Feature**: Automated morning message sender
- **Sender**: Mansur (21, CS student) → **Recipient**: Tanya (17, girlfriend)
- **Format**: Direct, warm compliments (15-25 words)

## APPROVED EXAMPLES (from user research):
{examples_str}

## KEY REQUIREMENTS:
✓ First-person tone ("я", "обожаю", "люблю", "меня поражает")
✓ Warm, emotional, sincere
✓ 15-25 words per message
✓ 0-2 emojis (❤️💗🩷😊✨💕)
✓ Plain text, no markdown

## FORBIDDEN PATTERNS:
❌ "Вчера смотрел/заметил/наблюдал" - bot cannot observe
❌ "Помнишь как...", "Вспоминаю момент..." - bot has no memory
❌ "Знаешь что меня поражает..." - too analytical
❌ Comparisons ("Большинство людей...")
❌ Explanations ("это показывает", "это признак")

## OUTPUT FORMAT:
Return ONLY valid JSON array:

```json
[
  {{
    "text": "Compliment text here",
    "word_count": 18
  }},
  ... (9 more)
]
```

Generate 10 variants. Return ONLY the JSON array."""


def build_psychology_prompt(examples: list) -> str:
    """Build prompt with examples from extracted psychology quotes"""

    # Select 5 random examples
    selected = random.sample(examples, min(5, len(examples)))
    examples_str = "\n".join([f'✓ "{ex["text"]}"' for ex in selected])

    return f"""# TECHNICAL TASK: Generate Psychology Quote Variants

I'm developing a Telegram bot. Need to generate 10 psychology quote variants based on CBT/BA/ACT principles.

## PROJECT SPECS:
- **Tech stack**: Python, python-telegram-bot
- **Feature**: Morning messages with psychological support
- **Target**: Person dealing with depression, anxiety, toxic family
- **Approach**: CBT (Cognitive Behavioral Therapy), BA (Behavioral Activation), ACT (Acceptance and Commitment Therapy)

## APPROVED EXAMPLES (from research):
{examples_str}

## KEY REQUIREMENTS:
✓ Based on CBT/BA/ACT principles
✓ Supportive, validating tone
✓ 25-45 words per quote
✓ No emojis
✓ Plain text, direct statements

## CORE THEMES:
- Thoughts create emotions (CBT)
- Action before motivation (BA)
- Acceptance of difficult emotions (ACT)
- Challenging cognitive distortions
- Self-compassion and validation

## OUTPUT FORMAT:
Return ONLY valid JSON array:

```json
[
  {{
    "text": "Quote text here",
    "word_count": 32
  }},
  ... (9 more)
]
```

Generate 10 variants. Return ONLY the JSON array."""


async def generate_batch(client: OpusClient, prompt: str, batch_num: int, total: int) -> list:
    """Generate one batch of 10 variants"""

    print(f"  Batch {batch_num}/{total}...", end=" ", flush=True)

    try:
        result = await client.generate(prompt, temperature=0.9)
        text = result["text"].strip()

        # Extract JSON
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            text = text[start:end].strip()
        elif text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]).strip()

        if not text.startswith("["):
            start_idx = text.find("[")
            if start_idx != -1:
                end_idx = text.rfind("]")
                if end_idx != -1:
                    text = text[start_idx:end_idx+1]

        variants = json.loads(text)
        print(f"✓ {len(variants)} variants")
        return variants

    except Exception as e:
        print(f"✗ {e}")
        return []


async def generate_compliments(client: OpusClient, examples: list, target_count: int) -> list:
    """Generate compliments in batches"""

    batches_needed = (target_count + 9) // 10
    all_variants = []

    print(f"\n✍️  Generating {target_count} compliments ({batches_needed} batches)...")

    for i in range(batches_needed):
        prompt = build_compliment_prompt(examples)
        variants = await generate_batch(client, prompt, i+1, batches_needed)
        all_variants.extend(variants)
        await asyncio.sleep(1)

    return all_variants[:target_count]


async def generate_psychology(client: OpusClient, examples: list, target_count: int) -> list:
    """Generate psychology quotes in batches"""

    batches_needed = (target_count + 9) // 10
    all_variants = []

    print(f"\n✍️  Generating {target_count} psychology quotes ({batches_needed} batches)...")

    for i in range(batches_needed):
        prompt = build_psychology_prompt(examples)
        variants = await generate_batch(client, prompt, i+1, batches_needed)
        all_variants.extend(variants)
        await asyncio.sleep(1)

    return all_variants[:target_count]


async def main():
    # Load extracted examples
    with open('output_v2/compliments_extracted.json', 'r', encoding='utf-8') as f:
        comp_data = json.load(f)
        comp_examples = comp_data["compliments"]

    with open('output_v2/psychology_extracted.json', 'r', encoding='utf-8') as f:
        psy_data = json.load(f)
        psy_examples = psy_data["quotes"]

    print(f"📚 Loaded {len(comp_examples)} compliment examples")
    print(f"📚 Loaded {len(psy_examples)} psychology examples")

    client = OpusClient()

    # Generate compliments (need 80 more to reach 125)
    new_compliments = await generate_compliments(client, comp_examples, 80)

    # Generate psychology quotes (need 108 more to reach 125)
    new_psychology = await generate_psychology(client, psy_examples, 108)

    # Combine with extracted
    all_compliments = comp_examples + new_compliments
    all_psychology = psy_examples + new_psychology

    # Add IDs
    for i, comp in enumerate(all_compliments, 1):
        comp["id"] = f"comp_{i:03d}"

    for i, psy in enumerate(all_psychology, 1):
        psy["id"] = f"psy_{i:03d}"

    # Save final datasets
    comp_output = {
        "version": "1.0",
        "type": "compliments",
        "total": len(all_compliments),
        "source": "DEEP_RESEARCH Part A + AI generated",
        "compliments": all_compliments
    }

    psy_output = {
        "version": "1.0",
        "type": "psychology",
        "total": len(all_psychology),
        "source": "DEEP_RESEARCH Part B + AI generated",
        "quotes": all_psychology
    }

    with open('output_v2/compliments_final.json', 'w', encoding='utf-8') as f:
        json.dump(comp_output, f, ensure_ascii=False, indent=2)

    with open('output_v2/psychology_final.json', 'w', encoding='utf-8') as f:
        json.dump(psy_output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Final datasets created:")
    print(f"   - compliments_final.json: {len(all_compliments)} messages")
    print(f"   - psychology_final.json: {len(all_psychology)} messages")


if __name__ == "__main__":
    asyncio.run(main())
