import requests
import feedparser
import re
from datetime import datetime, timedelta

# === CONFIG ===
KPOP_ARTISTS = [
    "TXT", "TOMORROW X TOGETHER", "ENHYPEN", "SEVENTEEN", "BLACKPINK", "BTS", "TWICE",
    "STRAY KIDS", "NEWJEANS", "IVE", "LE SSERAFIM", "AESPA", "NCT", "EXO", "ITZY", "ZB1"
]

def clean_text(text):
    # Remove URLs, emojis, extra spaces
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'[^\w\s\-.,!?():]+', ' ', text)
    return " ".join(text.split())

def scrape_twitter():
    """
    Simulate Twitter scraping.
    In production: use Twitter API v2 (free tier).
    """
    # Mock recent tweets (replace with real API call)
    mock_tweets = [
        "🚨 OFFICIAL: SEVENTEEN World Tour 'RIGHT HERE' – BANGKOK! Jan 18, 2026. Tickets: https://ticketmaster.co.th/seventeen",
        "BLACKPINK BORN PINK ENCORE – SEOUL! Nov 29-30, 2025. Presale Oct 28 (KST). https://weverse.io/blackpink/tickets",
        "TXT ACT: PROMISE – KUALA LUMPUR! Feb 14, 2026. https://my.bookmyshow.com/e/BMSTXT26"
    ]
    return [clean_text(t) for t in mock_tweets]

def scrape_weverse():
    """
    Scrape official notices via Weverse RSS feeds.
    Example: TXT = https://weverse.io/txt/notice/rss
    """
    weverse_rss_urls = {
        "TXT": "https://weverse.io/txt/notice/rss",
        "ENHYPEN": "https://weverse.io/enhypen/notice/rss",
        "SEVENTEEN": "https://weverse.io/seventeen/notice/rss",
        "BLACKPINK": "https://weverse.io/blackpink/notice/rss",
    }
    notices = []
    for artist, url in weverse_rss_urls.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:  # Last 3 notices
                if any(kw in entry.title.upper() for kw in ["TOUR", "CONCERT", "TICKET", "WORLD TOUR"]):
                    content = f"{artist} NOTICE: {entry.title}. {entry.summary}"
                    notices.append(clean_text(content))
        except Exception as e:
            print(f"[WARN] Weverse scrape failed for {artist}: {e}")
    return notices

def fetch_all_sources():
    twitter = scrape_twitter()
    weverse = scrape_weverse()
    all_text = "\n\n---\n\n".join(twitter + weverse)
    return all_text if all_text.strip() else None
