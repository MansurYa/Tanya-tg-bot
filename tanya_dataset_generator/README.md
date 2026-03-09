# Dataset Generator for Tanya's Morning Bot

Автоматический генератор датасета из 365 персонализированных утренних сообщений.

## Быстрый старт

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск генератора
python main.py
```

## Архитектура

Генератор работает в 5 этапов:

1. **Domain Mapping** (1 API запрос) - анализ контекста и создание карты доменов
2. **Batch Generation** (80 запросов) - генерация ~640 сообщений батчами
3. **Automated Filtering** (локально) - фильтрация по запрещенным фразам, длине, эмодзи
4. **Comparative Scoring** (10 запросов) - оценка качества через сравнение с реальными сообщениями
5. **Final Selection** (локально) - выбор топ-365 с учетом diversity

## Структура проекта

```
tanya_dataset_generator/
├── main.py                 # CLI entry point
├── config.py              # Конфигурация (API, пороги, константы)
├── requirements.txt       # Зависимости
├── stages/               # Модули этапов генерации
│   ├── stage1_mapping.py
│   ├── stage2_generation.py
│   ├── stage3_filtering.py
│   ├── stage4_scoring.py
│   └── stage5_selection.py
├── utils/                # Утилиты
│   ├── api_client.py     # Opus 4.6 клиент с retry
│   ├── validators.py     # Валидация сообщений
│   └── similarity.py     # Детекция дубликатов
├── data/                 # Входные данные
│   ├── TANYA_AND_MANSUR_CONTEXT.md
│   ├── DEEP_RESEARCH.md
│   └── ACTUAL_CONTEXT_OF_BOT.md
└── output/               # Результаты
    ├── checkpoints/      # Инкрементальные сохранения
    ├── domain_map.json
    ├── raw_messages_all.json
    ├── filtered_messages.json
    ├── all_scores.json
    └── dataset.json      # ФИНАЛЬНЫЙ РЕЗУЛЬТАТ
```

## Особенности

- **Checkpoints**: При прерывании процесса можно продолжить с места остановки
- **Retry logic**: Автоматические повторы при ошибках API
- **Semantic similarity**: Умная детекция дубликатов (с fallback на Levenshtein)
- **Budget control**: Строгий контроль расхода API запросов (макс. 100)

## Результат

Файл `output/dataset.json` содержит:
- 365 высококачественных сообщений
- Разделение на emotional (240) и psychological (125) пулы
- Каждое сообщение с ID и score качества

Формат готов для прямого использования в боте.

## Требования

- Python 3.8+
- Доступ к Opus 4.6 API
- ~30-60 минут времени выполнения
