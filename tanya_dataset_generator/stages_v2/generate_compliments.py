"""Generate compliment variants"""

import json
import asyncio
from pathlib import Path
from typing import List, Dict
import sys
sys.path.append(str(Path(__file__).parent.parent))

from utils.api_client import OpusClient


EMOJI_WHITELIST = "❤️💗🩷❤️‍🔥❤️‍🩹💔❣️💕💞💓💖💘💝😀😃😄😁😆😅😂🤣🥲🥺☺️😊😇🙂🙃😉😌😍🥰😘😗😙😚😋😛😝😜🤪🤨🧐🤓😎🥸🤩🥳😏😒😞😔😟😕🙁☹️😣😖😫😩😢😭😤😠😡🤬🤯😳🥵🥶😱😨😰😥😓🫣🤗🫡🤔🤭🥱🤫🤥😶😶‍🌫️😐😑😬🫨🫠🙄😯😦😧😮😲😴🤤😪😵😵‍💫🫥🤐🥴🤢🤮🤧😷🤒🤕🤑🤠😈👿👹👺🤡💩👻💀☠️👽🥷🖐️👱‍♀️🤷‍♂️🙏🫰💪💋🥀💸⛽🧱🔋"


def build_generation_prompt(aspect: Dict) -> str:
    """Build prompt for generating 10 compliment variants"""

    anchors_str = ", ".join(aspect["personal_anchors"]) if aspect["personal_anchors"] else "нет"

    return f"""# TECHNICAL TASK: Dataset Generation for Telegram Bot

I'm developing a Telegram bot that sends morning messages. This is a software development project.

## PROJECT SPECS:
- **Tech stack**: Python, python-telegram-bot, SQLite, APScheduler
- **Feature**: Automated morning message sender
- **Data structure**: JSON dataset with message rotation algorithm
- **Sender persona**: Mansur (21, CS student)
- **Recipient**: Tanya (17, girlfriend)
- **Delivery**: One message per morning at 08:45 UTC+3 (±67min normal distribution)

## CURRENT TASK:
Generate 10 message variants for: **{aspect['description']}**
Personal details to incorporate: {anchors_str}

## MESSAGE REQUIREMENTS:
**Format**: Direct, warm compliments from boyfriend to girlfriend
**Length**: 10-20 words
**Emojis**: 0-2 per message
**Tone**: First-person ("я", "обожаю", "люблю"), sincere, affectionate
**Style**: Plain text, no markdown

## APPROVED EXAMPLES (from user testing):
✓ "Тань, люблю тебя, пусть этот день наполнит тебя новыми впечатлениями!"
✓ "Ты у меня лучшая при лучшая, обожаю тебя ❤️"
✓ "Всегда буду поражаться твоим скрытым талантам ✨"
✓ "Обожаю твои большие голубые глаза 💗"
✓ "Твоя улыбка - самое красивое на свете"

## FORBIDDEN PATTERNS (break bot logic):
❌ "Вчера смотрел/заметил/наблюдал" - bot cannot observe
❌ "Знаешь что меня поражает..." - too analytical
❌ "Большинство людей..." - comparisons not allowed
❌ "Помнишь как...", "Вспоминаю момент..." - bot has no memory
❌ Explanations ("это показывает", "это признак") - not in scope

## OUTPUT FORMAT:
Return ONLY valid JSON array:

```json
[
  {{
    "variant_id": 1,
    "text": "Обожаю твои большие голубые глаза ❤️",
    "word_count": 5,
    "emojis_used": ["❤️"]
  }},
  {{
    "variant_id": 2,
    "text": "Твоя улыбка делает мой день лучше",
    "word_count": 6,
    "emojis_used": []
  }},
  ... (8 more variants)
]
```

Generate 10 variants. Return ONLY the JSON array."""


async def generate_variants_for_aspect(client: OpusClient, aspect: Dict) -> List[Dict]:
    """Generate 10 variants for one aspect"""

    prompt = build_generation_prompt(aspect)

    try:
        result = await client.generate(prompt, temperature=0.9)

        # Parse JSON
        text = result["text"].strip()

        # Remove markdown if present
        if "```json" in text:
            # Extract JSON from markdown block
            start = text.find("```json") + 7
            end = text.find("```", start)
            text = text[start:end].strip()
        elif text.startswith("```"):
            # Generic markdown block
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]).strip()

        # Try to find JSON array in text
        if not text.startswith("["):
            # Look for [ in the text
            start_idx = text.find("[")
            if start_idx != -1:
                end_idx = text.rfind("]")
                if end_idx != -1:
                    text = text[start_idx:end_idx+1]

        variants = json.loads(text)

        # Add aspect_id to each variant
        for variant in variants:
            variant["aspect_id"] = aspect["id"]
            variant["category"] = aspect["category"]

        return variants

    except Exception as e:
        print(f"❌ Failed to generate variants for {aspect['id']}: {e}")
        # Print first 200 chars of response for debugging
        if 'result' in locals() and result:
            print(f"   Response preview: {result['text'][:200]}...")
        return []


async def generate_all_variants(aspects: List[Dict], client: OpusClient) -> List[Dict]:
    """Generate variants for all aspects"""

    all_variants = []

    print(f"\n✍️  Generating variants for {len(aspects)} aspects...")

    for i, aspect in enumerate(aspects, 1):
        print(f"  [{i}/{len(aspects)}] {aspect['id']}...", end=" ", flush=True)

        variants = await generate_variants_for_aspect(client, aspect)

        if variants:
            all_variants.extend(variants)
            print(f"✓ {len(variants)} variants")
        else:
            print("✗ failed")

        # Small delay to avoid rate limits
        await asyncio.sleep(1)

    return all_variants


if __name__ == "__main__":
    async def main():
        # Load aspects
        with open('output_v2/aspects.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            aspects = data["aspects"]

        # Initialize client
        client = OpusClient()

        # Generate variants
        variants = await generate_all_variants(aspects, client)

        print(f"\n✅ Generated {len(variants)} total variants")

        # Save
        output = {
            "version": "1.0",
            "total_variants": len(variants),
            "variants": variants
        }

        with open('output_v2/compliment_variants.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"Saved to output_v2/compliment_variants.json")

    asyncio.run(main())
