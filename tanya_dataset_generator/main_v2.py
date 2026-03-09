"""Main entry point for dataset generation v2.0"""

import asyncio
import json
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from stages_v2.extract_aspects import extract_aspects_from_context
from stages_v2.extract_psychology import extract_psychology_quotes
from stages_v2.generate_compliments import generate_all_variants
from utils_v2.api_client import OpusClient


async def main():
    print("=" * 60)
    print("🚀 DATASET GENERATOR v2.0")
    print("=" * 60)

    output_dir = Path('output_v2')
    output_dir.mkdir(exist_ok=True)

    # Stage 1: Extract aspects (0 requests)
    print("\n📋 Stage 1: Extracting aspects...")
    aspects = extract_aspects_from_context()
    print(f"✅ Extracted {len(aspects)} aspects")

    # Save aspects
    with open(output_dir / 'aspects.json', 'w', encoding='utf-8') as f:
        json.dump({
            "version": "1.0",
            "total_aspects": len(aspects),
            "aspects": aspects
        }, f, ensure_ascii=False, indent=2)

    # Stage 2: Extract psychology (0 requests)
    print("\n📚 Stage 2: Extracting psychology quotes...")
    psychology = extract_psychology_quotes()

    if len(psychology) == 0:
        print("⚠️  WARNING: No psychology quotes found in DEEP_RESEARCH.md")
        print("   File appears to contain game development context instead")
        print("   Proceeding with compliments only")
    else:
        print(f"✅ Extracted {len(psychology)} quotes")

    # Save psychology
    with open(output_dir / 'psychology.json', 'w', encoding='utf-8') as f:
        json.dump({
            "version": "1.0",
            "type": "psychology_quotes",
            "source": "DEEP_RESEARCH.md",
            "total": len(psychology),
            "quotes": psychology
        }, f, ensure_ascii=False, indent=2)

    # Stage 3: Generate compliment variants (~20 requests)
    print("\n✍️  Stage 3: Generating compliment variants...")
    print(f"   This will make ~{len(aspects)} API requests")
    print(f"   Estimated time: ~{len(aspects) * 2} seconds")

    client = OpusClient()
    variants = await generate_all_variants(aspects, client)

    print(f"\n✅ Generated {len(variants)} total variants")

    # Save variants
    with open(output_dir / 'compliment_variants.json', 'w', encoding='utf-8') as f:
        json.dump({
            "version": "1.0",
            "total_variants": len(variants),
            "variants": variants
        }, f, ensure_ascii=False, indent=2)

    # Stage 4: Select best (for now, just take all)
    print("\n⭐ Stage 4: Selecting best compliments...")
    print("   (Simplified: taking all variants)")

    best_compliments = variants

    # Save final compliments
    with open(output_dir / 'compliments.json', 'w', encoding='utf-8') as f:
        json.dump({
            "version": "2.0",
            "type": "compliments",
            "total": len(best_compliments),
            "generation_method": "5_variants_per_aspect",
            "compliments": best_compliments
        }, f, ensure_ascii=False, indent=2)

    # Summary
    print("\n" + "=" * 60)
    print("✅ GENERATION COMPLETE!")
    print("=" * 60)
    print(f"Compliments: {len(best_compliments)}")
    print(f"Psychology quotes: {len(psychology)}")
    print(f"\nFiles created:")
    print(f"  - output_v2/aspects.json")
    print(f"  - output_v2/psychology.json")
    print(f"  - output_v2/compliment_variants.json")
    print(f"  - output_v2/compliments.json")

    if len(psychology) == 0:
        print(f"\n⚠️  NOTE: Psychology quotes dataset is empty")
        print(f"   DEEP_RESEARCH.md does not contain expected quote format")
        print(f"   Manual intervention may be needed")


if __name__ == "__main__":
    asyncio.run(main())
