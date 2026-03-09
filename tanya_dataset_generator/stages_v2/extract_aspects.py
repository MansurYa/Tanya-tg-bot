"""Extract compliment aspects from context"""

import json
from pathlib import Path


def extract_aspects_from_context():
    """
    Extract compliment aspects from TANYA_AND_MANSUR_CONTEXT.md
    """

    aspects = {
        "appearance": [
            {
                "id": "eyes",
                "description": "Большие голубые глаза",
                "personal_anchors": ["большие голубые глаза", "голубые глаза"],
                "target_variants": 10
            },
            {
                "id": "skin",
                "description": "Мягкая, нежная кожа",
                "personal_anchors": ["мягкая кожа", "кожа"],
                "target_variants": 8
            },
            {
                "id": "smile",
                "description": "Улыбка",
                "personal_anchors": ["улыбка"],
                "target_variants": 10
            },
            {
                "id": "body",
                "description": "Тело, физическое присутствие",
                "personal_anchors": ["тело", "ребра"],
                "target_variants": 8
            }
        ],
        "talents": [
            {
                "id": "song",
                "description": "Первая песня получилась топовой",
                "personal_anchors": ["первая песня", "топовая", "музыка"],
                "target_variants": 10
            },
            {
                "id": "book",
                "description": "Пишет книгу, создает истории",
                "personal_anchors": ["книга", "писательство"],
                "target_variants": 10
            },
            {
                "id": "coding",
                "description": "Программирование, код",
                "personal_anchors": ["код", "программирование"],
                "target_variants": 8
            },
            {
                "id": "math",
                "description": "Математика, аналитическое мышление",
                "personal_anchors": ["математика", "матмех"],
                "target_variants": 8
            },
            {
                "id": "creativity",
                "description": "Креативность, творчество",
                "personal_anchors": ["творчество", "рисование"],
                "target_variants": 8
            }
        ],
        "character": [
            {
                "id": "strength",
                "description": "Внутренняя сила, стойкость",
                "personal_anchors": [],
                "target_variants": 10
            },
            {
                "id": "resilience",
                "description": "Способность продолжать несмотря ни на что",
                "personal_anchors": ["депрессия"],
                "target_variants": 10
            },
            {
                "id": "empathy",
                "description": "Эмпатия, способность чувствовать",
                "personal_anchors": [],
                "target_variants": 8
            },
            {
                "id": "honesty",
                "description": "Честность, открытость",
                "personal_anchors": [],
                "target_variants": 8
            },
            {
                "id": "intelligence",
                "description": "Ум, способность понимать",
                "personal_anchors": [],
                "target_variants": 8
            }
        ],
        "relationship": [
            {
                "id": "care",
                "description": "Забота о близких",
                "personal_anchors": ["кот Крем", "забота о близких"],
                "target_variants": 8
            },
            {
                "id": "presence",
                "description": "Просто быть рядом",
                "personal_anchors": [],
                "target_variants": 8
            },
            {
                "id": "warmth",
                "description": "Тепло, которое она дает",
                "personal_anchors": [],
                "target_variants": 8
            }
        ],
        "daily_life": [
            {
                "id": "morning",
                "description": "Утро, начало дня",
                "personal_anchors": [],
                "target_variants": 8
            },
            {
                "id": "moments",
                "description": "Маленькие моменты вместе",
                "personal_anchors": ["наггетсы KFC", "Ritter Sport", "пицца Песто"],
                "target_variants": 8
            },
            {
                "id": "memories",
                "description": "Воспоминания",
                "personal_anchors": ["зеленый мед"],
                "target_variants": 8
            }
        ]
    }

    # Flatten to list
    all_aspects = []
    for category, aspect_list in aspects.items():
        for aspect in aspect_list:
            aspect["category"] = category
            all_aspects.append(aspect)

    return all_aspects


if __name__ == "__main__":
    aspects = extract_aspects_from_context()

    total_variants = sum(a["target_variants"] for a in aspects)

    print(f"Extracted {len(aspects)} aspects")
    print(f"Target variants: {total_variants}")

    # Save
    output = {
        "version": "1.0",
        "total_aspects": len(aspects),
        "target_variants": total_variants,
        "aspects": aspects
    }

    with open('output_v2/aspects.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("Saved to output_v2/aspects.json")
