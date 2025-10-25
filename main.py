import os
import json
import requests
from datetime import datetime

# Load environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# File to track sent alerts
SENT_EVENTS_FILE = "data/sent_events.json"

# Ensure data directory exists
os.makedirs("data", exist_ok=True)
if not os.path.exists(SENT_EVENTS_FILE):
    with open(SENT_EVENTS_FILE, "w") as f:
        json.dump([], f)

def load_sent_events():
    with open(SENT_EVENTS_FILE, "r") as f:
        return json.load(f)

def save_sent_event(event):
    events = load_sent_events()
    # Use source + date as unique key
    events.append({
        "source": event.get("source", ""),
        "date": event.get("date", ""),
        "artist": event.get("artist", "")
    })
    with open(SENT_EVENTS_FILE, "w") as f:
        json.dump(events, f)

def is_duplicate(event):
    sent = load_sent_events()
    for e in sent:
        if e["source"] == event.get("source") and e["date"] == event.get("date"):
            return True
    return False

def fetch_raw_announcements():
    """
    REPLACE THIS WITH REAL DATA SOURCE LATER.
    For now: simulate a real announcement.
    """
    return """
    TOMORROW X TOGETHER (TXT) 'ACT: PROMISE' World Tour – Kuala Lumpur!
    Date: February 14, 2026 at 6:00 PM
    Venue: Axiata Arena, Bukit Jalil
    Location: Kuala Lumpur, Malaysia
    MOA Presale: October 22, 2025 at 12:00 PM MYT
    General Sale: October 25, 2025 at 12:00 PM MYT
    Tickets: https://my.bookmyshow.com/e/BMSTXT26
    """

def call_openrouter(prompt: str):
    """Call OpenRouter with qwen/qwen3-coder:free"""
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/your-username/kpop-event-alerts",
                "X-Title": "K-pop Event Alert Bot",
            },
            data=json.dumps({
                "model": "qwen/qwen3-coder:free",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
                "max_tokens": 500
            }),
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[ERROR] OpenRouter API call failed: {e}")
        return None

def extract_structured_event(raw_text):
    prompt = f"""
    Extract K-pop concert details from the text below. Output ONLY a valid JSON object in this exact format:
    {{
      "artist": "string",
      "venue": "string",
      "date": "YYYY-MM-DD HH:MM",
      "region": "City, Country",
      "presale": "YYYY-MM-DD HH:MM TZ",
      "general_sale": "YYYY-MM-DD HH:MM TZ",
      "source": "https://...",
      "verified": true
    }}
    Do not add any other text, explanation, or markdown. If a field is unknown, omit it or use null.
    Text: {raw_text}
    """
    
    result = call_openrouter(prompt)
    if not result:
        return None

    content = result["choices"][0]["message"]["content"].strip()

    # Remove markdown code blocks if present
    if content.startswith("```"):
        content = content.split("```json")[-1].split("```")[0].strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        print(f"[ERROR] Invalid JSON from model: {content}")
        return None

def send_telegram_alert(event):
    message = (
        f"🚨 *New K-pop Event Alert!* 🚨\n\n"
        f"🎤 *Artist:* {event['artist']}\n"
        f"📍 *Venue:* {event['venue']}\n"
        f"📅 *Date:* {event['date']} ({event['region']})\n"
        f"🎟️ *Presale:* {event.get('presale', 'TBA')}\n"
        f"🛒 *General Sale:* {event.get('general_sale', 'TBA')}\n"
        f"🔗 [Buy Tickets]({event['source']})"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(
            url,
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": False
            },
            timeout=10
        )
        print(f"[INFO] Alert sent: {event['artist']} – {event['date']}")
    except Exception as e:
        print(f"[ERROR] Failed to send Telegram alert: {e}")

def main():
    print(f"[{datetime.utcnow().isoformat()}] Starting K-pop event check...")
    raw = fetch_raw_announcements()
    event = extract_structured_event(raw)

    if not event:
        print("[INFO] No valid event extracted.")
        return

    if is_duplicate(event):
        print("[INFO] Duplicate event. Skipping.")
        return

    save_sent_event(event)
    send_telegram_alert(event)

if __name__ == "__main__":
    main()
