import os
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SUBSCRIBERS_FILE = "data/subscribers.json"

# Ensure data dir exists
os.makedirs("data", exist_ok=True)
if not os.path.exists(SUBSCRIBERS_FILE):
    with open(SUBSCRIBERS_FILE, "w") as f:
        json.dump([], f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    with open(SUBSCRIBERS_FILE, "r") as f:
        subscribers = json.load(f)
    
    if user_id not in subscribers:
        subscribers.append(user_id)
        with open(SUBSCRIBERS_FILE, "w") as f:
            json.dump(subscribers, f)
        await update.message.reply_text(
            "✅ Subscribed! You'll get alerts for K-pop world tours (TXT, SEVENTEEN, BLACKPINK, ENHYPEN, and more)."
        )
        print(f"[INFO] New subscriber: {user_id}")
    else:
        await update.message.reply_text("✅ You're already subscribed!")

def main():
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is not set!")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("Telegram bot is running. Send /start to subscribe.")
    app.run_polling()

if __name__ == "__main__":
    main()
