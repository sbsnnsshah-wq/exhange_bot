import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Введи сумму для обмена (в PLN):",
        reply_markup=menu_keyboard
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_id = update.effective_chat.id

    if text == "💰 Выплатить баланс":
        balance = users.get(chat_id, {}).get("balance", 0)
        await update.message.reply_text(f"💸 Твой баланс: {balance} PLN\nОтправь адрес LTC для вывода.")
        return

    if text == "⚙️ Сменить адрес":
        await update.message.reply_text("🔄 Введи новый LTC-адрес.")
        return

    if text == "📞 Контакт":
        await update.message.reply_text("📬 Поддержка: @your_username")
        return

    # Если текст — число, значит это сумма
    try:
        amount = float(text)
        users[chat_id] = {"amount": amount}
        await update.message.reply_text("📲 Введи код BLIK:")
    except ValueError:
        if "amount" in users.get(chat_id, {}):
            code = text
            amount = users[chat_id]["amount"]
            payout = round(amount * (1 - COMMISSION), 2)

            orders[chat_id] = {"code": code, "amount": amount, "payout": payout}
            users[chat_id]["balance"] = users.get(chat_id, {}).get("balance", 0) + payout

            keyboard = [
                [
                    InlineKeyboardButton("✅ Принять", callback_data=f"accept_{chat_id}"),
                    InlineKeyboardButton("❌ Отклонить", callback_data=f"decline_{chat_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"💳 Новый BLIK-код\nСумма: {amount} PLN\nКод: {code}\n"
                     f"💰 Выплата: {payout} PLN",
                reply_markup=reply_markup
            )
            await update.message.reply_text("✅ Код отправлен на проверку.")
        else:
            await update.message.reply_text("⚠️ Введи сначала сумму.")

async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("accept_"):
        uid = int(data.split("_")[1])
        await context.bot.send_message(chat_id=uid, text="✅ Код принят! Баланс обновлён.")
    elif data.startswith("decline_"):
        uid = int(data.split("_")[1])
        await context.bot.send_message(chat_id=uid, text="❌ Код отклонён. Обратись в поддержку.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(admin_action))
    app.run_polling()

if __name__ == "__main__":
    main()
