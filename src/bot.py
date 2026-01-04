# ============ Импорты ============

# Стандартные библиотеки
import json
import logging
import os
import random
from datetime import date, datetime, time, timedelta
from typing import TYPE_CHECKING, Any, Dict, List, Optional

# Сторонние библиотеки
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from openai import AsyncOpenAI
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    CallbackContext,
    MessageHandler,
    filters,
)

# Модули текущего проекта
from . import database
from .database import create_user, get_user, get_users_for_notification, update_user

if TYPE_CHECKING:
    from telegram.ext import Application

# ============ Логирование и окружение ============
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============ Загрузка Конфига ============
try:
    with open("config.json", "r", encoding="utf-8") as f:
        CONFIG = json.load(f)
except FileNotFoundError:
    logger.critical("КРИТИЧЕСКАЯ ОШИБКА: config.json не найден! Бот не может запуститься.")
    exit()

# ============ Клиент OpenRouter (Асинхронный) ============
client = AsyncOpenAI(
    api_key=CONFIG["settings"].get("openrouter_api_key"),
    base_url="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "https://github.com/mansur-zainullin/tanya-tg-bot",
        "X-Title": "Tanya Digital Avatar",
    },
)

# ============ Константы ============
QUEST_Q1, QUEST_Q2, COMPLETED = range(3)
UNLOCK_SEQUENCE = CONFIG["settings"]["unlock_sequence"]


# ============ Вспомогательные функции ============

def get_current_gift(user: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Получает текущий подарок для пользователя на основе его прогресса в квесте.
    :param user: Словарь с данными пользователя из базы данных.
    :return: Словарь с данными о текущем подарке или None, если все подарки открыты.
    """
    if user["current_gift_idx"] >= len(UNLOCK_SEQUENCE):
        return None
    gift_id = UNLOCK_SEQUENCE[user["current_gift_idx"]]
    return CONFIG["quests"][str(gift_id)]


def get_current_question(user: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Получает текущий вопрос для пользователя.
    :param user: Словарь с данными пользователя.
    :return: Словарь с данными о текущем вопросе или None, если подарок не найден.
    """
    gift = get_current_gift(user)
    if not gift:
        return None
    q_idx = user["current_question"] - 1
    return gift["questions"][q_idx]


async def validate_answer(question: Dict[str, Any], user_input: str) -> bool:
    """
    Проверяет ответ пользователя с помощью LLM и резервного механизма.
    :param question: Словарь с данными вопроса.
    :param user_input: Текст ответа, предоставленный пользователем.
    :return: True, если ответ правильный, иначе False.
    """
    prompt = f"""
Ты проверяешь ответ в квесте. Ответь ТОЛЬКО "ДА" или "НЕТ".

ВОПРОС: {question['text']}
ПРАВИЛЬНЫЕ ОТВЕТЫ: {question['valid_answers']}
ИНСТРУКЦИЯ: {question['llm_validation_instruction']}

ОТВЕТ ПОЛЬЗОВАТЕЛЯ: {user_input}

Засчитывай синонимы, опечатки, неполные ответы если смысл верный.
Ответь одним словом: ДА или НЕТ"""

    try:
        llm_config = CONFIG["settings"].get("llm", {})

        model = llm_config.get("validation_model", "google/gemini-flash-1.5")
        temperature = llm_config.get("validation_temperature", 0.0)
        max_tokens = llm_config.get("max_tokens", 10)

        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature
        )
        answer = response.choices[0].message.content.strip().upper()
        return "ДА" in answer
    except Exception as e:
        logger.error(f"Ошибка при валидации через LLM: {e}. Использую fallback.")
        # Fallback: простое сравнение
        user_lower = user_input.lower().strip()
        for valid in question['valid_answers']:
            if valid.lower() in user_lower or user_lower in valid.lower():
                return True
        return False


# ============ Handlers Квеста (FSM) ============

async def start(update: Update, context: CallbackContext) -> int:
    """
    Начинает или перезапускает квест для пользователя.
    Это входная точка для ConversationHandler.
    :param update: Объект Update от Telegram.
    :param context: Контекст бота.
    :return: Следующее состояние FSM (QUEST_Q1 или COMPLETED).
    """
    user_id = update.effective_user.id
    user = get_user(user_id)

    initial_skips = CONFIG["settings"].get("allowed_skips", 3)

    if not user:
        user = create_user(user_id, initial_skips=initial_skips)
        await update.message.reply_text("Привет! Начинаем новогодний квест... 🎄")
    elif user["state"] == "COMPLETED":
        await show_main_menu(update, context)
        return COMPLETED
    else:
        # Сброс прогресса для существующего пользователя
        update_user(
            user_id,
            state='QUEST',
            current_gift_idx=0,
            current_question=1,
            unlocked_gifts=[],
            skips_left=initial_skips
        )
        user = get_user(user_id)  # Перезагружаем данные пользователя
        await update.message.reply_text("Прогресс квеста сброшен. Начинаем заново! ✨")

    question = get_current_question(user)

    total_gifts = len(UNLOCK_SEQUENCE)
    current_gift_num = user["current_gift_idx"] + 1

    keyboard = None
    if question.get("user_hint"):
        buttons = [[InlineKeyboardButton("💡 Взять подсказку", callback_data="get_hint")]]
        keyboard = InlineKeyboardMarkup(buttons)

    await update.message.reply_text(
        f"Подарок {current_gift_num}/{total_gifts}\n\n"
        f"❓ Вопрос: {question['text']}",
        reply_markup=keyboard
    )

    return QUEST_Q1


async def handle_answer_q1(update: Update, context: CallbackContext) -> int:
    """
    Обрабатывает текстовый ответ пользователя на первый вопрос подарка.
    :param update: Объект Update от Telegram.
    :param context: Контекст бота.
    :return: Следующее состояние FSM (QUEST_Q2 или QUEST_Q1).
    """
    user_id = update.effective_user.id
    user = get_user(user_id)
    user_input = update.message.text

    question = get_current_question(user)
    is_correct = await validate_answer(question, user_input)

    if is_correct:
        update_user(user_id, current_question=2)
        user = get_user(user_id)  # Обновляем данные
        next_q = get_current_question(user)

        keyboard = None
        if next_q.get("user_hint"):
            buttons = [[InlineKeyboardButton("💡 Взять подсказку", callback_data="get_hint")]]
            keyboard = InlineKeyboardMarkup(buttons)

        await update.message.reply_text(
            f"✅ Верно!\n\n"
            f"❓ Вопрос 2: {next_q['text']}",
            reply_markup=keyboard
        )
        return QUEST_Q2
    else:
        await update.message.reply_text(
            f"❌ Неправильно, попробуй ещё раз.\n\n"
            f"Осталось пропусков: {user['skips_left']}\n"
            f"Используй /skip чтобы пропустить."
        )
        return QUEST_Q1


async def handle_answer_q2(update: Update, context: CallbackContext) -> int:
    """
    Обрабатывает текстовый ответ пользователя на второй вопрос подарка.
    :param update: Объект Update от Telegram.
    :param context: Контекст бота.
    :return: Следующее состояние FSM.
    """
    user_id = update.effective_user.id
    user_input = update.message.text

    question = get_current_question(get_user(user_id))
    is_correct = await validate_answer(question, user_input)

    if is_correct:
        return await unlock_gift_and_proceed(update, user_id)
    else:
        user = get_user(user_id)
        await update.message.reply_text(
            f"❌ Неправильно, попробуй ещё раз.\n\n"
            f"Осталось пропусков: {user['skips_left']}"
        )
        return QUEST_Q2


async def skip(update: Update, context: CallbackContext) -> int:
    """
    Обрабатывает команду /skip для пропуска текущего вопроса.
    :param update: Объект Update от Telegram.
    :param context: Контекст бота.
    :return: Следующее состояние FSM.
    """
    user_id = update.effective_user.id
    user = get_user(user_id)

    if user["skips_left"] <= 0:
        await update.message.reply_text("😢 Пропуски закончились!")
        return user["current_question"]  # Остаемся в том же состоянии

    new_skips = user["skips_left"] - 1
    update_user(user_id, skips_left=new_skips)

    if user["current_question"] == 1:
        update_user(user_id, current_question=2)
        user = get_user(user_id)
        next_q = get_current_question(user)

        keyboard = None
        if next_q.get("user_hint"):
            buttons = [[InlineKeyboardButton("💡 Взять подсказку", callback_data="get_hint")]]
            keyboard = InlineKeyboardMarkup(buttons)

        await update.message.reply_text(
            f"⏭ Вопрос пропущен! Осталось пропусков: {new_skips}\n\n"
            f"❓ Вопрос 2:\n{next_q['text']}",
            reply_markup=keyboard
        )
        return QUEST_Q2
    else:
        return await unlock_gift_and_proceed(update, user_id, skipped=True)


async def handle_get_hint(update: Update, context: CallbackContext):
    """
    Обрабатывает нажатие на inline-кнопку для получения подсказки.
    :param update: Объект Update от Telegram.
    :param context: Контекст бота.
    """
    query = update.callback_query
    await query.answer()

    user = get_user(query.from_user.id)
    if not user:
        return

    question = get_current_question(user)
    if not question:
        return

    hint_text = question.get("user_hint")

    if hint_text:
        new_text = f"{query.message.text}\n\n💡 Подсказка: {hint_text}"
        await query.edit_message_text(text=new_text, reply_markup=None)
    else:
        await query.edit_message_text(text=f"{query.message.text}\n\n(К этому вопросу подсказки нет)",
                                      reply_markup=None)


async def unlock_gift_and_proceed(update: Update, user_id: int, skipped: bool = False) -> int:
    """
    "Открывает" подарок, обновляет прогресс пользователя и переходит к следующему вопросу.
    :param update: Объект Update от Telegram.
    :param user_id: ID пользователя.
    :param skipped: True, если вопрос был пропущен.
    :return: Следующее состояние FSM.
    """
    user = get_user(user_id)

    unlocked_gifts_list = user["unlocked_gifts"] + [UNLOCK_SEQUENCE[user["current_gift_idx"]]]
    next_gift_idx = user["current_gift_idx"] + 1
    total_gifts = len(UNLOCK_SEQUENCE)

    update_user(user_id,
                unlocked_gifts=unlocked_gifts_list,
                current_gift_idx=next_gift_idx,
                current_question=1
                )

    unlock_status_message = "✅ Верно!"
    if skipped:
        unlock_status_message = "⏭ Вопрос пропущен!"

    if next_gift_idx >= total_gifts:
        update_user(user_id, state="COMPLETED")
        await update.message.reply_text(
            f"{unlock_status_message}\n\n"
            f"Прогресс: {len(unlocked_gifts_list)}/{total_gifts}\n\n"
            "🎉🎉🎉 ПОЗДРАВЛЯЮ! ВСЕ 12 ПОДАРКОВ ОТКРЫТЫ! 🎉🎉🎉\n\n"
            "Теперь тебе доступно меню поддержки и другие секреты. 💕"
        )
        await show_main_menu(update, None)
        return COMPLETED
    else:
        user = get_user(user_id)
        next_q = get_current_question(user)

        keyboard = None
        if next_q.get("user_hint"):
            buttons = [[InlineKeyboardButton("💡 Взять подсказку", callback_data="get_hint")]]
            keyboard = InlineKeyboardMarkup(buttons)

        await update.message.reply_text(
            f"{unlock_status_message}\n\n"
            f"Прогресс: {len(unlocked_gifts_list)}/{total_gifts}\n\n"
            f"❓ Вопрос: {next_q['text']}",
            reply_markup=keyboard
        )
        return QUEST_Q1


# ============ Handlers Пост-Квеста ============

async def show_main_menu(update: Update, context: CallbackContext):
    """
    Показывает главное меню с кнопками поддержки после завершения квеста.
    :param update: Объект Update от Telegram.
    :param context: Контекст бота.
    """
    keyboard = [
        [InlineKeyboardButton("😢 Мне грустно", callback_data="support_sad")],
        [InlineKeyboardButton("🤗 Хочу на ручки", callback_data="support_hug")],
        [InlineKeyboardButton("💕 Напомни, что я твоя", callback_data="support_yours")],
    ]

    message_text = "🏠 Главное меню\n\nВыбери, что тебе нужно:"

    if update.callback_query:
        await update.callback_query.edit_message_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_support_callback(update: Update, context: CallbackContext):
    """
    Обрабатывает нажатия на кнопки в меню поддержки.
    :param update: Объект Update от Telegram.
    :param context: Контекст бота.
    """
    query = update.callback_query
    await query.answer()

    responses = {
        "support_sad": [
            "Иди сюда, моя хорошая. Всё будет хорошо 🤍",
            "Я рядом. Ты справишься, я в тебя верю 💪",
            "Помни, что любая грусть временна. А я с тобой навсегда.",
        ],
        "support_hug": [
            "*крепко-крепко обнимает* Ты моя самая сладкая девочка 🫂",
            "Представь, что я рядом, целую тебя в макушку и глажу по голове 💕",
            "Хочу сейчас же оказаться рядом и заключить тебя в объятия.",
        ],
        "support_yours": [
            "Ты моя собственность. Только моя. Не забывай об этом никогда. 🔐",
            "Ты принадлежишь мне. Полностью. Без остатка. И я обожаю это. ❤️‍🔥",
            "Каждая твоя мысль, каждое движение — всё принадлежит мне. Ты — моя.",
        ],
    }

    category = query.data
    message = random.choice(responses.get(category, ["💕"]))

    keyboard = [[InlineKeyboardButton("⬅️ Назад в меню", callback_data="main_menu")]]

    if category == "main_menu":
        await show_main_menu(update, context)
    else:
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_webapp_data(update: Update, context: CallbackContext):
    """
    Обрабатывает данные, полученные от Telegram Mini App.
    :param update: Объект Update от Telegram.
    :param context: Контекст бота.
    """
    try:
        data = json.loads(update.message.web_app_data.data)
        logger.info(f"Получены данные из Mini App: {data}")

        if data.get("action") == "feed" and "score" in data:
            await update.message.reply_text(f"😺 Крем доволен! Ты покормила его {data['score']} раз. Спасибо!")
        else:
            await update.message.reply_text("Получил данные от твоего котика! 😺")
    except json.JSONDecodeError:
        logger.error(f"Ошибка декодирования JSON из Web App: {update.message.web_app_data.data}")
        await update.message.reply_text("Произошла ошибка при обработке данных от веб-приложения.")


# ============ Планировщик (APScheduler) ============

scheduler = AsyncIOScheduler(timezone="Europe/Moscow")


def get_random_morning_time() -> time:
    """
    Генерирует случайное время для утреннего уведомления.
    Использует Гауссово распределение со средним в 11:00 и стандартным отклонением 90 минут.
    :return: Объект time.
    """
    mean_minutes = 11 * 60
    std_minutes = 90

    random_minutes = random.gauss(mean_minutes, std_minutes)
    random_minutes = max(8 * 60, min(14 * 60, random_minutes))

    hours = int(random_minutes // 60)
    minutes = int(random_minutes % 60)

    return time(hour=hours, minute=minutes)


async def send_single_notification(bot, telegram_id: int):
    """
    Отправляет одно утреннее уведомление конкретному пользователю.
    :param bot: Экземпляр бота.
    :param telegram_id: ID пользователя в Telegram.
    """
    messages = CONFIG.get("notifications", {}).get("morning_messages", [
        "Доброе утро, моя хорошая ☀️",
        "Привет, сладкая. Как спалось? 🌙",
        "Проснулась? Я уже думаю о тебе 💭",
    ])

    try:
        await bot.send_message(telegram_id, random.choice(messages))
        update_user(telegram_id, last_notification_date=date.today().isoformat())
        logger.info(f"Утреннее уведомление отправлено пользователю {telegram_id}")
    except Exception as e:
        logger.error(f"Не удалось отправить уведомление {telegram_id}: {e}")


async def schedule_daily_notifications(bot):
    """
    Планирует ежедневную отправку уведомлений всем подходящим пользователям.
    :param bot: Экземпляр бота.
    """
    today_str = date.today().isoformat()
    users = get_users_for_notification()

    for user in users:
        user_id = user['telegram_id']
        if user.get('last_notification_date') != today_str:
            send_time = get_random_morning_time()
            run_date = datetime.combine(date.today(), send_time)

            scheduler.add_job(
                send_single_notification,
                'date',
                run_date=run_date,
                args=[bot, user_id],
                id=f"notif_{user_id}_{today_str}",
                replace_existing=True
            )
            logger.info(f"Запланировано уведомление для {user_id} на {run_date.strftime('%H:%M:%S')}")


async def setup_scheduler(app: Application):
    """
    Настраивает и запускает планировщик задач.
    :param app: Экземпляр `telegram.ext.Application`.
    """
    scheduler.add_job(
        schedule_daily_notifications,
        'cron',
        hour=4,
        minute=0,
        args=[app.bot]
    )
    scheduler.start()
    logger.info("Планировщик запущен.")


# ============ Главная функция ============

def main():
    """Основная функция, настраивающая и запускающая бота."""
    database.init_db()

    token = CONFIG["settings"].get("bot_token")
    if not token or token == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        logger.critical("Критическая ошибка: bot_token не найден в config.json! Укажите токен и перезапустите бота.")
        return

    app = Application.builder().token(token).post_init(setup_scheduler).concurrent_updates(False).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            QUEST_Q1: [
                CallbackQueryHandler(handle_get_hint, pattern="^get_hint$"),
                CommandHandler("skip", skip),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer_q1),
            ],
            QUEST_Q2: [
                CallbackQueryHandler(handle_get_hint, pattern="^get_hint$"),
                CommandHandler("skip", skip),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer_q2),
            ],
            COMPLETED: [
                CallbackQueryHandler(handle_support_callback, pattern="^support_|^main_menu$"),
                MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data),
                CommandHandler("start", start),  # Чтобы можно было снова вызвать меню
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)

    logger.info("🤖 Бот запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()