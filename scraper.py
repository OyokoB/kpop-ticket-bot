import os
import requests
import feedparser
import re

# Supported artists (for filtering)
KPOP_ARTISTS_EN = [
    "TXT", "TOMORROW X TOGETHER", "ENHYPEN", "SEVENTEEN", "BLACKPINK", "BTS", "TWICE",
    "STRAY KIDS", "NEWJEANS", "IVE", "LE SSERAFIM", "AESPA", "NCT", "EXO", "ITZY", "ZB1"
]

def is_korean(text):
    """Check if text contains Korean Hangul characters."""
    for char in text:
        if '가' <= char <= '힣' or 'ㄱ' <= char <= 'ㅎ' or 'ㅏ' <= char <= 'ㅣ':
            return True
    return False

def clean_and_prepare(text):
    """Remove URLs and clean special characters, preserve Korean."""
    text = re.sub(r'http\S+', '', text)  # Remove URLs
    text = re.sub(r'[^\w\s\-.,!?():ㄱ-ㅎㅏ-ㅣ가-힣]', ' ', text)  # Keep Korean + basic chars
    return " ".join(text.split())

def scrape_twitter_v2():
    BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
    if not BEARER_TOKEN:
        print("[WARN] TWITTER_BEARER_TOKEN not set. Skipping Twitter.")
        return []

    # Build query with English + Korean tour keywords
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
        data = response.json()
        tweets = []
        if "data" in data:
            for tweet in data["data"]:
                clean = clean_and_prepare(tweet["text"])
                # Final keyword filter
                if any(kw in clean.lower() for kw in ["tour", "concert", "티켓", "투어", "월드투어", "tickets"]):
                    tweets.append(clean)
        return tweets
    except Exception as e:
        print(f"[ERROR] Twitter API failed: {e}")
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
            for entry in feed.entries[:3]:  # Last 3 notices
                full = f"{artist} NOTICE: {entry.title}. {getattr(entry, 'summary', '')}"
                clean = clean_and_prepare(full)
                if any(kw in clean.lower() for kw in ["tour", "concert", "티켓", "투어"]):
                    notices.append(clean)
        except Exception as e:
            print(f"[WARN] Weverse scrape failed for {artist}: {e}")
    return notices

def fetch_all_sources():
    """Fetch from all sources and return combined text."""
    twitter = scrape_twitter_v2()
    weverse = scrape_weverse()
    combined = "\n\n---\n\n".join(twitter + weverse)
    return combined if combined.strip() else None
