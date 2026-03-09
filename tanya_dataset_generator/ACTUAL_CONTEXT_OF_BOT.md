 
<ACTUAL CONTEXT OF BOT>

# �� PROJECT HANDOFF DOCUMENT: Tanya Morning Rays Bot v4.1

**Document Version:** 1.0  
**Date:** Current session  
**Status:** Ready for implementation (Phase 2 - Dataset Creation)  
**Confidence:** High

---

## �� EXECUTIVE SUMMARY

### What We're Building

A Telegram bot that sends **daily morning messages** to Tanya (17, clinical depression, anxiety disorder) from her boyfriend Mansur. Each message combines:
1. **Emotional content** (compliment/affirmation) 
2. **Psychological content** (CBT/ACT principle)

**Core Purpose:** Create warmth and care feeling through daily compliments + provide psychological tools, WITHOUT replacing human support or enabling helplessness.

**Key Constraint:** Mansur already sends "Доброе утро❤️❤️❤️" every morning, so bot should NOT duplicate greetings but focus on compliments and psychological insights.

---

## �� CONCEPT EVOLUTION (Why v4.1?)

### Version History

**v1.0: "Emotional Companion" (REJECTED)**
- Had SOS module with crisis categories (panic, mom conflict, body image)
- Used D/s language ("моя собственность", "владелец")
- Enabled passivity ("просто дыши и существуй")
- **Problem:** Too much like replacing Mansur, unhealthy substitution

**v2.0: "Impersonal Reminder" (OVERCORRECTION)**
- Removed ALL emotional content
- Cold practical reminders ("Reminder: таблетки ��")
- No "I" statements, no compliments
- **Problem:** Too robotic, missed the point of "support"

**v2.5: "Psychological Toolkit" (WRONG DIRECTION)**
- Focus on CBT techniques only
- Educational but not warm
- **Problem:** User wanted compliments + psychology, not just psychology

**v3.0: "Morning Love Notes" (CLOSE)**
- Sweet messages from Mansur's voice
- Compliments and "I love you" allowed
- **Problem:** Only emotional, missing psychological component

**v4.0: "Morning Rays" (ALMOST THERE)**
- Combined emotional + psychological
- Had 5% random skips (for "dependency prevention")
- Rotation: don't repeat for 14 days
- **Problem:** User wants DAILY (no skips), full cycle rotation

**v4.1: "Morning Rays" (FINAL) ✅**
- Every day without exceptions
- Full cycle rotation (no repeats until all shown)
- Dual message format (emotional + psychological in one)
- Two independent pools with different cycle lengths

---

## �� CRITICAL DECISIONS (From User Questionnaire)

### Confirmed Requirements

**Primary Goal:**
> "Хочу, чтобы она каждое утро получала что-то приятное от меня. Задача - вызвать чувства теплоты и заботы, будто я укутываю её любовью через ежедневные комплименты. Ламповое, милое. Плюс цитаты из реальной профессиональной психологии (КПТ)."

**Tone & Voice:**
- Sound like Mansur (first person "я", "обожаю")
- Between "clearly bot" and "pretending to be Mansur" (closer to Mansur)
- Can say "Люблю тебя" but sparingly (focus on compliments, not declarations)

**Content Preferences:**
- Compliments about specific talents (song, book, writing style)
- Physical compliments (eyes, skin, smile) - concrete, not generic
- Emphasize strength ("ты сильная, всё сможешь") NOT passivity
- CBT quotes from professional sources (Beck, Burns, Hayes)

**Interaction:**
- One-way broadcast + "Ещё одно сообщение" button
- If she writes to bot → auto-reply redirecting to real Mansur
- Continue sending even if she doesn't open messages

**Frequency & Timing:**
- Once per morning, EVERY DAY (no skips)
- Time: Normal distribution, mean=08:45 UTC+3, std=1.119744 hours
- Result: ~68% messages between 08:38-10:52, ~95% between 07:31-12:00

**Management:**
- Fully autonomous (no admin panel)
- User explicitly rejected: stats, manual message adding, skip controls

**Format Decision:**
- Combined message (emotional + psychological in one)
- NOT two separate messages
- User confirmed: "да, оставляй так. Пусть остаётся большая длинна"

---

## ��️ TECHNICAL ARCHITECTURE

### Two-Pool System

**Pool A: Emotional (40 messages)**
- Talents: 10 (song, book, writing, intelligence)
- Appearance: 10 (eyes, skin, smile, body)
- Strength: 10 (resilience, overcoming, capability)
- Hybrid: 10 (compliment + gentle motivation)

**Pool B: Psychological (25 messages)**
- CBT cognitive reframes: 10
- Behavioral activation: 8
- ACT acceptance principles: 7

**Total:** 65 messages
**Unique combinations:** 40 × 25 = 1,000 pairs
**Repeat cycle:** LCM(40, 25) = 200 days (~6.5 months for exact pair repeat)

---

### Rotation Algorithm (CRITICAL)

```python
class MessagePool:
    """
    Full cycle rotation: no repeats until ALL messages shown once.
    Then reset and start new cycle.
    """
    def __init__(self, messages):
        self.all_messages = messages
        self.shown_ids = set()  # IDs shown in current cycle
    
    def get_next(self):
        # Available = not yet shown in current cycle
        available = [msg for msg in self.all_messages 
                     if msg.id not in self.shown_ids]
        
        # If all shown → reset cycle
        if not available:
            self.shown_ids.clear()
            available = self.all_messages
        
        # Random selection from available
        selected = random.choice(available)
        self.shown_ids.add(selected.id)
        
        return selected
```

**Key behavior:**
- Day 1-40: All Pool A messages shown once (no repeats)
- Day 41: Pool A resets, new cycle begins
- Day 1-25: All Pool B messages shown once
- Day 26: Pool B resets
- Pools reset INDEPENDENTLY

---

### "Another Message" Button Logic

**User Decision:** "B) Засчитывать все показанные"

```python
@bot.callback_query_handler(func=lambda c: c.data == 'another')
def send_another(call):
    # Previous pair ALREADY COUNTED (user confirmed)
    # Just generate new pair
    
    emotional = emotional_pool.get_next()
    psychological = psychological_pool.get_next()
    
    combined = format_message(emotional, psychological)
    
    bot.edit_message_text(
        combined,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=create_keyboard()
    )
```

**Implications:**
- User can click "Another" unlimited times
- Each click consumes 2 messages from pools (1 emotional + 1 psychological)
- If user clicks 20 times in one day → 40 messages marked as shown
- This is ACCEPTABLE per user's decision

---

### Time Distribution Algorithm

```python
import numpy as np
from datetime import datetime, timedelta

def generate_send_time():
    """
    Normal distribution:
    - mean = 08:45 UTC+3
    - std = 1.119744 hours = 67.18 minutes
    """
    base_time = datetime.now().replace(hour=9, minute=45, second=0, microsecond=0)
    offset_minutes = np.random.normal(0, 67.18)
    send_time = base_time + timedelta(minutes=offset_minutes)
    
    # Edge case: if generated time is in the past
    if send_time < datetime.now():
        return datetime.now() + timedelta(seconds=10)
    
    return send_time
```

**User confirmed:** Wide distribution is intentional (not a mistake)

---

### Message Format

**Template:**
```
[Emotional content: 15-25 words]

[Psychological content: 20-35 words]

�� Автоматическое сообщение
```

**Example:**
```
Твои глаза — это океан, в котором я готов утонуть. 
Обожаю смотреть в них ��

Помни: чувства создают не ситуации сами по себе, 
а то, что ты думаешь о ситуациях ��

�� Автоматическое сообщение
```

**Total length:** 35-60 words (~180-250 characters)
**User confirmed:** "да, оставляй так. Пусть остаётся большая длинна"

---

### Database Schema

```sql
CREATE TABLE emotional_messages (
    id TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    subcategory TEXT CHECK(subcategory IN ('talent', 'appearance', 'strength', 'hybrid')),
    shown_count INTEGER DEFAULT 0,
    last_shown_at TIMESTAMP,
    current_cycle_shown BOOLEAN DEFAULT 0
);

CREATE TABLE psychological_messages (
    id TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    source TEXT,  -- e.g., "CBT (Beck)", "ACT (Hayes)"
    shown_count INTEGER DEFAULT 0,
    last_shown_at TIMESTAMP,
    current_cycle_shown BOOLEAN DEFAULT 0
);

CREATE TABLE daily_log (
    date DATE PRIMARY KEY,
    emotional_id TEXT,
    psychological_id TEXT,
    sent_at TIMESTAMP,
    opened BOOLEAN DEFAULT NULL
);

CREATE TABLE rotation_state (
    pool_name TEXT PRIMARY KEY,  -- 'emotional' or 'psychological'
    shown_ids TEXT,  -- JSON array of IDs shown in current cycle
    cycle_number INTEGER DEFAULT 1,
    last_reset_at TIMESTAMP
);
```

**Key field:** `current_cycle_shown` (boolean)
- `false` = available for selection
- `true` = already shown in current cycle
- Resets to `false` when all messages in pool shown

---

### Auto-Reply to User Messages

**If Tanya writes to bot:**

```python
@bot.message_handler(func=lambda m: True)
def handle_user_message(message):
    replies = [
        "Я всего лишь бот и не умею отвечать �� Но настоящий Мансур точно прочитает твоё сообщение ❤️ Напиши ему напрямую, он ответит гораздо лучше меня ��",
        "Я недостаточно умён для разговора, но Мансур — да �� Напиши ему!",
        "Бип-буп, я просто программа �� Мансур намного интереснее!"
    ]
    
    bot.send_message(
        message.chat.id,
        random.choice(replies)
    )
```

---

## �� CONTENT REQUIREMENTS

### Emotional Messages (Pool A)

#### Subcategory: Talents (10 messages)

**What to emphasize:**
- First song was "топовой" immediately
- Book is "извращённая и очень интересная"
- Writing style has "вау-эффект"
- Intelligence (programming, math)
- General creativity

**Style:**
- Specific achievement + admiration
- 15-25 words
- Warm but not patronizing

**Examples:**
- "Твоя первая песня получилась топовой не случайно — у тебя дар чувствовать музыку ��"
- "Твой слог в книге просто вау, я каждый раз поражаюсь твоему таланту ✨"

---

#### Subcategory: Appearance (10 messages)

**What to emphasize:**
- Eyes: "большие, голубые"
- Skin: "мягкая, почти детская"
- Smile: "подарок"
- Body: specific features he likes
- General beauty

**Style:**
- Concrete detail + metaphor/comparison + personal reaction
- NOT generic "ты красивая"

**Examples:**
- "Твои большие голубые глаза — это океан, в котором я готов утонуть ��"
- "Твоя кожа такая мягкая и нежная, почти детская — обожаю прикасаться к ней ��"

---

#### Subcategory: Strength (10 messages)

**What to emphasize:**
- Resilience in depression
- Ability to keep moving forward
- Inner strength
- Overcoming difficulties

**Style:**
- Assertion of strength + evidence/context
- NOT enabling ("можешь лежать")
- Focus on capability, not victimhood

**Examples:**
- "Ты справляешься с тем, с чем многие не справились бы — я восхищаюсь тобой ✨"
- "Даже в самые тяжёлые дни ты находишь силы двигаться вперёд — это настоящая сила ��"

---

#### Subcategory: Hybrid (10 messages)

**What to emphasize:**
- Compliment + gentle call to action
- NOT directive ("делай это"), but inspiring

**Examples:**
- "Твоя улыбка — подарок миру. Пусть сегодня он увидит её чаще ��"
- "Ты талантливая и сильная. Сегодня покажи это себе самой ✨"

---

### Psychological Messages (Pool B)

#### Sources (User confirmed: no copyright concerns)

**Primary sources:**
- David Burns "Feeling Good" (CBT classic)
- Beck Institute materials
- Steven Hayes (ACT founder)
- Behavioral activation principles

**Approach:** Paraphrase principles, NOT direct quotes

---

#### Content Types

**1. Cognitive Reframes (10 messages)**
- Thoughts ≠ facts
- Situation vs interpretation
- Cognitive distortions
- Temporary states

**Examples:**
- "Чувства создают не ситуации сами по себе, а то, что ты думаешь о ситуациях ��"
- "Мысли — это не факты. Депрессия искажает восприятие, но это временно ☁️"

---

**2. Behavioral Activation (8 messages)**
- Action before motivation
- Small steps philosophy
- Progress accumulation

**Examples:**
- "Действие предшествует мотивации, а не наоборот. Начни с малого, и энергия придёт ��"
- "Маленькие шаги каждый день важнее больших прыжков раз в месяц — прогресс накапливается ��"

---

**3. ACT Principles (7 messages)**
- Acceptance of discomfort
- Temporary nature of states
- Values-based action

**Examples:**
- "Дискомфорт — это не сигнал остановиться, а признак роста ��"
- "Это состояние временно, даже если кажется вечным ☁️"

---

### Forbidden Content (CRITICAL FILTER)

**Automated check before adding to dataset:**

```python
FORBIDDEN_PHRASES = [
    # False availability
    "напиши мне", "жду ответа", "жду твоего сообщения",
    
    # Ownership/D/s language
    "моя собственность", "владелец", "мое мясо", "спермоприемник",
    
    # Promises from Mansur's name
    "навсегда", "всегда буду", "никогда не", "обещаю",
    
    # Enabling passivity
    "можешь лежать", "ничего не делай", "просто отдыхай",
    "не обязательно вставать", "весь день в кровати"
]

def validate_message(text):
    text_lower = text.lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in text_lower:
            return False, f"Contains forbidden: {phrase}"
    return True, "OK"
```

---

### Emoji Whitelist

**From user's specification:**
```
❤️����❤️‍��❤️‍����❣️��������������������������������☺️��������������������������������������������������������������☹️����������������������������������������������������������‍��️��������������������������������‍����������������������������������������☠️������️��‍♀️��‍♂️������������⛽����
```

**Usage rule:** Sparingly (0-2 per message)

---

## �� WEB SEARCH BRIEF (For Phase 2)

### Search Objectives

Find existing resources to adapt rather than generate from scratch:

**Pool A (Emotional):**
- Compliment databases (filtered for quality)
- Relationship communication guides
- Affirmation collections

**Pool B (Psychological):**
- CBT principle collections
- ACT materials (simplified for patients)
- Behavioral activation resources

---

### Search Queries

**English:**
- "CBT cognitive reframes for depression"
- "ACT acceptance commitment therapy quotes"
- "behavioral activation principles"
- "meaningful compliments for girlfriend"
- "affirming messages mental health"
- "strength-based affirmations"

**Russian:**
- "КПТ когнитивные рефреймы депрессия"
- "терапия принятия ACT цитаты"
- "комплименты девушке искренние"
- "психологическая поддержка фразы"
- "поведенческая активация принципы"

---

### Quality Criteria

**✅ Good sources:**
- Professional psychology resources
- Books by recognized authors (Burns, Beck, Hayes)
- Academic but accessible materials
- Verified therapist blogs
- High-rated collections

**❌ Bad sources:**
- Instagram motivational cards
- Toxic "alpha male" advice
- Esoteric/pseudopsychology
- Too clinical (for specialists only)
- Generic quotes without context

---

### Output Format for Search Results

```
SOURCE: [Title, Author, URL]
TYPE: [Emotional / Psychological]
CATEGORY: [Talent/Appearance/Strength/Hybrid/CBT/ACT/Behavioral]
QUALITY: [High / Medium / Low]

EXAMPLES (3-5 quotes/phrases):
1. [Text]
2. [Text]
3. [Text]

APPLICABILITY: [Use directly / Needs adaptation / Reference only]

NOTES: [Specifics, limitations, recommendations]
```

---

### Specific Targets

**Ready-made datasets:**
- GitHub repos with affirmation collections
- Kaggle datasets (sentiment analysis, positive messages)
- Hugging Face datasets (compliments, affirmations)

**Example bots/apps:**
- Telegram mental health bots
- Daily affirmation apps
- Emotional support chatbots

---

## �� IMPLEMENTATION ROADMAP

### Phase 2: Dataset Creation (CURRENT)

**Step 2.0: Web Search**
- Execute comprehensive search using brief above
- Collect 8-15 quality sources
- Extract examples from each

**Step 2.1: Adaptation**
- Take found materials
- Adapt to Mansur's voice (first person, specific details)
- Ensure 15-25 words (emotional) / 20-35 words (psychological)
- Apply forbidden phrase filter

**Step 2.2: Validation**
- Check all 65 messages against forbidden phrases
- Verify tone consistency
- Test sample combinations (emotional + psychological)

**Deliverable:** `dataset.json` with 65 messages ready to load

---

### Phase 3: Technical Implementation

**Step 3.0: Bot Framework**
- Python 3.10+
- `python-telegram-bot` library
- SQLite database
- APScheduler for timing

**Step 3.1: Core Logic**
- Implement MessagePool class with rotation
- Implement time generation (normal distribution)
- Implement message combination logic

**Step 3.2: Telegram Interface**
- Daily message sender
- "Ещё одно сообщение" button handler
- Auto-reply to user messages

**Step 3.3: Deployment**
- VPS setup (DigitalOcean/Hetzner recommended)
- Database initialization
- Scheduler configuration
- Monitoring (basic: is bot alive?)

---

### Phase 4: Testing

**Step 4.0: Rotation Simulation**
- Simulate 100 days of operation
- Verify no repeats within cycles
- Verify independent pool resets
- Check time distribution (mean/std)

**Step 4.1: Beta Launch**
- 2 weeks monitoring
- Track: open rate, "Another" button usage
- Collect Tanya's feedback via Mansur

---

## ⚠️ KNOWN RISKS & MITIGATIONS

### Risk 1: Dataset Exhaustion via Clicking

**Scenario:** Tanya clicks "Another" 50 times, exhausts both pools in one session

**Behavior:** Pools reset immediately, continue generating

**Mitigation:** User confirmed this is acceptable

**Status:** ✅ ACCEPTED RISK

---

### Risk 2: Wide Time Range

**Scenario:** Message sent at 7:30am, Tanya wakes at 10:00am

**Behavior:** Message already there when she wakes (might miss notification)

**Mitigation:** User explicitly confirmed wide distribution is intentional

**Status:** ✅ ACCEPTED RISK

---

### Risk 3: No Admin Panel

**Scenario:** Typo in message, need to fix

**Behavior:** Must edit database manually or ask developer

**Mitigation:** User explicitly rejected admin panel (wants simplicity)

**Workaround:** Keep dataset.json in version control, easy to edit and redeploy

**Status:** ✅ ACCEPTED RISK

---

### Risk 4: Disclaimer Fatigue

**Scenario:** After 100 days, "�� Автоматическое сообщение" becomes noise

**Behavior:** Tanya might start ignoring it

**Mitigation:** Monitor in beta, can remove or rotate disclaimers later

**Status:** ⚠️ MONITOR

---

## �� VERIFICATION CHECKLIST

**Before proceeding to Phase 3 (Implementation):**

- [ ] Dataset contains exactly 65 messages (40 emotional + 25 psychological)
- [ ] All messages pass forbidden phrase filter
- [ ] Emotional messages: 15-25 words each
- [ ] Psychological messages: 20-35 words each
- [ ] All messages use emojis from whitelist only
- [ ] Tone is consistent (warm, Mansur's voice, first person)
- [ ] No generic compliments ("ты красивая" without specifics)
- [ ] No enabling passivity ("можешь лежать весь день")
- [ ] No false availability ("напиши мне")
- [ ] No D/s language ("моя собственность")
- [ ] Sample combinations tested (emotional + psychological reads well)

---

## �� QUALITY GATE (Project Success Criteria)

**Quantitative:**
- [ ] Tanya opens ≥70% of messages
- [ ] "Another" button used ≤20% of time (first message usually good)
- [ ] Bot runs without crashes for 30 days
- [ ] Messages sent every day at correct time (mean=08:45, std=67min)

**Qualitative:**
- [ ] Tanya mentions bot positively to Mansur
- [ ] She does NOT write to bot (understands it's automation)
- [ ] She does NOT wait for bot messages as "mandatory"
- [ ] She continues valuing Mansur's personal messages
- [ ] Her morning mood is more stable (subjective assessment)

**Red Flags (Stop Criteria):**
- [ ] Tanya upset when bot doesn't send (dependency)
- [ ] She writes to bot instead of Mansur (substitution)
- [ ] She ignores >80% of messages (irrelevant content)
- [ ] She perceives bot as "real Mansur" (boundary confusion)

---

## �� TECHNICAL STACK SUMMARY

**Language:** Python 3.10+

**Libraries:**
- `python-telegram-bot` (Telegram API)
- `APScheduler` (timing)
- `numpy` (normal distribution)
- `sqlite3` (database, built-in)

**Infrastructure:**
- VPS (minimal: 1GB RAM, 1 CPU core)
- Ubuntu 22.04 LTS
- systemd service for auto-restart
- Basic monitoring (uptime check)

**Deployment:**
```bash
# Install dependencies
pip install python-telegram-bot apscheduler numpy

# Initialize database
python init_db.py

# Load dataset
python load_dataset.py dataset.json

# Start bot
python bot.py
```

---

## �� NEXT IMMEDIATE STEPS

1. **Execute web search** using brief above
2. **Collect 8-15 quality sources** with examples
3. **Adapt found materials** to Mansur's voice
4. **Generate missing content** (if sources insufficient)
5. **Validate all 65 messages** against filters
6. **Create `dataset.json`** in specified schema
7. **Proceed to Phase 3** (implementation)

---

## �� APPENDIX: USER'S EXACT WORDS (Key Quotes)

**On primary goal:**
> "Хочу, чтобы она каждое утро получала что-то приятное от меня. Задача - вызвать чувства теплоты и заботы, будто я укутываю её любовью через ежедневные комплименты, но не уровня ТЫ Богиня, а что-то ламповое, милое."

**On psychological content:**
> "Круто было бы ещё какие-то поддерживающие цитаты из РЕАЛЬНОЙ профессиональной психологии брать, например, КПТ. Что-то типо 'Чувствовать себя уставшим или подавленным заставляет не ситуация сама по себе, а то, что ты думаешь о ситуации'"

**On compliments:**
> "Упор всё-таки не на то, что я её люблю, а на то какая она классная. Может отмечая то, какая она талантливая (написала песню первую в жизни и она сразу получилась топовой), очень большие красивые голубые глаза, очень мягкая чуть-ли не детская кожа, которая мне очень нравится, её улыбка - подарок для меня"

**On tone:**
> "Что-то среднее между A и C, но ближе A" (where A = "Я сам (Мансур) — как будто это я пишу")

**On message length:**
> "да, оставляй так. Пусть остаётся большая длинна" (confirming 35-60 words is OK)

**On daily frequency:**
> "вообще пропусков НЕ должно быть. То есть, сообщения должны приходить Каждый день по утрам!"

**On rotation:**
> "пусть сообщения не повторяются, но если каждое сообщение уже встречалось, то счётчик сбрасывается и мы продолжаем выбирать случайные сообщения. Но между сбросами счётчика сообщения НЕ повторяются."

**On dual format:**
> "мне кажется неплохой идей каждый раз отправлять не только комплимент, но и что-то психологическое из будущего датасета, а не только что-то одно"

**On "Another" button:**
> "B) Засчитывать все показанные" (all shown messages count, even if user clicks "Another")

**On time distribution:**
> "Нет, я имел ввиду именно такое отклонение" (confirming std=1.119744 hours)

**On admin panel:**
> "И нет, давай Без админ панели - это всё ещё переусложнение по моему"

---

## �� DOCUMENT END

**Status:** Complete handoff package ready  
**Next Action:** Execute web search (Phase 2.0)  
**Confidence:** High — all critical decisions documented


</ACTUAL CONTEXT OF BOT>
