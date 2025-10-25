import os
import requests
import feedparser
from bs4 import BeautifulSoup
import re
import time
import json

KPOP_ARTISTS_EN = [
    "TXT", "TOMORROW X TOGETHER", "ENHYPEN", "SEVENTEEN", "BLACKPINK", "BTS", "TWICE",
    "STRAY KIDS", "NEWJEANS", "IVE", "LE SSERAFIM", "AESPA", "NCT", "EXO", "ITZY", "ZB1"
]

CACHE_FILE = "data/scrape_cache.json"
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

# === 1. FAN UPDATE RSS FEEDS (No API needed) ===
def scrape_fan_rss():
    rss_feeds = [
        "https://rsshub.app/twitter/user/TXT_TourUpdates",
        "https://rsshub.app/twitter/user/SEVENTEEN_tour",
        "https://rsshub.app/twitter/user/BlinkUpdates",
        "https://rsshub.app/twitter/user/ENHYPEN_Tour",
        # Add more fan accounts as needed
    ]
    posts = []
    for url in rss_feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:
                clean = clean_and_prepare(entry.title + " " + getattr(entry, 'summary', ''))
                if any(artist in clean for artist in KPOP_ARTISTS_EN) and any(kw in clean.lower() for kw in ["tour", "concert", "티켓"]):
                    posts.append(clean)
        except Exception as e:
            print(f"[WARN] Fan RSS failed: {url} - {e}")
    return posts

# === 2. TICKET SITE SCRAPERS ===
def scrape_interpark():
    """Scrape Interpark for new K-pop events (Korea)"""
    try:
        # Interpark doesn't have public API, but we can check main event page
        response = requests.get("https://ticket.interpark.com/contents/ranking", timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        # Look for K-pop related titles (simplified)
        text = soup.get_text()
        if any(artist in text for artist in ["투모로우바이투게더", "세븐틴", "블랙핑크", "엔하이픈"]):
            return [f"Interpark: New K-pop event detected. Check https://ticket.interpark.com"]
    except Exception as e:
        print(f"[WARN] Interpark scrape failed: {e}")
    return []

def scrape_bookmyshow_my():
    """Scrape BookMyShow Malaysia for TXT/SEVENTEEN/etc."""
    try:
        response = requests.get("https://www.bookmyshow.com.my/events", timeout=10)
        if "TXT" in response.text or "SEVENTEEN" in response.text or "BLACKPINK" in response.text:
            return [f"BookMyShow MY: K-pop event found. https://www.bookmyshow.com.my"]
    except Exception as e:
        print(f"[WARN] BookMyShow MY failed: {e}")
    return []

def scrape_ticketmaster_global():
    """Check Ticketmaster global search"""
    try:
        # Search for "K-pop" events
        response = requests.get("https://www.ticketmaster.com/search?query=k-pop", timeout=10)
        if any(artist in response.text for artist in ["SEVENTEEN", "BLACKPINK", "TXT"]):
            return [f"Ticketmaster: New K-pop event. https://www.ticketmaster.com"]
    except Exception as e:
        print(f"[WARN] Ticketmaster failed: {e}")
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
            for entry in feed.entries[:2]:
                full = f"{artist} NOTICE: {entry.title}. {getattr(entry, 'summary', '')}"
                clean = clean_and_prepare(full)
                if any(kw in clean.lower() for kw in ["tour", "concert", "티켓", "투어"]):
                    notices.append(clean)
        except Exception as e:
            print(f"[WARN] Weverse {artist}: {e}")
    return notices

# === MAIN SCRAPER ===
def fetch_all_sources():
    print("[INFO] Scraping sources...")
    sources = []
    
    # Official sources (high priority)
    sources.extend(scrape_weverse())
    
    # Fan updates
    sources.extend(scrape_fan_rss())
    
    # Ticket sites (check for new events)
    sources.extend(scrape_interpark())
    sources.extend(scrape_bookmyshow_my())
    sources.extend(scrape_ticketmaster_global())
    
    combined = "\n\n---\n\n".join(sources)
    return combined if combined.strip() else None
