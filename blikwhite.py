import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters, CallbackContext

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))

COMMISSION = 0.3  # 30%

users = {}
orders = {}

# Главное меню
menu_keyboard = ReplyKeyboardMarkup(
    [["💰 Выплатить баланс", "⚙️ Сменить адрес"], ["📞 Контакт"]],
    resize_keyboard=True
)

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "👋 Привет! Введи сумму для обмена (в PLN):",
        reply_markup=menu_keyboard
    )

def handle_message(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    chat_id = update.effective_chat.id

    if text == "💰 Выплатить баланс":
        balance = users.get(chat_id, {}).get("balance", 0)
        update.message.reply_text(f"💸 Твой баланс: {balance} PLN\nОтправь адрес LTC для вывода.")
        return

    if text == "⚙️ Сменить адрес":
        update.message.reply_text("🔄 Введи новый LTC-адрес.")
        return

    if text == "📞 Контакт":
        update.message.reply_text("📬 Поддержка: @your_username")
        return

    # Если текст — число, значит это сумма
    try:
        amount = float(text)
        users[chat_id] = {"amount": amount}
        update.message.reply_text("📲 Введи код BLIK:")
    except ValueError:
        if
