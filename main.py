import os
import json
import requests
from datetime import datetime

# Load environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Paths
SENT_EVENTS_FILE = "data/sent_events.json"

# Ensure data dir exists
os.makedirs("data", exist_ok=True)
if not os.path.exists(SENT_EVENTS_FILE):
    with open(SENT_EVENTS_FILE, "w") as f:
        json.dump([], f)

def load_sent_events():
    with open(SENT_EVENTS_FILE, "r") as f:
        return json.load(f)

def save_sent_event(event):
    events = load_sent_events()
    events.append({
        "source": event["source"],
        "date": event["date"],
        "artist": event["artist"]
    })
    with open(SENT_EVENTS_FILE, "w") as f:
        json.dump(events, f)

def is_duplicate(event):
    sent = load_sent_events()
    for e in sent:
        if e["source"] == event["source"] and e["date"] == event["date"]:
            return True
    return False

def fetch_raw_announcements():
    """
    Simulate fetching from a source.
    In real use: scrape Twitter/X, Weverse, or ticket sites.
    For demo: return hardcoded example.
    """
    return """
    TOMORROW X TOGETHER (TXT) has announced their 'ACT: PROMISE' World Tour stop in Kuala Lumpur!
    Date: February 14, 2026 at 6:00 PM
    Venue: Axiata Arena, Bukit Jalil
    Region: Kuala Lumpur, Malaysia
    Presale starts: October 22, 2025 at 12:00 PM MYT (MOA members)
    General sale: October 25, 2025 at 12:00 PM MYT
    Tickets: https://my.bookmyshow.com/e/BMSTXT26
    """

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
    Do not add extra fields. If a field is unknown, omit it or use null.
    Text: {raw_text}
    """

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "qwen/qwen3-coder",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
                "max_tokens": 500
            },
            timeout=30
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"].strip()

        # Clean markdown code blocks
        if content.startswith("```"):
            content = content.split("```json")[-1].split("```")[0].strip()

        event = json.loads(content)
        return event
    except Exception as e:
        print(f"[ERROR] Extraction failed: {e}")
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
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    try:
        requests.post(url, json=payload, timeout=10)
        print(f"[INFO] Alert sent for {event['artist']} on {event['date']}")
    except Exception as e:
        print(f"[ERROR] Telegram send failed: {e}")

def main():
    print(f"[{datetime.now()}] Checking for new K-pop events...")
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
