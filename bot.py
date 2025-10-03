from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
import json

# --- Ключевые слова и действия ---
ban_keywords = {
    "оск род": ("/ban", "7", "Оскорбление родни"),
    "нрп обман": ("/permban", "", "Нрп обман"),
    "упом род": ("/mute", "120", "Упоминание родни"),
    "дм": ("/jail", "60", "DeathMatch"),
    "дб": ("/jail", "60", "DriveBy"),
    "капс": ("/mute", "30", "CapsLock"),
    "мг": ("/mute", "30", "MetaGaming"),
    "прово": ("/jail", "30", "Провокация госс"),
    "попытка": ("/permban", "", "Попытка Нрп обмана"),
    "читы": ("/permban", "", "Стороннее ПО"),
    "аморал": ("/jail", "30", "Аморальные действия"),
    "коп": ("/warn", "", "Нрп коп"),
    "оск адм": ("/mute", "180", "Неуважительное обращение к адм"),
}

# --- История нарушений ---
user_stats = {}

# --- Эмодзи для команд ---
action_emojis = {
    "/ban": "🔴",
    "/permban": "🔴",
    "/jail": "🟡",
    "/mute": "🟡",
    "/warn": "🟡",
}

# --- Команды бота ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот модератор. Отправь сообщение, и я проверю его.")

# Проверка текста и генерация действия
async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text.lower()
    words = update.message.text.split()
    username = words[0] if words else ""

    # Проверка на ссылку
    link = ""
    for word in words[1:]:
        if word.startswith("http://") or word.startswith("https://"):
            link = word
            break

    for keyword, (cmd, num, reason) in ban_keywords.items():
        if keyword in message_text:
            ban_command = f"{cmd} {username} {num} {reason} F"

            # Сохраняем нарушение
            if username not in user_stats:
                user_stats[username] = []
            user_stats[username].append({
                "cmd": cmd,
                "reason": reason,
                "link": link,
                "date": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
                "text": ban_command  # сохраняем готовую форму
            })

            # Отправляем одним сообщением
            await update.message.reply_text(ban_command)

            # Удаляем сообщение пользователя
            try:
                await update.message.delete()
            except:
                pass

            return

# /stats Никнейм
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Использование: /stats nickname")
        return

    nickname = context.args[0]
    if nickname not in user_stats:
        await update.message.reply_text("Нет информации по этому игроку.")
        return

    messages = []
    for entry in user_stats[nickname]:
        cmd = entry["cmd"]
        reason = entry["reason"]
        link = entry["link"]
        date = entry["date"]
        emoji = action_emojis.get(cmd, "🟢")
        text = f"{emoji} <b>Ник:</b> {nickname}\n<b>Причина:</b> {reason}\n<b>Дата:</b> {date}"
        if link:
            text += f"\n<a href='{link}'>Ссылка</a>"
        messages.append(text)
        messages.append("-" * 30)
    await update.message.reply_text("\n".join(messages), parse_mode="HTML", disable_web_page_preview=False)

# /last N [nickname]
async def last(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /last N [nickname]")
        return

    N_arg = context.args[0]
    if not N_arg.isdigit():
        await update.message.reply_text("Первый аргумент должен быть число N")
        return

    N = int(N_arg)
    nickname = context.args[1] if len(context.args) > 1 else None

    all_entries = []
    for user, entries in user_stats.items():
        if nickname and user != nickname:
            continue
        for entry in entries:
            all_entries.append((user, entry))

    all_entries.sort(key=lambda x: x[1]["date"], reverse=True)

    for user, entry in all_entries[:N]:
        await update.message.reply_text(entry["text"])

# /allstats
async def allstats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not user_stats:
        await update.message.reply_text("База пустая.")
        return
    await update.message.reply_text("Игроки с нарушениями:\n" + "\n".join(user_stats.keys()))

# /search слово
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Использование: /search слово")
        return

    word = context.args[0].lower()
    result = []
    for nickname, entries in user_stats.items():
        for entry in entries:
            if word in entry["reason"].lower():
                result.append(f"{nickname}: {entry['reason']} ({entry['date']})")
    if not result:
        await update.message.reply_text("Ничего не найдено.")
        return
    await update.message.reply_text("\n".join(result))

# /clear Никнейм
async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Использование: /clear nickname")
        return
    nickname = context.args[0]
    if nickname in user_stats:
        del user_stats[nickname]
        await update.message.reply_text(f"История {nickname} удалена.")
    else:
        await update.message.reply_text("Игрока нет в базе.")

# /clearall
async def clearall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_stats.clear()
    await update.message.reply_text("База очищена.")

# /export
async def export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open("user_stats.json", "w", encoding="utf-8") as f:
        json.dump(user_stats, f, ensure_ascii=False, indent=4)
    await update.message.reply_document(open("user_stats.json", "rb"))

# --- Запуск ---
if __name__ == "__main__":
    TOKEN = "8174814912:AAHjCYdcByjzG-EmeZC0ttDx-6rFCign3sA"
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_message))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("last", last))
    app.add_handler(CommandHandler("allstats", allstats))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("clearall", clearall))
    app.add_handler(CommandHandler("export", export))

    print("Бот запущен...")
    app.run_polling()
