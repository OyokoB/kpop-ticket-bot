import os
import json
import time
import requests
from datetime import datetime
from scraper import fetch_all_sources

# === CONFIG ===
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SENT_EVENTS_FILE = "data/sent_events.json"
SUBSCRIBERS_FILE = "data/subscribers.json"

os.makedirs("data", exist_ok=True)
for f in [SENT_EVENTS_FILE, SUBSCRIBERS_FILE]:
    if not os.path.exists(f):
        with open(f, "w") as fp:
            json.dump([], fp)

def load_json(file):
    with open(file, "r") as f:
        return json.load(f)

def save_event(event):
    events = load_json(SENT_EVENTS_FILE)
    key = f"{event.get('source')}|{event.get('date')}"
    if not any(e.get("key") == key for e in events):
        events.append({"key": key, **event})
        with open(SENT_EVENTS_FILE, "w") as f:
            json.dump(events, f)

def is_duplicate(event):
    key = f"{event.get('source')}|{event.get('date')}"
    return any(e.get("key") == key for e in load_json(SENT_EVENTS_FILE))

def call_openrouter(prompt):
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/your-username/kpop-event-alerts",
                "X-Title": "K-pop Global Alert Bot",
            },
            json={
                "model": "qwen/qwen3-coder:free",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
                "max_tokens": 600
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[ERROR] OpenRouter: {e}")
        return None

def extract_events(raw_text):
    if not raw_text:
        return []
   # Inside main.py → extract_events()
prompt = f"""
You are a bilingual K-pop event parser. The text may be in English or Korean (already translated to English).
Extract ONLY official concert announcements for these artists: {', '.join(KPOP_ARTISTS_EN)}.
Output a JSON array of events in this format:
{{
  "artist": "English artist name (e.g., SEVENTEEN)",
  "venue": "Venue name",
  "date": "YYYY-MM-DD HH:MM",
  "region": "City, Country",
  "presale": "YYYY-MM-DD HH:MM TZ",
  "general_sale": "YYYY-MM-DD HH:MM TZ",
  "source": "https://...",
  "verified": true
}}
Ignore rumors, fan posts, or unconfirmed dates.
Text: {raw_text}
"""
    result = call_openrouter(prompt)
    if not result:
        return []
    content = result["choices"][0]["message"]["content"].strip()
    if content.startswith("```"):
        content = content.split("```json")[-1].split("```")[0].strip()
    try:
        events = json.loads(content)
        return events if isinstance(events, list) else [events] if isinstance(events, dict) else []
    except:
        return []

def broadcast_to_subscribers(event):
    subscribers = load_json(SUBSCRIBERS_FILE)
    message = (
        f"🚨 *New K-pop Event!* 🚨\n\n"
        f"🎤 {event['artist']}\n"
        f"📍 {event['venue']} ({event['region']})\n"
        f"📅 {event['date']}\n"
        f"🎟️ Presale: {event.get('presale', 'TBA')}\n"
        f"🔗 [Tickets]({event['source']})"
    )
    for user_id in subscribers:
        try:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": user_id, "text": message, "parse_mode": "Markdown"}
            )
        except Exception as e:
            print(f"[WARN] Failed to send to {user_id}: {e}")

def main_loop():
    print("✅ K-pop Alert Engine started (runs every 5 minutes)")
    while True:
        try:
            print(f"\n[{datetime.now()}] Checking sources...")
            raw = fetch_all_sources()
            if not raw:
                print("[INFO] No new data from sources.")
            else:
                events = extract_events(raw)
                print(f"[INFO] Extracted {len(events)} events")
                for ev in events:
                    if not is_duplicate(ev):
                        save_event(ev)
                        broadcast_to_subscribers(ev)
                    else:
                        print(f"[INFO] Duplicate: {ev.get('artist')} – {ev.get('date')}")
        except Exception as e:
            print(f"[CRITICAL] Loop error: {e}")
        print("💤 Sleeping for 5 minutes...")
        time.sleep(300)  # 5 minutes

if __name__ == "__main__":
    main_loop()
