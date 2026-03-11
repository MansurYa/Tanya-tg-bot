# Чистая переустановка бота на сервере

## Шаг 1: Остановить все процессы
```bash
# Убить все экземпляры бота
pkill -9 -f "python -m src.bot"

# Проверить, что все убиты
ps aux | grep "python -m src.bot"
```

## Шаг 2: Обновить код
```bash
cd /root/Tanya-tg-bot
git pull origin main
```

## Шаг 3: Исправить базу данных
```bash
# Это отключит старую систему уведомлений
python fix_duplicate_notifications.py
```

## Шаг 4: Запустить бота
```bash
# Запустить в фоне
nohup python -m src.bot > bot.log 2>&1 &

# Подождать 3 секунды
sleep 3

# Проверить, что запустился
ps aux | grep "python -m src.bot"
```

## Шаг 5: Проверить логи
```bash
# Смотреть логи в реальном времени
tail -f bot.log

# Если всё ок, увидишь:
# "🤖 Бот запущен!"
# "Message pools loaded: 73 compliments, 121 psychology"
```

## Готово!
Теперь бот будет отправлять правильные сообщения из датасета.
