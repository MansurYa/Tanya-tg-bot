# ЗАДАЧА: Автоматическое создание датасета для утреннего бота Тани

## КОНТЕКСТ

Ты — CLI-агент на базе Claude Opus 4.5. Твоя задача: полностью автоматически создать датасет из **365 высококачественных сообщений** для Telegram-бота, который будет отправлять утренние сообщения Тане от имени её парня Мансура.

## ВХОДНЫЕ ДАННЫЕ

В корне проекта лежат 3 файла:
- `TANYA_AND_MANSUR_CONTEXT.md` — полный контекст их отношений (50+ страниц)
- `DEEP_RESEARCH.md` — психологические принципы и комплименты
- `ACTUAL_CONTEXT_OF_BOT.md` — технические требования к боту

## КРИТИЧЕСКИЕ ОГРАНИЧЕНИЯ

1. **Бюджет:** Максимум 100 запросов к Opus 4.6
2. **Автоматизация:** Никакого ручного вмешательства
3. **Качество:** Сообщения должны звучать как реальный Мансур, а не ChatGPT
4. **Формат:** Каждое сообщение = эмоциональный контент (15-25 слов) + психологический принцип (20-35 слов)

## АРХИТЕКТУРА РЕШЕНИЯ

Ты будешь работать в **5 этапов**:

```
Stage 1: Domain Mapping (1 запрос)
  ↓
Stage 2: Batch Generation (80 запросов)
  ↓
Stage 3: Automated Filtering (локально)
  ↓
Stage 4: Comparative Scoring (10 запросов)
  ↓
Stage 5: Final Selection (локально)
```

---

## ЭТАП 0: ПОДГОТОВКА ИНФРАСТРУКТУРЫ

### Структура проекта

Создай следующую структуру:

```
tanya_dataset_generator/
├── main.py                          # CLI entry point
├── config.py                        # API keys, constants
├── requirements.txt                 # Dependencies
├── stages/
│   ├── __init__.py
│   ├── stage1_mapping.py
│   ├── stage2_generation.py
│   ├── stage3_filtering.py
│   ├── stage4_scoring.py
│   └── stage5_selection.py
├── utils/
│   ├── __init__.py
│   ├── api_client.py               # Opus 4.6 client
│   ├── validators.py               # Forbidden phrases, word count
│   └── similarity.py               # Duplicate detection
├── data/
│   ├── TANYA_AND_MANSUR_CONTEXT.md
│   ├── DEEP_RESEARCH.md
│   └── ACTUAL_CONTEXT_OF_BOT.md
└── output/
    ├── checkpoints/                # Incremental saves
    ├── domain_map.json
    ├── raw_messages_all.json
    ├── filtered_messages.json
    ├── all_scores.json
    ├── dataset_final.json
    └── dataset.json                # ГЛАВНЫЙ РЕЗУЛЬТАТ
```

### requirements.txt

```
aiohttp==3.9.1
python-Levenshtein==0.23.0
emoji==2.10.0
tqdm==4.66.1
sentence-transformers==2.2.2
numpy==1.24.3
```

### config.py

```python
"""Configuration for dataset generator"""

# API Configuration
ANTHROPIC_BASE_URL = "https://dev.aiprime.store/api"
ANTHROPIC_AUTH_TOKEN = "cr_dfb54972ac4679d2d916c2af15d50cbd8a62bb51cfd9d18f61034ca462a2ef08"
ANTHROPIC_API_VERSION = "2023-06-01"
MODEL_NAME = "claude-opus-4-20250514"

# Budget
MAX_REQUESTS = 100
STAGE1_REQUESTS = 1
STAGE2_BASE_REQUESTS = 80
STAGE2_RETRY_BUFFER = 5
STAGE4_BASE_REQUESTS = 10
STAGE4_RETRY_BUFFER = 2
RESERVE_REQUESTS = 2

# Generation parameters
MESSAGES_PER_BATCH = 8  # КРИТИЧЕСКИ ВАЖНО: 8, не меньше!
MAX_PARALLEL_REQUESTS = 10
REQUEST_TIMEOUT = 120  # seconds
MAX_RETRIES = 2
BASE_RETRY_DELAY = 2.0  # seconds

# Filtering thresholds
WORD_COUNT_MIN = 35
WORD_COUNT_MAX = 60
DUPLICATE_THRESHOLD_SEMANTIC = 0.85
DUPLICATE_THRESHOLD_LEVENSHTEIN = 0.70
DIVERSITY_THRESHOLD = 0.80

# Target distribution
TARGET_TOTAL = 365
EMOTIONAL_POOL_SIZE = 240
PSYCHOLOGICAL_POOL_SIZE = 125

# Emoji whitelist
EMOJI_WHITELIST = {
    "❤️", "��", "��", "❤️‍��", "❤️‍��", "��", "❣️", "��", "��", "��",
    "��", "��", "��", "��", "��", "��", "��", "��", "��", "��",
    "��", "��", "��", "☺️", "��", "��", "��", "��", "��", "��",
    "��", "��", "��", "��", "��", "��", "��", "��", "��", "��",
    "��", "��", "��", "��", "��", "��", "��", "��", "��", "��",
    "��", "��", "��", "��", "��", "☹️", "��", "��", "��", "��",
    "��", "��", "��", "��", "��", "��", "��", "��", "��", "��",
    "��", "��", "��", "��", "��", "��", "��", "��", "��", "��",
    "��", "��", "��", "��", "��‍��️", "��", "��", "��", "��", "��",
    "��", "��", "��", "��", "��", "��", "��", "��", "��", "��",
    "��‍��", "��", "��", "��", "��", "��", "��", "��", "��", "��",
    "��", "��", "��", "��", "��", "��", "��", "��", "��", "��",
    "☠️", "��", "��", "��️", "��‍♀️", "��‍♂️", "��", "��", "��", "��",
    "��", "��", "⛽", "��", "��"
}

# Forbidden phrases
FORBIDDEN_PHRASES = [
    "напиши мне", "жду ответа", "жду твоего сообщения",
    "моя собственность", "владелец", "мое мясо", "спермоприемник",
    "навсегда", "всегда буду", "никогда не", "обещаю",
    "можешь лежать", "ничего не делай", "просто отдыхай",
    "не обязательно вставать", "весь день в кровати",
    "доброе утро", "просыпайся", "хорошего дня"
]
```

---

## ЭТАП 1: DOMAIN MAPPING (1 запрос)

### Цель
Проанализировать контекст и создать структурированную карту доменов для генерации.

### utils/api_client.py

```python
"""Opus 4.6 API client with retry logic"""

import aiohttp
import asyncio
import json
from typing import Dict, Optional
from config import *

class OpusClient:
    def __init__(self):
        self.base_url = ANTHROPIC_BASE_URL
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "anthropic-version": ANTHROPIC_API_VERSION,
            "x-api-key": ANTHROPIC_AUTH_TOKEN,
        }
    
    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.8,
        max_tokens: int = 4096
    ) -> Dict:
        """Send request to Opus 4.6"""
        body = {
            "model": MODEL_NAME,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "temperature": temperature,
        }
        
        if system:
            body["system"] = [{"type": "text", "text": system}]
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/v1/messages",
                headers=self.headers,
                json=body,
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API Error {response.status}: {error_text}")
                
                data = await response.json()
                text = "".join(
                    block["text"] 
                    for block in data["content"] 
                    if block["type"] == "text"
                )
                
                return {
                    "text": text,
                    "usage": data["usage"],
                    "stop_reason": data["stop_reason"]
                }

async def generate_with_retry(
    client: OpusClient,
    prompt: str,
    max_retries: int = MAX_RETRIES
) -> Optional[Dict]:
    """Generate with exponential backoff retry"""
    for attempt in range(max_retries + 1):
        try:
            result = await client.generate(prompt)
            return result
        except Exception as e:
            if attempt == max_retries:
                print(f"❌ Failed after {max_retries} retries: {e}")
                return None
            
            delay = BASE_RETRY_DELAY * (2 ** attempt)
            print(f"⚠️  Retry {attempt + 1}/{max_retries} after {delay}s: {e}")
            await asyncio.sleep(delay)
    
    return None
```

### stages/stage1_mapping.py

```python
"""Stage 1: Domain Mapping"""

import json
from pathlib import Path
from utils.api_client import OpusClient, generate_with_retry

async def run(client: OpusClient, output_dir: Path) -> dict:
    """Generate domain map from context"""
    
    print("�� Loading context files...")
    
    # Load all context
    context_files = {
        "tanya_context": "data/TANYA_AND_MANSUR_CONTEXT.md",
        "research": "data/DEEP_RESEARCH.md",
        "bot_requirements": "data/CLAUDE_CODE_INSTRUCTIONS.md"
    }
    
    context = {}
    for key, path in context_files.items():
        with open(path, 'r', encoding='utf-8') as f:
            context[key] = f.read()
    
    # Build prompt
    prompt = f"""<task>
Ты — архитектор датасета сообщений. Создай структурированную карту доменов и аспектов.

<context>
{context['tanya_context']}

{context['research']}

{context['bot_requirements']}
</context>

<requirements>
1. Создай 8 базовых доменов:
   
   EMOTIONAL (240 messages total):
   - talents (60): song, book, writing, coding, math, creativity
   - appearance (60): eyes, skin, smile, body, presence
   - strength (60): resilience, capability, overcoming
   - hybrid (60): compliment + gentle motivation
   
   PSYCHOLOGICAL (125 messages total):
   - CBT (50): cognitive reframes, thought-reality separation
   - ACT (35): acceptance, defusion, values
   - behavioral_activation (40): action-motivation, small steps

2. Для каждого домена выдели 6-8 ключевых аспектов.

3. Для каждого аспекта создай 2-3 constraints (требования к сообщению).

4. Извлеки из контекста 30-40 "персональных якорей":
   - Еда: Ritter Sport с мятой, наггетсы KFC, пицца Песто
   - Питомцы: кот Крем, Котэ, Милка
   - Места: зеленый мед, Башкирия, перекресток
   - Мемы: "зарядка от вибратора", первая песня, книга
   - Внешность: большие голубые глаза, мягкая кожа
   - Таланты: программирование, математика, музыка

5. Распредели якоря по аспектам (где они органично впишутся).

6. Для каждого аспекта укажи target_messages (итого должно быть 365).
</requirements>

<output_format>
Верни ТОЛЬКО валидный JSON (без markdown блоков):
{{
  "domains": [
    {{
      "id": "talents",
      "category": "emotional",
      "target_count": 60,
      "aspects": [
        {{
          "id": "song_creation",
          "description": "First song was immediately great",
          "constraints": [
            "mention_first_song",
            "emphasize_natural_talent",
            "use_admiration_tone"
          ],
          "personal_anchors": ["первая песня", "топовая"],
          "target_messages": 8
        }}
      ]
    }}
  ],
  "personal_anchors": {{
    "food": ["Ritter Sport с мятой", "наггетсы KFC"],
    "pets": ["кот Крем", "Котэ"],
    "places": ["зеленый мед", "Башкирия"],
    "memes": ["зарядка от вибратора"]
  }},
  "distribution_check": {{
    "emotional_total": 240,
    "psychological_total": 125,
    "grand_total": 365
  }}
}}
</output_format>

<critical_rules>
- Персональные якоря ОБЯЗАТЕЛЬНЫ
- Распределение должно быть точным (итого 365)
- Constraints конкретные и проверяемые
- Учитывай forbidden phrases из контекста
</critical_rules>
</task>"""
    
    print("�� Sending request to Opus 4.6...")
    result = await generate_with_retry(client, prompt)
    
    if not result:
        raise Exception("Failed to generate domain map")
    
    # Parse JSON
    try:
        domain_map = json.loads(result["text"])
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON response: {e}")
        print(f"Response: {result['text'][:500]}...")
        raise
    
    # Save
    output_file = output_dir / "domain_map.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(domain_map, f, ensure_ascii=False, indent=2)
    
    # Validate
    total = domain_map["distribution_check"]["grand_total"]
    print(f"✅ Domain map created: {len(domain_map['domains'])} domains, {total} target messages")
    
    return domain_map
```

---

## ЭТАП 2: BATCH GENERATION (80 запросов)

### Цель
Сгенерировать ~640 сообщений (80 батчей × 8 сообщений).

### stages/stage2_generation.py

```python
"""Stage 2: Batch Generation with checkpoints"""

import json
import asyncio
from pathlib import Path
from typing import List, Dict, Optional
from tqdm.asyncio import tqdm
from utils.api_client import OpusClient, generate_with_retry
from config import *

async def save_checkpoint(output_dir: Path, batch_id: int, result: Dict):
    """Save checkpoint after each batch"""
    checkpoint_dir = output_dir / "checkpoints"
    checkpoint_dir.mkdir(exist_ok=True)
    
    checkpoint_file = checkpoint_dir / f"batch_{batch_id:03d}.json"
    with open(checkpoint_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

def load_checkpoints(output_dir: Path) -> List[Dict]:
    """Load existing checkpoints"""
    checkpoint_dir = output_dir / "checkpoints"
    if not checkpoint_dir.exists():
        return []
    
    checkpoints = []
    for file in sorted(checkpoint_dir.glob("batch_*.json")):
        with open(file, 'r', encoding='utf-8') as f:
            checkpoints.append(json.load(f))
    
    return checkpoints

def create_batches(domain_map: dict) -> List[Dict]:
    """Create 80 batches from domain map"""
    batches = []
    batch_id = 0
    
    for domain in domain_map["domains"]:
        aspects = domain["aspects"]
        
        # Group aspects into batches of 4-5
        for i in range(0, len(aspects), 4):
            batch_aspects = aspects[i:i+4]
            batches.append({
                "id": batch_id,
                "domain_id": domain["id"],
                "aspects": batch_aspects
            })
            batch_id += 1
    
    return batches[:80]  # Limit to 80

def build_generation_prompt(batch: Dict) -> str:
    """Build prompt for batch generation"""
    
    aspects_json = json.dumps(batch["aspects"], ensure_ascii=False, indent=2)
    
    return f"""<task>
Ты — Мансур, парень Тани. Напиши утренние сообщения для неё.

<context>
Таня: 17 лет, клиническая депрессия, тревожное расстройство, дисморфофобия.
Ты: 21 год, студент матмеха, программист. Любишь её, заботишься.
</context>

<your_voice>
- Говоришь от первого лица ("я", "обожаю", "люблю")
- Тон: теплый, заботливый, естественный
- Можешь использовать легкий мат если уместно
- Избегай markdown, длинных тире (—), используй дефис (-)
</your_voice>

<batch_aspects>
{aspects_json}
</batch_aspects>

<requirements>
Для КАЖДОГО аспекта создай ОДНО сообщение:

1. Формат: [Emotional 15-25 слов] + [Psychological 20-35 слов]
2. Используй constraints из аспекта
3. Вплети personal_anchor ОРГАНИЧНО (не форсированно!)
4. Эмодзи: 0-2 штуки, только из whitelist
5. Длина: 35-60 слов total

<personalization_strategy>
ПЛОХО (механистично):
"Твоя улыбка сладка, как зеленый башкирский мед ��"

ХОРОШО (органично):
"Помнишь, я рассказывал про зеленый мед? Вот так же редко 
встречается твое умение находить красоту в математике"

ПРАВИЛА:
1. Якорь = часть истории, не прямое сравнение
2. Используй только если естественно вписывается
3. Если не подходит — НЕ ИСПОЛЬЗУЙ
4. Максимум 1 якорь на сообщение
</personalization_strategy>

<forbidden_phrases>
КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО:
- "напиши мне", "жду ответа"
- "моя собственность", "владелец"
- "навсегда", "обещаю"
- "можешь лежать", "просто отдыхай"
- "доброе утро" (как основная мысль)
</forbidden_phrases>

<examples>
ПЛОХО: "Доброе утро! Ты моя собственность ❤️"
ХОРОШО: "Твоя первая песня получилась топовой не случайно — у тебя дар чувствовать музыку �� Помни: действие предшествует мотивации, начни с малого ✨"
</examples>
</requirements>

<output_format>
Верни ТОЛЬКО валидный JSON массив (без markdown):
[
  {{
    "aspect_id": "song_creation",
    "text": "...",
    "word_count": 32,
    "emojis_used": ["��", "✨"],
    "personal_anchors_used": ["первая песня"]
  }}
]
</output_format>

<critical>
Если сгенерируешь сообщение с forbidden phrase, оно будет отклонено. Проверяй дважды!
</critical>
</task>"""

class BatchGenerator:
    def __init__(self, client: OpusClient, output_dir: Path):
        self.client = client
        self.output_dir = output_dir
        self.semaphore = asyncio.Semaphore(MAX_PARALLEL_REQUESTS)
        self.failed_batches = []
    
    async def generate_batch_safe(self, batch: Dict) -> Optional[Dict]:
        """Generate batch with error handling"""
        async with self.semaphore:
            prompt = build_generation_prompt(batch)
            
            result = await generate_with_retry(self.client, prompt)
            
            if result:
                try:
                    messages = json.loads(result["text"])
                    batch_result = {
                        "batch_id": batch["id"],
                        "messages": messages,
                        "usage": result["usage"]
                    }
                    await save_checkpoint(self.output_dir, batch["id"], batch_result)
                    return batch_result
                except json.JSONDecodeError:
                    print(f"❌ Batch {batch['id']}: Invalid JSON")
                    self.failed_batches.append(batch["id"])
                    return None
            else:
                self.failed_batches.append(batch["id"])
                return None
    
    async def generate_all(self, batches: List[Dict]) -> List[Dict]:
        """Generate all batches with progress"""
        # Load existing checkpoints
        existing = load_checkpoints(self.output_dir)
        completed_ids = {r["batch_id"] for r in existing}
        
        # Filter pending
        pending = [b for b in batches if b["id"] not in completed_ids]
        
        if existing:
            print(f"�� Resuming: {len(existing)} completed, {len(pending)} pending")
        
        # Generate pending
        tasks = [self.generate_batch_safe(batch) for batch in pending]
        
        results = []
        for coro in tqdm.as_completed(tasks, total=len(tasks), desc="Generating batches"):
            result = await coro
            if result:
                results.append(result)
        
        # Combine
        all_results = existing + results
        
        # Report
        if self.failed_batches:
            print(f"⚠️  Failed batches: {self.failed_batches}")
        
        success_rate = len(all_results) / len(batches) * 100
        print(f"✅ Success rate: {len(all_results)}/{len(batches)} ({success_rate:.1f}%)")
        
        return all_results

async def run(client: OpusClient, domain_map: dict, output_dir: Path) -> List[Dict]:
    """Run Stage 2: Batch Generation"""
    
    print("\n✍️  STAGE 2: Batch Generation")
    print("-" * 60)
    
    # Create batches
    batches = create_batches(domain_map)
    print(f"�� Created {len(batches)} batches")
    
    # Generate
    generator = BatchGenerator(client, output_dir)
    results = await generator.generate_all(batches)
    
    # Flatten messages
    all_messages = []
    for result in results:
        for msg in result["messages"]:
            msg["batch_id"] = result["batch_id"]
            all_messages.append(msg)
    
    # Save
    output_file = output_dir / "raw_messages_all.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_messages, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Generated: {len(all_messages)} messages")
    
    return all_messages
```

---

## ЭТАП 3: AUTOMATED FILTERING (локально)

### utils/validators.py

```python
"""Validation functions"""

import re
import emoji
from config import FORBIDDEN_PHRASES, WORD_COUNT_MIN, WORD_COUNT_MAX, EMOJI_WHITELIST

def check_forbidden(text: str) -> bool:
    """Check for forbidden phrases"""
    text_lower = text.lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in text_lower:
            return False
    return True

def validate_word_count(text: str) -> bool:
    """Validate word count"""
    words = text.split()
    return WORD_COUNT_MIN <= len(words) <= WORD_COUNT_MAX

def validate_emojis(text: str) -> bool:
    """Validate emojis"""
    emojis_in_text = [char for char in text if char in emoji.EMOJI_DATA]
    
    if len(emojis_in_text) > 2:
        return False
    
    return all(e in EMOJI_WHITELIST for e in emojis_in_text)

def detect_chatgpt_patterns(text: str) -> bool:
    """Detect generic ChatGPT patterns"""
    chatgpt_markers = [
        r"важно понимать",
        r"стоит отметить",
        r"следует помнить",
        r"невероятно|потрясающе|фантастически",
        r"как маяк|как звезда|как солнце"
    ]
    
    for pattern in chatgpt_markers:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    return False
```

### utils/similarity.py

```python
"""Similarity detection"""

from typing import List, Dict
from config import DUPLICATE_THRESHOLD_SEMANTIC, DUPLICATE_THRESHOLD_LEVENSHTEIN

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    SEMANTIC_AVAILABLE = True
    print("✅ Semantic similarity enabled")
except ImportError:
    print("⚠️  sentence-transformers not available, using Levenshtein fallback")
    SEMANTIC_AVAILABLE = False

def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity with fallback"""
    if SEMANTIC_AVAILABLE:
        embeddings = model.encode([text1, text2])
        similarity = np.dot(embeddings[0], embeddings[1]) / (
            np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
        )
        return float(similarity)
    else:
        from Levenshtein import distance
        max_len = max(len(text1), len(text2))
        return 1 - (distance(text1, text2) / max_len)

def detect_duplicates(messages: List[Dict]) -> List[Dict]:
    """Remove duplicates"""
    threshold = DUPLICATE_THRESHOLD_SEMANTIC if SEMANTIC_AVAILABLE else DUPLICATE_THRESHOLD_LEVENSHTEIN
    
    unique_messages = []
    seen_texts = []
    
    for msg in messages:
        text = msg["text"]
        is_duplicate = False
        
        for seen_text in seen_texts:
            similarity = calculate_similarity(text, seen_text)
            if similarity > threshold:
                is_duplicate = True
                break

```python
        
        if not is_duplicate:
            unique_messages.append(msg)
            seen_texts.append(text)
    
    return unique_messages
```

### stages/stage3_filtering.py

```python
"""Stage 3: Automated Filtering"""

import json
from pathlib import Path
from typing import List, Dict
from utils.validators import (
    check_forbidden,
    validate_word_count,
    validate_emojis,
    detect_chatgpt_patterns
)
from utils.similarity import detect_duplicates

def run(messages: List[Dict], output_dir: Path) -> List[Dict]:
    """Run Stage 3: Automated Filtering"""
    
    print("\n�� STAGE 3: Automated Filtering")
    print("-" * 60)
    
    initial_count = len(messages)
    
    # Filter 1: Forbidden phrases
    messages = [m for m in messages if check_forbidden(m["text"])]
    print(f"  Forbidden phrases: {initial_count - len(messages)} removed")
    
    # Filter 2: Word count
    count_before = len(messages)
    messages = [m for m in messages if validate_word_count(m["text"])]
    print(f"  Word count: {count_before - len(messages)} removed")
    
    # Filter 3: Emojis
    count_before = len(messages)
    messages = [m for m in messages if validate_emojis(m["text"])]
    print(f"  Invalid emojis: {count_before - len(messages)} removed")
    
    # Filter 4: ChatGPT patterns
    count_before = len(messages)
    messages = [m for m in messages if not detect_chatgpt_patterns(m["text"])]
    print(f"  ChatGPT patterns: {count_before - len(messages)} removed")
    
    # Filter 5: Duplicates
    count_before = len(messages)
    messages = detect_duplicates(messages)
    print(f"  Duplicates: {count_before - len(messages)} removed")
    
    # Save
    output_file = output_dir / "filtered_messages.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)
    
    pass_rate = len(messages) / initial_count * 100
    print(f"✅ Filtered: {len(messages)} messages ({pass_rate:.1f}% pass rate)")
    
    return messages
```

---

## ЭТАП 4: COMPARATIVE SCORING (10 запросов)

### stages/stage4_scoring.py

```python
"""Stage 4: Comparative Scoring"""

import json
import re
from pathlib import Path
from typing import List, Dict
from utils.api_client import OpusClient, generate_with_retry

def extract_real_mansur_examples(context_path: str) -> List[str]:
    """Extract real Mansur messages from context"""
    with open(context_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract messages from Mansur in the chat log
    pattern = r'Мансур[^:]*:\s*([^\n]+)'
    matches = re.findall(pattern, content)
    
    # Filter and clean
    examples = []
    for match in matches:
        # Skip system messages, long messages, empty
        if len(match) < 20 or len(match) > 200:
            continue
        if match.startswith('[') or match.startswith('('):
            continue
        examples.append(match.strip())
    
    # Return first 15 unique
    return list(dict.fromkeys(examples))[:15]

def build_scoring_prompt(messages: List[Dict], real_examples: List[str]) -> str:
    """Build comparative scoring prompt"""
    
    messages_json = json.dumps(
        [{"id": m.get("aspect_id", f"msg_{i}"), "text": m["text"]} 
         for i, m in enumerate(messages)],
        ensure_ascii=False,
        indent=2
    )
    
    examples_text = "\n".join([f"{i+1}. {ex}" for i, ex in enumerate(real_examples)])
    
    return f"""<task>
Перед тобой сообщения для утреннего бота. Оцени, какие звучат как РЕАЛЬНЫЙ Мансур.

<real_mansur_examples>
Вот примеры реальных сообщений Мансура из переписки:

{examples_text}
</real_mansur_examples>

<generated_messages>
{messages_json}
</generated_messages>

<scoring_criteria>
Для каждого сообщения оцени по 4 критериям:

1. СТИЛЬ (0-3): Похоже на стиль Мансура из примеров?
   - Использует похожие обороты?
   - Естественность vs ChatGPT-ность?
   - Допустимы "неидеальности" (как у реального человека)?

2. ТОН (0-3): Соответствует тону?
   - Баланс заботы и прямоты
   - Не слишком приторно/формально?

3. ПЕРСОНАЛИЗАЦИЯ (0-2): Есть специфика Тани?
   - Упоминаются детали их отношений?
   - Или generic для любой девушки?

4. ПОЛЕЗНОСТЬ (0-2): Реально поможет Тане?
   - Конкретная ценность (комплимент/принцип)?
   - Или просто красивые слова?

ИТОГО: 0-10 баллов
</scoring_criteria>

<output_format>
Верни ТОЛЬКО валидный JSON (без markdown):
{{
  "scores": [
    {{
      "message_id": "msg_0",
      "style": 2,
      "tone": 3,
      "personalization": 1,
      "utility": 2,
      "total": 8,
      "reasoning": "Краткое объяснение"
    }}
  ]
}}
</output_format>

<critical>
Будь честен. Если звучит как ChatGPT — ставь низкий балл.
</critical>
</task>"""

async def run(client: OpusClient, messages: List[Dict], output_dir: Path) -> Dict[str, float]:
    """Run Stage 4: Comparative Scoring"""
    
    print("\n⭐ STAGE 4: Comparative Scoring")
    print("-" * 60)
    
    # Extract real examples
    real_examples = extract_real_mansur_examples("data/TANYA_AND_MANSUR_CONTEXT.md")
    print(f"�� Extracted {len(real_examples)} real Mansur examples")
    
    # Group messages (30 per group)
    groups = []
    for i in range(0, len(messages), 30):
        groups.append(messages[i:i+30])
    
    print(f"�� Created {len(groups)} groups")
    
    # Score each group
    all_scores = {}
    
    for i, group in enumerate(groups):
        print(f"  Scoring group {i+1}/{len(groups)}...")
        
        prompt = build_scoring_prompt(group, real_examples)
        result = await generate_with_retry(client, prompt)
        
        if result:
            try:
                data = json.loads(result["text"])
                for score_entry in data["scores"]:
                    msg_id = score_entry["message_id"]
                    all_scores[msg_id] = score_entry["total"]
            except json.JSONDecodeError:
                print(f"  ⚠️  Group {i+1}: Invalid JSON, skipping")
    
    # Save
    output_file = output_dir / "all_scores.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_scores, f, ensure_ascii=False, indent=2)
    
    avg_score = sum(all_scores.values()) / len(all_scores) if all_scores else 0
    print(f"✅ Scored: {len(all_scores)} messages, average {avg_score:.1f}/10")
    
    return all_scores
```

---

## ЭТАП 5: FINAL SELECTION (локально)

### stages/stage5_selection.py

```python
"""Stage 5: Final Selection"""

import json
from pathlib import Path
from typing import List, Dict
from utils.similarity import calculate_similarity
from config import TARGET_TOTAL, DIVERSITY_THRESHOLD

def run(
    messages: List[Dict],
    scores: Dict[str, float],
    domain_map: dict,
    output_dir: Path
) -> List[Dict]:
    """Run Stage 5: Final Selection"""
    
    print("\n�� STAGE 5: Final Selection")
    print("-" * 60)
    
    # Add scores to messages
    for i, msg in enumerate(messages):
        msg_id = msg.get("aspect_id", f"msg_{i}")
        msg["score"] = scores.get(msg_id, 0)
        msg["id"] = f"msg_{i:04d}"
    
    # Sort by score
    messages.sort(key=lambda x: x["score"], reverse=True)
    
    # Calculate domain targets
    domain_targets = {}
    for domain in domain_map["domains"]:
        domain_targets[domain["id"]] = domain["target_count"]
    
    # Greedy selection with diversity
    selected = []
    selected_texts = []
    domain_counts = {d: 0 for d in domain_targets}
    
    for msg in messages:
        # Determine domain (from aspect_id or batch context)
        domain = None
        for d in domain_map["domains"]:
            for aspect in d["aspects"]:
                if aspect["id"] == msg.get("aspect_id"):
                    domain = d["id"]
                    break
            if domain:
                break
        
        if not domain:
            continue
        
        # Check quota
        if domain_counts[domain] >= domain_targets[domain]:
            continue
        
        # Check quality threshold
        if msg["score"] < 7:
            continue
        
        # Diversity check
        is_too_similar = False
        for selected_text in selected_texts:
            similarity = calculate_similarity(msg["text"], selected_text)
            if similarity > DIVERSITY_THRESHOLD:
                is_too_similar = True
                break
        
        if is_too_similar:
            continue
        
        # Accept
        selected.append(msg)
        selected_texts.append(msg["text"])
        domain_counts[domain] += 1
        
        if len(selected) >= TARGET_TOTAL:
            break
    
    # Save final dataset
    output_file = output_dir / "dataset_final.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(selected, f, ensure_ascii=False, indent=2)
    
    # Create bot-ready format
    emotional = [m for m in selected if m.get("aspect_id", "").startswith(("talents", "appearance", "strength", "hybrid"))]
    psychological = [m for m in selected if m.get("aspect_id", "").startswith(("CBT", "ACT", "behavioral"))]
    
    dataset = {
        "version": "1.0",
        "total_messages": len(selected),
        "pools": {
            "emotional": [
                {
                    "id": m["id"],
                    "text": m["text"],
                    "score": m["score"]
                }
                for m in emotional
            ],
            "psychological": [
                {
                    "id": m["id"],
                    "text": m["text"],
                    "score": m["score"]
                }
                for m in psychological
            ]
        }
    }
    
    output_file = output_dir / "dataset.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Selected: {len(selected)} messages")
    print(f"   Emotional: {len(emotional)}")
    print(f"   Psychological: {len(psychological)}")
    
    return selected
```

---

## ГЛАВНЫЙ СКРИПТ

### main.py

```python
"""Main CLI entry point"""

import asyncio
import sys
from pathlib import Path
from utils.api_client import OpusClient
from stages import (
    stage1_mapping,
    stage2_generation,
    stage3_filtering,
    stage4_scoring,
    stage5_selection
)

async def main():
    print("=" * 60)
    print("�� DATASET GENERATOR FOR TANYA'S MORNING BOT")
    print("=" * 60)
    print()
    
    # Initialize
    client = OpusClient()
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    try:
        # Stage 1: Domain Mapping
        domain_map = await stage1_mapping.run(client, output_dir)
        print()
        
        # Stage 2: Batch Generation
        raw_messages = await stage2_generation.run(client, domain_map, output_dir)
        print()
        
        # Stage 3: Automated Filtering
        filtered_messages = stage3_filtering.run(raw_messages, output_dir)
        print()
        
        # Check if we have enough messages
        if len(filtered_messages) < 365:
            print(f"⚠️  WARNING: Only {len(filtered_messages)} messages after filtering")
            print(f"   Need 365, deficit: {365 - len(filtered_messages)}")
            print(f"   Continuing with available messages...")
        
        # Stage 4: Comparative Scoring
        scores = await stage4_scoring.run(client, filtered_messages, output_dir)
        print()
        
        # Stage 5: Final Selection
        final_dataset = stage5_selection.run(
            filtered_messages,
            scores,
            domain_map,
            output_dir
        )
        print()
        
        # Summary
        print("=" * 60)
        print("�� DATASET CREATION COMPLETE!")
        print("=" * 60)
        print(f"Output: {output_dir / 'dataset.json'}")
        print(f"Total messages: {len(final_dataset)}")
        print()
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## ЗАПУСК

После создания всех файлов:

```bash
# Установи зависимости
pip install -r requirements.txt

# Запусти генератор
python main.py
```

Процесс займёт 30-60 минут. Результат будет в `output/dataset.json`.

---

## ВАЖНЫЕ ЗАМЕЧАНИЯ

1. **Checkpoints:** Если процесс прервётся, просто запусти `python main.py` снова — он продолжит с места остановки.

2. **Дефицит сообщений:** Если после фильтрации останется меньше 365 сообщений, скрипт продолжит работу с тем, что есть. Это нормально — лучше 300 качественных, чем 365 посредственных.

3. **Semantic similarity:** Если библиотека `sentence-transformers` не установится, скрипт автоматически переключится на Levenshtein distance.

4. **Ошибки API:** Retry logic обработает временные сбои. Если батч упадёт 3 раза подряд — он будет пропущен.

5. **Финальный файл:** `output/dataset.json` готов для использования в боте.

---

## КРИТЕРИИ УСПЕХА

✅ Скрипт завершился без критических ошибок  
✅ Создан файл `output/dataset.json`  
✅ В датасете минимум 300 сообщений  
✅ Средний score ≥ 7.0/10  
✅ Нет очевидных дубликатов  

Если всё выполнено — датасет готов! ��
```
