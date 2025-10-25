import os
import requests
import feedparser
import re
import time
import json

# === CONFIG ===
KPOP_ARTISTS_EN = [
    "TXT", "TOMORROW X TOGETHER", "ENHYPEN", "SEVENTEEN", "BLACKPINK", "BTS", "TWICE",
    "STRAY KIDS", "NEWJEANS", "IVE", "LE SSERAFIM", "AESPA", "NCT", "EXO", "ITZY", "ZB1"
]

# Cache file to track last Twitter fetch
CACHE_FILE = "data/twitter_cache.json"
os.makedirs("data", exist_ok=True)

def is_korean(text):
    for char in text:
        if '가' <= char <= '힣' or 'ㄱ' <= char <= 'ㅎ' or 'ㅏ' <= char <= 'ㅣ':
            return True
    return False

def clean_and_prepare(text):
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'[^\w\s\-.,!?():ㄱ-ㅎㅏ-ㅣ가-힣]', ' ', text)
    return " ".join(text.split())

def can_fetch_twitter():
    """Check if we can make a Twitter API call (max once per hour)."""
    if not os.path.exists(CACHE_FILE):
        return True
    try:
        with open(CACHE_FILE, "r") as f:
            cache = json.load(f)
        last_fetch = cache.get("last_twitter_fetch", 0)
        return (time.time() - last_fetch) > 3600  # 1 hour
    except:
        return True

def mark_twitter_fetched():
    """Record last fetch time."""
    with open(CACHE_FILE, "w") as f:
        json.dump({"last_twitter_fetch": time.time()}, f)

def scrape_twitter_v2():
    BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
    if not BEARER_TOKEN:
        print("[WARN] TWITTER_BEARER_TOKEN not set.")
        return []

    if not can_fetch_twitter():
        print("[INFO] Skipping Twitter (rate limit: max once/hour)")
        return []

    artist_keywords = " OR ".join([f'"{a}"' for a in KPOP_ARTISTS_EN])
    kr_keywords = " OR ".join(['"투어"', '"콘서트"', '"티켓"', '"월드투어"'])
    en_keywords = " OR ".join(['"world tour"', '"concert"', '"tickets"', '"tour"'])
    query = f"({artist_keywords}) ({en_keywords} OR {kr_keywords}) -is:retweet -is:reply"

    try:
        response = requests.get(
            "https://api.twitter.com/2/tweets/search/recent",
            headers={"Authorization": f"Bearer {BEARER_TOKEN}"},
            params={
                "query": query,
                "max_results": 20,
                "tweet.fields": "created_at"
            },
            timeout=15
        )
        response.raise_for_status()
        mark_twitter_fetched()
        data = response.json()
        tweets = []
        if "data" in data:  # ✅ FIXED: was incomplete before
            for tweet in data["data"]:
                clean = clean_and_prepare(tweet["text"])
                if any(kw in clean.lower() for kw in ["tour", "concert", "티켓", "투어", "월드투어", "tickets"]):
                    tweets.append(clean)
        return tweets
    except requests.HTTPError as e:
        if e.response.status_code == 429:
            print("[WARN] Twitter rate limit hit. Skipping for 1 hour.")
            mark_twitter_fetched()
        else:
            print(f"[ERROR] Twitter API failed: {e}")
        return []
    except Exception as e:
        print(f"[ERROR] Twitter unexpected error: {e}")
        return []

def scrape_weverse():
    weverse_rss = {
        "TXT": "https://weverse.io/txt/notice/rss",
        "ENHYPEN": "https://weverse.io/enhypen/notice/rss",
        "SEVENTEEN": "https://weverse.io/seventeen/notice/rss",
        "BLACKPINK": "https://weverse.io/blackpink/notice/rss",
    }
    notices = []
    for artist, url in weverse_rss.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:
                full = f"{artist} NOTICE: {entry.title}. {getattr(entry, 'summary', '')}"
                clean = clean_and_prepare(full)
                if any(kw in clean.lower() for kw in ["tour", "concert", "티켓", "투어"]):
                    notices.append(clean)
        except Exception as e:
            print(f"[WARN] Weverse {artist}: {e}")
    return notices

def fetch_all_sources():
    weverse = scrape_weverse()
    twitter = scrape_twitter_v2()
    combined = "\n\n---\n\n".join(twitter + weverse)
    return combined if combined.strip() else None
