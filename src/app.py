import asyncio
import logging
import re
import time
import os
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import pytz
from bomber import HighVelocityBomber
from proxy_manager import ProxyManager

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "8179350031:AAF71X8FZF-C4mP0HEYiMezSURxBi2di0dw")
ADMIN_ID = int(os.getenv("ADMIN_ID", "00000000"))
GH_TOKEN = os.getenv("GH_TOKEN")
BOMB_SESSIONS = {}
PROXY_MANAGER = ProxyManager()  # Global proxy manager instance

# Conversation states
SELECT_TYPE, SELECT_INTENSITY, ENTER_PHONE = range(3)

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# GitHub Actions config (REPLACE WITH YOUR VALUES)
REPO_OWNER = "your_github_username"
REPO_NAME = "your_repository_name"
WORKFLOW_ID = "bomber.yml"

def is_russian_phone(phone: str) -> bool:
    """Validate Russian phone number format"""
    return re.match(r'^\+7\d{10}$', phone) is not None

def format_phone(phone: str) -> str:
    """Format phone number to Russian standard"""
    digits = re.sub(r'\D', '', phone)
    if digits.startswith('8') and len(digits) == 11:
        return '+7' + digits[1:]
    if digits.startswith('7') and len(digits) == 11:
        return '+' + digits
    if len(digits) == 10:
        return '+7' + digits
    return '+' + digits

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start command handler"""
    user = update.effective_user
    if user.id in BOMB_SESSIONS:
        await update.message.reply_text(
            "🚫 У вас уже есть активная атака! Остановите текущую перед началом новой."
        )
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton("💣 SMS Бомбардировка", callback_data="sms")],
        [InlineKeyboardButton("📞 Звонковый Спам", callback_data="call")],
        [InlineKeyboardButton("☁️ Cloud Attack (Beta)", callback_data="cloud")]
    ]

    await update.message.reply_text(
        "🔥 Добро пожаловать в Russian Bomber! 🔥\n\n"
        "Выберите тип атаки:",
        reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_TYPE

async def select_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle attack type selection"""
    query = update.callback_query
    await query.answer()

    attack_type = query.data
    context.user_data['type'] = attack_type

    if attack_type == "cloud":
        await query.edit_message_text(
            text="☁️ Запускаем распределённую атаку через GitHub Actions...")
        await start_cloud_attack(update, context)
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton("⚡️ Ураганная (10 мин)", callback_data="hurricane")],
        [InlineKeyboardButton("🔥 Высокая (15 мин)", callback_data="high")],
        [InlineKeyboardButton("☁ Скрытная (30 мин)", callback_data="low")]
    ]

    await query.edit_message_text(
        text="Выберите интенсивность атаки:",
        reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_INTENSITY

async def start_cloud_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start distributed attack via GitHub Actions"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        text="📱 Введите российский номер телефона в формате +7XXXXXXXXXX:")
    context.user_data['cloud'] = True
    return ENTER_PHONE

async def select_intensity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle intensity selection"""
    query = update.callback_query
    await query.answer()

    intensity = query.data
    context.user_data['intensity'] = intensity

    await query.edit_message_text(
        text="📱 Введите российский номер телефона в формате +7XXXXXXXXXX:")
    return ENTER_PHONE

async def enter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle phone number input"""
    phone = format_phone(update.message.text)
    user = update.message.from_user
    chat_id = update.effective_chat.id

    if not is_russian_phone(phone):
        await update.message.reply_text("❌ Неверный формат номера! Используйте формат +7XXXXXXXXXX")
        return ENTER_PHONE

    # Cloud attack
    if context.user_data.get('cloud'):
        await trigger_github_action(phone, context, user.id, chat_id)
        return ConversationHandler.END

    # Local attack
    try:
        bomb_session = HighVelocityBomber(
            phone=phone,
            bomb_type=context.user_data['type'],
            intensity=context.user_data['intensity'],
            chat_id=chat_id,
            proxy_manager=PROXY_MANAGER
        )
    except Exception as e:
        logger.error(f"Error creating bomber: {e}")
        await update.message.reply_text("❌ Ошибка при запуске атаки! Попробуйте позже.")
        return ConversationHandler.END

    # Store session
    BOMB_SESSIONS[user.id] = bomb_session

    # Send confirmation
    keyboard = [[InlineKeyboardButton("⛔ Остановить атаку", callback_data=f"stop_{user.id}")]]
    message = await update.message.reply_text(
        f"🚀 Запуск атаки на номер {phone}!\n"
        "⚡ Статус: ИНИЦИАЛИЗАЦИЯ...",
        reply_markup=InlineKeyboardMarkup(keyboard))

    # Store message ID in session
    bomb_session.status_msg_id = message.message_id

    # Start bombing in background
    asyncio.create_task(run_bombing(user.id, bomb_session, context))

    return ConversationHandler.END

async def trigger_github_action(phone: str, context: ContextTypes.DEFAULT_TYPE, user_id: int, chat_id: int):
    """Trigger GitHub Actions workflow"""
    if not GH_TOKEN:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ GitHub token not configured! Cloud attack disabled.")
        return

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GH_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    payload = {
        "ref": "main",
        "inputs": {
            "phone": phone,
            "chat_id": str(chat_id),
            "user_id": str(user_id)
        }
    }

    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/{WORKFLOW_ID}/dispatches"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 204:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"☁️ Запуск распределённой атаки на {phone}!\n"
                             "⚡ Рабочие процессы запускаются на GitHub...")
                else:
                    error = await response.text()
                    logger.error(f"GitHub API error: {response.status} - {error}")
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="❌ Ошибка запуска cloud attack! Попробуйте позже.")
        except Exception as e:
            logger.error(f"GitHub request failed: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ Ошибка подключения к GitHub! Попробуйте позже.")

async def run_bombing(user_id, bomb_session, context):
    """Run bombing and update status"""
    chat_id = bomb_session.chat_id
    msg_id = bomb_session.status_msg_id

    # Start bombing
    asyncio.create_task(bomb_session.start_attack())

    # Update status every 3 seconds
    start_time = time.time()
    while bomb_session.active:
        elapsed = int(time.time() - start_time)
        total = bomb_session.success + bomb_session.failed
        success_rate = bomb_session.success / total * 100 if total > 0 else 0

        status = (
            f"🔥 АТАКА В ПРОЦЕССЕ 🔥\n\n"
            f"📱 Цель: +7{bomb_session.phone}\n"
            f"🎯 Тип: {'SMS' if bomb_session.bomb_type == 'sms' else 'Звонки'}\n"
            f"⚡ Интенсивность: {get_intensity_name(bomb_session.intensity)}\n"
            f"⏱ Время: {elapsed // 60}м {elapsed % 60}с\n"
            f"📡 Скорость: {bomb_session.speed:.1f} req/сек\n"
            f"✅ Успешно: {bomb_session.success}\n"
            f"❌ Ошибки: {bomb_session.failed}\n"
            f"📊 Успешность: {success_rate:.1f}%\n"
            f"🔰 Статус: АКТИВНА"
        )

        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=msg_id,
                text=status,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("⛔ Остановить атаку", callback_data=f"stop_{user_id}")]]))
        except Exception as e:
            logger.error(f"Error updating status: {e}")

        await asyncio.sleep(3)

    # Final status
    elapsed = int(time.time() - start_time)
    total = bomb_session.success + bomb_session.failed
    success_rate = bomb_session.success / total * 100 if total > 0 else 0
    status = (
        f"✅ АТАКА ЗАВЕРШЕНА ✅\n\n"
        f"📱 Цель: +7{bomb_session.phone}\n"
        f"⏱ Общее время: {elapsed // 60}м {elapsed % 60}с\n"
        f"💣 Всего отправлено: {total}\n"
        f"✅ Успешно: {bomb_session.success}\n"
        f"❌ Ошибки: {bomb_session.failed}\n"
        f"📊 Успешность: {success_rate:.1f}%"
    )

    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg_id,
            text=status)
    except Exception as e:
        logger.error(f"Error sending final status: {e}")

    # Cleanup
    if user_id in BOMB_SESSIONS:
        del BOMB_SESSIONS[user_id]

def get_intensity_name(intensity: str) -> str:
    """Get intensity display name"""
    names = {
        "hurricane": "Ураганная",
        "high": "Высокая",
        "low": "Скрытная"
    }
    return names.get(intensity, "Неизвестно")

async def stop_bombing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop active bombing session"""
    query = update.callback_query
    await query.answer()

    try:
        user_id = int(query.data.split('_')[1])
        if user_id in BOMB_SESSIONS:
            BOMB_SESSIONS[user_id].stop()
            await query.edit_message_text(text="⛔ АТАКА ОСТАНОВЛЕНА ПОЛЬЗОВАТЕЛЕМ")
    except Exception as e:
        logger.error(f"Error stopping bombing: {e}")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel conversation"""
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

async def update_proxies():
    """Periodic proxy update"""
    logger.info("Updating proxy list...")
    await PROXY_MANAGER.fetch_proxies()

def main() -> None:
    """Start the bot"""
    # Build the application
    application = Application.builder() \
        .token(BOT_TOKEN) \
        .build()

    # Create scheduler for proxy updates
    scheduler = AsyncIOScheduler()
    scheduler.add_job(update_proxies, IntervalTrigger(minutes=30))
    scheduler.start()

    # Initial proxy load
    asyncio.create_task(update_proxies())

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_TYPE: [CallbackQueryHandler(select_type)],
            SELECT_INTENSITY: [CallbackQueryHandler(select_intensity)],
            ENTER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_phone)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=True
    )

    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(stop_bombing, pattern=r"^stop_\d+$"))

    application.run_polling()

if __name__ == "__main__":
    main()
