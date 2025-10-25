import os
import json
import requests
from datetime import datetime

# === CONFIG ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Supported artists (case-insensitive match)
KPOP_ARTISTS = [
    "TXT", "TOMORROW X TOGETHER",
    "ENHYPEN",
    "SEVENTEEN",
    "BLACKPINK", "BLACK PINK",
    "BTS", "BANGTAN",
    "TWICE",
    "STRAY KIDS", "SKZ",
    "NEWJEANS",
    "IVE",
    "LE SSERAFIM",
    "AESPA",
    "NCT",
    "EXO",
    "ITZY",
    "ZEROBASEONE", "ZB1"
]

# Major global ticket & news sources (for scraping/future expansion)
TICKET_SITES = {
    "South Korea": [
        "https://ticket.interpark.com",
        "https://www.yes24.com",
        "https://weverse.io"
    ],
    "USA/Global": [
        "https://www.ticketmaster.com",
        "https://www.livenation.com"
    ],
    "Southeast Asia": [
        "https://www.bookmyshow.com",
        "https://www.sistic.com.sg",
        "https://www.ticket2u.com.my"
    ],
    "Japan": [
        "https://eplus.jp",
        "https://www.lawson-ticket.jp"
    ],
    "Europe": [
        "https://www.ticketmaster.co.uk",
        "https://www.eventim.de"
    ]
}

SENT_EVENTS_FILE = "data/sent_events.json"
os.makedirs("data", exist_ok=True)
if not os.path.exists(SENT_EVENTS_FILE):
    with open(SENT_EVENTS_FILE, "w") as f:
        json.dump([], f)

# === UTILS ===
def load_sent_events():
    with open(SENT_EVENTS_FILE, "r") as f:
        return json.load(f)

def save_sent_event(event):
    events = load_sent_events()
    key = f"{event.get('source', '')}|{event.get('date', '')}"
    if not any(e.get("key") == key for e in events):
        events.append({"key": key, **event})
        with open(SENT_EVENTS_FILE, "w") as f:
            json.dump(events, f)

def is_duplicate(event):
    key = f"{event.get('source', '')}|{event.get('date', '')}"
    return any(e.get("key") == key for e in load_sent_events())

# === SIMULATED DATA SOURCE (REPLACE WITH REAL SCRAPER LATER) ===
def fetch_raw_announcements():
    """
    In production: scrape Twitter, Weverse, or ticket sites.
    For now: return recent real-world examples.
    """
    samples = [
        """
        BLACKPINK WORLD TOUR [BORN PINK] ENCORE – SEOUL 2025!
        Date: November 29–30, 2025 at 6:00 PM
        Venue: Gocheok Sky Dome
        Region: Seoul, South Korea
        Presale: October 28, 2025 (12:00 PM KST) via Weverse
        General Sale: October 30, 2025 (12:00 PM KST)
        Tickets: https://weverse.io/blackpink/tickets
        """,
        """
        SEVENTEEN WORLD TOUR 'RIGHT HERE' – BANGKOK!
        Date: January 18, 2026 at 5:00 PM
        Venue: Rajamangala National Stadium
        Region: Bangkok, Thailand
        Presale: November 5, 2025 (10:00 AM ICT)
        General Sale: November 8, 2025 (10:00 AM ICT)
        Tickets: https://www.ticketmaster.co.th/event/seventeen-right-here-bangkok
        """,
        """
        TOMORROW X TOGETHER (TXT) 'ACT: PROMISE' – KUALA LUMPUR
        Date: February 14, 2026 at 6:00 PM
        Venue: Axiata Arena, Bukit Jalil
        Region: Kuala Lumpur, Malaysia
        Presale: October 22, 2025 (12:00 PM MYT)
        General Sale: October 25, 2025 (12:00 PM MYT)
        Tickets: https://my.bookmyshow.com/e/BMSTXT26
        """
    ]
    # In real use: return combined scraped content
    return "\n\n---\n\n".join(samples)

# === OPENROUTER INTEGRATION ===
def call_openrouter(prompt: str):
    if not OPENROUTER_API_KEY:
        print("[FATAL] OPENROUTER_API_KEY is not set!")
        return None
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/your-username/kpop-event-alerts",
                "X-Title": "K-pop Global Alert Bot",
            },
            data=json.dumps({
                "model": "qwen/qwen3-coder:free",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
                "max_tokens": 600
            }),
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[ERROR] OpenRouter failed: {e}")
        return None

# === EVENT EXTRACTION ===
def extract_structured_events(raw_text):
    prompt = f"""
    You are a K-pop event parser. Extract ALL concert announcements from the text below.
    Output ONLY a JSON array of objects. Each object must follow this format:
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
    Rules:
    - Include only events for these artists: {', '.join(KPOP_ARTISTS)}
    - If time is missing, use 18:00
    - If timezone is missing, infer from region (e.g., MYT for Malaysia, KST for Korea)
    - Output valid JSON ONLY. No markdown, no explanation.
    
    Text:
    {raw_text}
    """
    
    result = call_openrouter(prompt)
    if not result:
        return []
    
    content = result["choices"][0]["message"]["content"].strip()
    
    # Clean markdown
    if content.startswith("```"):
        content = content.split("```json")[-1].split("```")[0].strip()
    
    try:
        events = json.loads(content)
        if isinstance(events, dict):
            events = [events]
        return events if isinstance(events, list) else []
    except Exception as e:
        print(f"[ERROR] JSON parse failed: {e} | Content: {content[:200]}")
        return []

# === TELEGRAM ALERT ===
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
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
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
        print(f"[ERROR] Telegram failed: {e}")

# === MAIN ===
def main():
    print(f"[{datetime.utcnow().isoformat()}] Checking for K-pop events...")
    
    # Safety check
    if not all([TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, OPENROUTER_API_KEY]):
        print("[FATAL] Missing environment variables!")
        return

    raw = fetch_raw_announcements()
    events = extract_structured_events(raw)
    
    print(f"[INFO] Found {len(events)} potential events")
    
    for event in events:
        if not is_duplicate(event):
            save_sent_event(event)
            send_telegram_alert(event)
        else:
            print(f"[INFO] Duplicate skipped: {event.get('artist')} – {event.get('date')}")

if __name__ == "__main__":
    main()
