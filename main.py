import os
import json
import time
import requests
from datetime import datetime
from scraper import fetch_all_sources

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # For system alerts
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
    prompt = f"""
    Extract K-pop concert events from text (English/Korean). Output JSON array.
    Format per event: {{"artist":"str","venue":"str","date":"YYYY-MM-DD HH:MM","region":"City, Country","presale":"...","general_sale":"...","source":"https://...","verified":true}}
    Artists: {', '.join(KPOP_ARTISTS_EN)}
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
    except Exception as e:
        print(f"[ERROR] JSON parse failed: {e}")
        return []

def send_telegram_message(text, chat_id=None):
    """Send message to specific chat or all subscribers"""
    if chat_id:
        targets = [chat_id]
    else:
        targets = load_json(SUBSCRIBERS_FILE)
    
    for target in targets:
        try:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": target, "text": text, "parse_mode": "Markdown"}
            )
        except Exception as e:
            print(f"[WARN] Failed to send to {target}: {e}")

def broadcast_to_subscribers(event):
    message = (
        f"🚨 *New K-pop Event!* 🚨\n\n"
        f"🎤 {event['artist']}\n"
        f"📍 {event['venue']} ({event['region']})\n"
        f"📅 {event['date']}\n"
        f"🎟️ Presale: {event.get('presale', 'TBA')}\n"
        f"🔗 [Tickets]({event['source']})"
    )
    send_telegram_message(message)

def main_loop():
    # Send system active alert
    if TELEGRAM_CHAT_ID:
        send_telegram_message("✅ *K-pop Alert System is ACTIVE*\n\nMonitoring:\n• Weverse\n• Fan RSS\n• Interpark\n• BookMyShow\n• Ticketmaster\n\nRuns every 10 minutes.", TELEGRAM_CHAT_ID)
    
    print("✅ System started. Sending active alert to admin.")
    
    while True:
        try:
            print(f"\n[{datetime.now()}] Running scrape cycle...")
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
                        print(f"[INFO] Alert sent: {ev.get('artist')}")
                    else:
                        print(f"[INFO] Duplicate skipped")
        except Exception as e:
            print(f"[CRITICAL] Loop error: {e}")
        print("💤 Sleeping for 10 minutes...")
        time.sleep(600)

if __name__ == "__main__":
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY missing")
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN missing")
    main_loop()
