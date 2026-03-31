import json
import logging
import os
import random
import numpy as np
from datetime import date, datetime, time, timedelta, timezone as dt_timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

# Moscow timezone
moscow_tz = dt_timezone(timedelta(hours=3))

# Morning message time settings (normal distribution)
# Source: derived from user behavior analysis
MORNING_MESSAGE_MEAN_MINUTES = 8 * 60 + 45  # 08:45 MSK (525 min from midnight)
MORNING_MESSAGE_STD_MINUTES = 67.18
MORNING_MESSAGE_MIN_MINUTES = 7.5 * 60      # 07:30 (clamped)
MORNING_MESSAGE_MAX_MINUTES = 12 * 60       # 12:00 (clamped)

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
from . import database
from .database import create_user, get_user, update_user
from .message_pool import MessagePool, load_compliments, load_psychology, format_combined_message

if TYPE_CHECKING:
    from telegram.ext import Application

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)
logger = logging.getLogger(__name__)

try:
    with open("config.json", "r", encoding="utf-8") as f:
        CONFIG = json.load(f)
except FileNotFoundError:
    logger.critical("КРИТИЧЕСКАЯ ОШИБКА: config.json не найден! Бот не может запуститься.")
    exit()

client = AsyncOpenAI(
    api_key=CONFIG["settings"].get("openrouter_api_key"),
    base_url="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "https://github.com/mansur-zainullin/tanya-tg-bot",
        "X-Title": "Tanya Digital Avatar",
    },
)

QUEST_Q1, QUEST_Q2, COMPLETED = range(3)
UNLOCK_SEQUENCE = CONFIG["settings"]["unlock_sequence"]

# Initialize message pools
try:
    emotional_pool = MessagePool("emotional", load_compliments())
    psychological_pool = MessagePool("psychological", load_psychology())
    logger.info(f"Message pools loaded: {emotional_pool.total_count} compliments, {psychological_pool.total_count} psychology")
except Exception as e:
    logger.error(f"Failed to load message pools: {e}")
    emotional_pool = None
    psychological_pool = None


def get_current_gift(user: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Получает текущий подарок для пользователя."""
    if user["current_gift_idx"] >= len(UNLOCK_SEQUENCE):
        return None
    gift_id = UNLOCK_SEQUENCE[user["current_gift_idx"]]
    return CONFIG["quests"][str(gift_id)]


def get_current_question(user: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Получает текущий вопрос для пользователя."""
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


async def start(update: Update, context: CallbackContext) -> int:
    """
    Начинает или перезапускает квест. Входная точка ConversationHandler.
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
    """Обрабатывает ответ на первый вопрос."""
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
    """Обрабатывает ответ на второй вопрос."""
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
    """Обрабатывает команду /skip."""
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
    """Обрабатывает нажатие кнопки 'Взять подсказку'."""
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
        new_text = f"{query.message.text}\n\n(К этому вопросу подсказки нет)"
        await query.edit_message_text(text=new_text, reply_markup=None)


async def unlock_gift_and_proceed(update: Update, user_id: int, skipped: bool = False) -> int:
    """
    Открывает подарок, обновляет прогресс и переходит к следующему вопросу.
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

        # Activate morning messages
        await activate_morning_messages(update, user_id)

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


async def show_main_menu(update: Update, context: CallbackContext):
    """Показывает главное меню с кнопками поддержки."""
    keyboard = [
        [InlineKeyboardButton("😢 Мне грустно", callback_data="support_sad")],
        [InlineKeyboardButton("🤗 Хочу на ручки", callback_data="support_hug")],
        [InlineKeyboardButton("💌 Утреннее сообщение", callback_data="another_message")],
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
    """Обрабатывает нажатия на кнопки в меню поддержки."""
    query = update.callback_query
    await query.answer()

    responses = {
        "support_sad": [
            "Иди сюда, моя хорошая. Я знаю, как тебе сейчас тяжело, и я рядом. Ты не одна в этой грусти 🫂❤️",
            "Я рядом, солнышко. Сейчас тебе очень тяжело, и это нормально - чувствовать грусть. Ты уже столько раз справлялась, и я верю, что и сейчас сможешь 💕",
            "Эта грусть не будет длиться вечно, даже если сейчас так кажется. Я мысленно обнимаю тебя и держу за руку, пока ты проходишь через это ❤️",
            "Моя девочка, представь, что я укутываю тебя в самое мягкое одеяло, где можно просто быть грустной без вины и объяснений. Ты имеешь право чувствовать то, что чувствуешь 💗😌",
            "Котёнок, знаю, ты устала от этой грусти. Сегодня не нужно с ней бороться - просто позволь ей быть, как облаку на небе. А я мысленно сижу рядом и держу тебя за руку 💕",
            "Солнышко, когда грусть накрывает тебя тяжёлой волной, я - твой якорь. Закрой глаза, почувствуй моё присутствие и держись за меня мысленно. Мы вместе переждём этот шторм ⚓💕",
            "Малышка, ты так долго держишься, и я вижу, как это тяжело. Сегодня можно просто выдохнуть, опуститься на пол и позволить себе быть слабой. Я мысленно обнимаю тебя и говорю, что ты молодец ❤️🤗",
            "Девочка моя, ты не обязана быть счастливой каждый день. Грустить - это нормально и человечно. Закрой глаза и представь, что моя любовь - это тёплая ванна, в которую ты погружаешься прямо сейчас 💗",
            "Солнышко, твой мозг сейчас показывает тебе искажённую картинку из-за химии депрессии. Но я вижу правду - ты сильная, любимая и точно не одна. Я держу тебя за руку через это 💕",
            "Котёнок, прямо сейчас, в эту секунду, ты в безопасности. Представь, что моя любовь окружает тебя тёплым коконом, где можно спрятаться от всего мира, закрыть глаза и просто дышать 💖😌",
        ],
        "support_hug": [
            "Иди сюда, моя сладкая девочка. Я крепко-крепко обнимаю тебя, прижимаю к себе и глажу по голове. Чувствуешь моё тепло? Ты в безопасности 🤗❤️",
            "Закрой глаза, солнышко. Представь, что я рядом - целую тебя в макушку, глажу по волосам и шепчу на ухо, какая ты у меня хорошая 💋❤️",
            "Малышка, представь, что я прямо сейчас беру тебя на руки, усаживаю к себе на колени и укутываю в самое тёплое одеяло. Ты чувствуешь, как я дышу? 💗🥰",
            "Котёнок, представь, что я глажу тебя по спине медленными, успокаивающими кругами, целую в висок и обнимаю так, что ты чувствуешь приятную тяжесть моих рук 💕",
            "Девочка моя, иди ко мне. Я прижимаю тебя к себе так близко, что ты чувствуешь моё тепло, запах и биение моего сердца. Расслабься и растай в моих объятиях 💓❤️",
            "Солнышко, мои руки - это твоё безопасное место. Иди сюда, я беру тебя на руки, прижимаю к тёплой груди и медленно качаю. Ты можешь просто быть, ничего не делая 💕😌",
            "Малышка, иди ко мне и ложись всем своим весом - я выдержу тебя любую. Укутываю тебя в кокон из своих рук, где тепло, тихо и абсолютно безопасно 💖🫶",
            "Котёнок, закрой глаза и представь, что я строю вокруг тебя самое мягкое гнездо из одеял и своих объятий. Ты в самом центре, в самом защищённом месте на свете 🪺💕",
            "Девочка моя, иди сюда. Я беру твоё лицо в ладони, смотрю в твои красивые голубые глаза, целую в лоб и крепко прижимаю к себе. Дышим вместе - спокойно и медленно 💗🥰",
            "Солнышко, прижмись ко мне ближе. Слышишь, как бьётся моё сердце? Это для тебя. Положи голову мне на грудь и просто слушай этот спокойный, ровный ритм 💓💕",
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
    """Обрабатывает данные от Telegram Mini App."""
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


async def restore_state(update: Update, context: CallbackContext) -> int:
    """
    Восстанавливает состояние пользователя из БД при перезапуске бота.
    """
    user_id = update.effective_user.id
    user = get_user(user_id)

    if not user:
        return await start(update, context)

    if user["state"] == "COMPLETED":
        await show_main_menu(update, context)
        return COMPLETED

    q_idx = user.get("current_question", 1)
    if q_idx == 1:
        return await handle_answer_q1(update, context)
    elif q_idx == 2:
        return await handle_answer_q2(update, context)
    
    return await start(update, context)


scheduler = AsyncIOScheduler(timezone="Europe/Moscow")


async def activate_morning_messages(update: Update, user_id: int):
    """Activate morning messages and send first one immediately."""
    if not emotional_pool or not psychological_pool:
        logger.error("Cannot activate morning messages: pools not loaded")
        return

    # Enable morning messages and disable old notification system
    update_user(user_id, morning_messages_enabled=1, notifications_enabled=0)
    logger.info(f"Morning messages activated for user {user_id} (old notifications disabled)")

    # Send first message immediately
    await send_morning_message(update.get_bot(), user_id, is_first=True)


async def _send_combined_message(
    bot,
    user_id: int,
    update_last_message_date: bool = False
) -> bool:
    """
    Send combined morning message to user.

    Args:
        bot: Telegram bot instance
        user_id: User's Telegram ID
        update_last_message_date: If True, update last_morning_message_date to today

    Returns:
        True if message sent successfully, False otherwise
    """
    if not emotional_pool or not psychological_pool:
        logger.error(f"Message pools not loaded for user {user_id}")
        return False

    try:
        with database.get_db() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE telegram_id = ? AND morning_messages_enabled = 1",
                (user_id,)
            ).fetchone()

            if not row:
                return False

            user = dict(row)
            today = datetime.now(moscow_tz).date().isoformat()

            # Check if already sent today (only for scheduled messages)
            if update_last_message_date and user.get('last_morning_message_date') == today:
                logger.info(f"Skipping user {user_id} - already sent today")
                return False

            # Get shown IDs
            emotional_shown = json.loads(user.get('emotional_pool_shown_ids', '[]'))
            psychological_shown = json.loads(user.get('psychological_pool_shown_ids', '[]'))

            # Get next messages from pools
            emotional_msg, new_emotional_shown = emotional_pool.get_next(emotional_shown)
            psychological_msg, new_psychological_shown = psychological_pool.get_next(psychological_shown)

            # Update database
            if update_last_message_date:
                conn.execute(
                    """UPDATE users
                       SET emotional_pool_shown_ids = ?,
                           psychological_pool_shown_ids = ?,
                           last_morning_message_date = ?,
                           next_morning_message_time = NULL
                       WHERE telegram_id = ?""",
                    (json.dumps(new_emotional_shown),
                     json.dumps(new_psychological_shown),
                     today,
                     user_id)
                )
            else:
                conn.execute(
                    """UPDATE users
                       SET emotional_pool_shown_ids = ?,
                           psychological_pool_shown_ids = ?
                       WHERE telegram_id = ?""",
                    (json.dumps(new_emotional_shown),
                     json.dumps(new_psychological_shown),
                     user_id)
                )
                conn.commit()

            conn.commit()

        # Format and send message
        combined_text = format_combined_message(emotional_msg["text"], psychological_msg["text"])
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Ещё одно сообщение", callback_data="another_message")]
        ])

        await bot.send_message(chat_id=user_id, text=combined_text, reply_markup=keyboard)

        pool_info = f"(emotional: {len(new_emotional_shown)}/{emotional_pool.total_count}, psych: {len(new_psychological_shown)}/{psychological_pool.total_count})"
        if update_last_message_date:
            logger.info(f"Morning message sent to user {user_id} {pool_info}")
        else:
            logger.info(f"Additional message sent to user {user_id} {pool_info}")

        return True

    except Exception as e:
        logger.error(f"Failed to send combined message to {user_id}: {e}", exc_info=True)
        # Try fallback message
        try:
            await bot.send_message(
                chat_id=user_id,
                text="Доброе утро! ❤️ (Произошла техническая ошибка, но я всё равно думаю о тебе)"
            )
        except:
            logger.critical(f"Cannot reach user {user_id} at all")
        return False


async def send_morning_message(bot, user_id: int, is_first: bool = False):
    """Send morning message to user."""
    await _send_combined_message(bot, user_id, update_last_message_date=True)


async def handle_another_message(update: Update, context: CallbackContext):
    """Handle 'Another message' button click."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if not emotional_pool or not psychological_pool:
        await query.answer("Сообщения временно недоступны", show_alert=True)
        return

    success = await _send_combined_message(bot=context.bot, user_id=user_id, update_last_message_date=False)

    if not success:
        await query.answer("Не удалось отправить сообщение", show_alert=True)


def generate_morning_time() -> datetime:
    """Generate random morning message time with normal distribution."""
    mean_minutes = MORNING_MESSAGE_MEAN_MINUTES
    std_minutes = MORNING_MESSAGE_STD_MINUTES

    # Generate random offset
    offset_minutes = np.random.normal(0, std_minutes)

    # Calculate time
    total_minutes = mean_minutes + offset_minutes

    # Clamp to reasonable range (7:30 - 12:00)
    total_minutes = max(MORNING_MESSAGE_MIN_MINUTES, min(MORNING_MESSAGE_MAX_MINUTES, total_minutes))

    hours = int(total_minutes // 60)
    minutes = int(total_minutes % 60)

    # Create datetime for today with Moscow timezone
    today = date.today()
    send_time = datetime.combine(today, time(hour=hours, minute=minutes))
    send_time = send_time.replace(tzinfo=moscow_tz)

    logger.info(f"Generated morning time: {send_time.strftime('%H:%M')} MSK")

    return send_time


async def schedule_morning_messages(bot):
    """Schedule morning messages for all active users."""
    try:
        with database.get_db() as conn:
            rows = conn.execute("""
                SELECT telegram_id, last_morning_message_date
                FROM users
                WHERE morning_messages_enabled = 1
            """).fetchall()

        today = datetime.now(moscow_tz).date().isoformat()
        now_moscow = datetime.now(moscow_tz)
        scheduled_count = 0

        for row in rows:
            user_id = row['telegram_id']
            last_date = row['last_morning_message_date']

            # Skip if already sent today
            if last_date == today:
                continue

            # Generate time
            send_time = generate_morning_time()

            # Если время уже прошло сегодня — отправить немедленно
            if send_time < now_moscow:
                logger.info(f"Morning time {send_time.strftime('%H:%M')} has passed, sending immediately to user {user_id}")
                await send_morning_message(bot, user_id)
                continue

            # Schedule job
            scheduler.add_job(
                send_morning_message,
                'date',
                run_date=send_time,
                args=[bot, user_id],
                id=f'morning_msg_{user_id}',
                replace_existing=True
            )

            # Save time to database
            update_user(user_id, next_morning_message_time=send_time.strftime("%H:%M"))

            scheduled_count += 1
            logger.info(f"Scheduled morning message for user {user_id} at {send_time.strftime('%H:%M')}")

        logger.info(f"Scheduled {scheduled_count} morning messages")

    except Exception as e:
        logger.error(f"Failed to schedule morning messages: {e}", exc_info=True)


async def setup_scheduler(app: Application):
    """Настраивает и запускает планировщик задач."""
    # Morning messages scheduling (new system)
    scheduler.add_job(
        schedule_morning_messages,
        'cron',
        hour=0,
        minute=5,
        args=[app.bot]
    )

    scheduler.start()
    logger.info("Планировщик запущен.")

    # Reschedule pending messages on startup
    await schedule_morning_messages(app.bot)
    logger.info("Проверка и планирование отложенных сообщений завершена.")


def main():
    """Основная функция, настраивающая и запускающая бота."""
    database.init_db()

    token = CONFIG["settings"].get("bot_token")
    if not token or token == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        logger.critical("Критическая ошибка: bot_token не найден в config.json! Укажите токен и перезапустите бота.")
        return

    app = Application.builder().token(token).post_init(setup_scheduler).concurrent_updates(False).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.TEXT & ~filters.COMMAND, restore_state),
        ],
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
                CallbackQueryHandler(handle_another_message, pattern="^another_message$"),
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