import os
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SUBSCRIBERS_FILE = "data/subscribers.json"

os.makedirs("data", exist_ok=True)
if not os.path.exists(SUBSCRIBERS_FILE):
    with open(SUBSCRIBERS_FILE, "w") as f:
        json.dump([], f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Anonymous"
    
    # Load subscribers
    with open(SUBSCRIBERS_FILE, "r") as f:
        subscribers = json.load(f)
    
    if user_id not in subscribers:
        subscribers.append(user_id)
        with open(SUBSCRIBERS_FILE, "w") as f:
            json.dump(subscribers, f)
        await update.message.reply_text(
            "✅ You're subscribed! You'll get alerts for K-pop world tours (TXT, SEVENTEEN, BLACKPINK, ENHYPEN, and more)."
        )
        print(f"[INFO] New subscriber: {username} ({user_id})")
    else:
        await update.message.reply_text("✅ You're already subscribed!")

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("Telegram bot started. Send /start to subscribe.")
    app.run_polling()

if __name__ == "__main__":
    main()
