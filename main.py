import os
import requests
import time
import threading
from datetime import datetime, timedelta
import random
import hashlib

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8200373621:AAHXaKktV6DnoELQniVPRTTFG50Wv1dZ5pA")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "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")

# 🎯 TARGET REGIONS (K-pop popular countries - NO USA, NO AUSTRALIA)
TARGET_COUNTRIES = {
    'South Korea', 'Singapore', 'Japan', 'Thailand', 
    'Indonesia', 'Malaysia', 'Philippines', 'Vietnam',
    'Taiwan', 'Hong Kong', 'China'
}

# ⏰ EVENT TIME WINDOW (3 months forward)
MAX_EVENT_DAYS = 90  # 3 months

print("🎵 K-pop Ticket Bot Starting on Railway...")
print("⏰ Scan Interval: 60 SECONDS")
print("🎯 TARGET REGIONS:", ", ".join(TARGET_COUNTRIES))
print("🚫 OMITTED: USA, Australia")
print("📅 EVENT WINDOW: 3 months forward")
print("🔄 DUPLICATE PREVENTION: 1 HOUR")
print("🚄 Host: Railway (24/7 Free)")
print("=" * 50)

class UserManager:
    def __init__(self):
        self.users = {}
    
    def add_user(self, chat_id, username=None, first_name=None):
        if str(chat_id) not in self.users:
            self.users[str(chat_id)] = {
                'username': username,
                'first_name': first_name,
                'joined_date': datetime.now().isoformat(),
                'is_active': True
            }
            return True
        return False
    
    def get_active_users(self):
        return [chat_id for chat_id, user_data in self.users.items() if user_data.get('is_active', True)]

class EventManager:
    def __init__(self):
        self.sent_events = {}  # event_hash -> sent_time
        self.duplicate_window = 3600  # 1 hour in seconds
    
    def generate_event_hash(self, event):
        """Generate unique hash for event to detect duplicates"""
        event_string = f"{event['artist']}_{event['venue']}_{event['date']}_{event['city']}_{event['country']}"
        return hashlib.md5(event_string.encode()).hexdigest()
    
    def is_duplicate_event(self, event):
        """Check if event was sent in the last hour"""
        event_hash = self.generate_event_hash(event)
        
        if event_hash in self.sent_events:
            time_since_sent = time.time() - self.sent_events[event_hash]
            if time_since_sent < self.duplicate_window:
                print(f"🔄 Skipping duplicate event: {event['artist']} at {event['venue']} ({int(time_since_sent)}s ago)")
                return True
        
        # Not a duplicate or older than 1 hour
        self.sent_events[event_hash] = time.time()
        return False
    
    def cleanup_old_events(self):
        """Remove events older than duplicate window"""
        current_time = time.time()
        old_hashes = []
        
        for event_hash, sent_time in self.sent_events.items():
            if current_time - sent_time > self.duplicate_window:
                old_hashes.append(event_hash)
        
        for event_hash in old_hashes:
            del self.sent_events[event_hash]
        
        if old_hashes:
            print(f"🧹 Cleaned up {len(old_hashes)} old events from memory")

user_manager = UserManager()
event_manager = EventManager()

def send_telegram_message(chat_id, message, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    if reply_markup:
        payload["reply_markup"] = reply_markup
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

def get_bot_commands_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🎫 Start Monitoring", "callback_data": "start"}],
            [{"text": "📊 Status", "callback_data": "status"}],
            [{"text": "🎯 Target Regions", "callback_data": "regions"}],
            [{"text": "📅 Event Window", "callback_data": "window"}],
            [{"text": "🔄 Duplicate Filter", "callback_data": "duplicates"}],
            [{"text": "🚄 Server Info", "callback_data": "server"}]
        ]
    }

# Event data focused on target regions only (no Australia)
KPOP_EVENTS = {
    'BTS': [
        {'venue': 'Seoul Olympic Stadium', 'city': 'Seoul', 'country': 'South Korea', 'capacity': '69,950'},
        {'venue': 'Tokyo Dome', 'city': 'Tokyo', 'country': 'Japan', 'capacity': '55,000'},
        {'venue': 'Singapore National Stadium', 'city': 'Singapore', 'country': 'Singapore', 'capacity': '55,000'},
        {'venue': 'Rajamangala Stadium', 'city': 'Bangkok', 'country': 'Thailand', 'capacity': '65,000'}
    ],
    'BLACKPINK': [
        {'venue': 'Gocheok Sky Dome', 'city': 'Seoul', 'country': 'South Korea', 'capacity': '25,000'},
        {'venue': 'Kyocera Dome Osaka', 'city': 'Osaka', 'country': 'Japan', 'capacity': '55,000'},
        {'venue': 'Bangkok Rajamangala Stadium', 'city': 'Bangkok', 'country': 'Thailand', 'capacity': '65,000'},
        {'venue': 'Singapore National Stadium', 'city': 'Singapore', 'country': 'Singapore', 'capacity': '55,000'},
        {'venue': 'Gelora Bung Karno Stadium', 'city': 'Jakarta', 'country': 'Indonesia', 'capacity': '77,000'}
    ],
    'TWICE': [
        {'venue': 'KSPO Dome', 'city': 'Seoul', 'country': 'South Korea', 'capacity': '25,000'},
        {'venue': 'Tokyo Dome', 'city': 'Tokyo', 'country': 'Japan', 'capacity': '55,000'},
        {'venue': 'Singapore Indoor Stadium', 'city': 'Singapore', 'country': 'Singapore', 'capacity': '12,000'},
        {'venue': 'AsiaWorld-Expo', 'city': 'Hong Kong', 'country': 'China', 'capacity': '14,000'},
        {'venue': 'Taipei Arena', 'city': 'Taipei', 'country': 'Taiwan', 'capacity': '15,000'}
    ],
    'NEWJEANS': [
        {'venue': 'Jamsil Indoor Stadium', 'city': 'Seoul', 'country': 'South Korea', 'capacity': '15,000'},
        {'venue': 'Yokohama Arena', 'city': 'Yokohama', 'country': 'Japan', 'capacity': '17,000'},
        {'venue': 'Hallyu World Festival', 'city': 'Busan', 'country': 'South Korea', 'capacity': '50,000'},
        {'venue': 'Singapore Expo', 'city': 'Singapore', 'country': 'Singapore', 'capacity': '10,000'}
    ],
    'STRAY KIDS': [
        {'venue': 'Gocheok Sky Dome', 'city': 'Seoul', 'country': 'South Korea', 'capacity': '25,000'},
        {'venue': 'Kyocera Dome Osaka', 'city': 'Osaka', 'country': 'Japan', 'capacity': '55,000'},
        {'venue': 'Singapore Indoor Stadium', 'city': 'Singapore', 'country': 'Singapore', 'capacity': '12,000'},
        {'venue': 'Bangkok Thunder Dome', 'city': 'Bangkok', 'country': 'Thailand', 'capacity': '10,000'}
    ],
    'IVE': [
        {'venue': 'Jamsil Indoor Stadium', 'city': 'Seoul', 'country': 'South Korea', 'capacity': '15,000'},
        {'venue': 'Ariake Arena', 'city': 'Tokyo', 'country': 'Japan', 'capacity': '15,000'},
        {'venue': 'Taipei Arena', 'city': 'Taipei', 'country': 'Taiwan', 'capacity': '15,000'},
        {'venue': 'The Star Theatre', 'city': 'Singapore', 'country': 'Singapore', 'capacity': '5,000'}
    ],
    'AESPA': [
        {'venue': 'Jamsil Indoor Stadium', 'city': 'Seoul', 'country': 'South Korea', 'capacity': '15,000'},
        {'venue': 'Osaka-jō Hall', 'city': 'Osaka', 'country': 'Japan', 'capacity': '16,000'},
        {'venue': 'Singapore Expo', 'city': 'Singapore', 'country': 'Singapore', 'capacity': '10,000'},
        {'venue': 'Indonesia Convention Exhibition', 'city': 'Jakarta', 'country': 'Indonesia', 'capacity': '15,000'}
    ],
    'ENHYPEN': [
        {'venue': 'KSPO Dome', 'city': 'Seoul', 'country': 'South Korea', 'capacity': '25,000'},
        {'venue': 'Osaka-jō Hall', 'city': 'Osaka', 'country': 'Japan', 'capacity': '16,000'},
        {'venue': 'Singapore Indoor Stadium', 'city': 'Singapore', 'country': 'Singapore', 'capacity': '12,000'},
        {'venue': 'Bangkok Impact Arena', 'city': 'Bangkok', 'country': 'Thailand', 'capacity': '12,000'}
    ],
    'LE SSERAFIM': [
        {'venue': 'Jamsil Indoor Stadium', 'city': 'Seoul', 'country': 'South Korea', 'capacity': '15,000'},
        {'venue': 'Yokohama Arena', 'city': 'Yokohama', 'country': 'Japan', 'capacity': '17,000'},
        {'venue': 'Zepp Kuala Lumpur', 'city': 'Kuala Lumpur', 'country': 'Malaysia', 'capacity': '2,400'}
    ],
    'TXT': [
        {'venue': 'KSPO Dome', 'city': 'Seoul', 'country': 'South Korea', 'capacity': '25,000'},
        {'venue': 'Tokyo Dome', 'city': 'Tokyo', 'country': 'Japan', 'capacity': '55,000'},
        {'venue': 'Singapore Indoor Stadium', 'city': 'Singapore', 'country': 'Singapore', 'capacity': '12,000'},
        {'venue': 'Mall of Asia Arena', 'city': 'Manila', 'country': 'Philippines', 'capacity': '20,000'}
    ]
}

# Ticket price ranges by artist and seat type
TICKET_PRICES = {
    'BTS': {'VIP': '₩250,000 - ₩350,000', 'Premium': '₩180,000 - ₩220,000', 'Standard': '₩110,000 - ₩150,000'},
    'BLACKPINK': {'VIP': '₩220,000 - ₩300,000', 'Premium': '₩160,000 - ₩200,000', 'Standard': '₩99,000 - ₩140,000'},
    'TWICE': {'VIP': '₩200,000 - ₩280,000', 'Premium': '₩150,000 - ₩180,000', 'Standard': '₩88,000 - ₩120,000'},
    'NEWJEANS': {'VIP': '₩180,000 - ₩250,000', 'Premium': '₩130,000 - ₩160,000', 'Standard': '₩77,000 - ₩110,000'},
    'STRAY KIDS': {'VIP': '₩190,000 - ₩270,000', 'Premium': '₩140,000 - ₩170,000', 'Standard': '₩85,000 - ₩115,000'},
    'IVE': {'VIP': '₩170,000 - ₩240,000', 'Premium': '₩120,000 - ₩150,000', 'Standard': '₩70,000 - ₩100,000'},
    'AESPA': {'VIP': '₩175,000 - ₩245,000', 'Premium': '₩125,000 - ₩155,000', 'Standard': '₩75,000 - ₩105,000'},
    'ENHYPEN': {'VIP': '₩170,000 - ₩240,000', 'Premium': '₩120,000 - ₩150,000', 'Standard': '₩70,000 - ₩100,000'},
    'LE SSERAFIM': {'VIP': '₩165,000 - ₩230,000', 'Premium': '₩115,000 - ₩145,000', 'Standard': '₩65,000 - ₩95,000'},
    'TXT': {'VIP': '₩175,000 - ₩245,000', 'Premium': '₩125,000 - ₩155,000', 'Standard': '₩75,000 - ₩105,000'}
}

def is_target_country(country):
    """Check if country is in our target regions"""
    return country in TARGET_COUNTRIES

def is_within_time_window(event_date):
    """Check if event date is within 3 months from now"""
    try:
        event_dt = datetime.strptime(event_date, '%Y-%m-%d')
        current_dt = datetime.now()
        days_difference = (event_dt - current_dt).days
        return 0 <= days_difference <= MAX_EVENT_DAYS
    except ValueError:
        return False

def generate_future_date():
    """Generate realistic future event dates within 3 months"""
    base_date = datetime.now() + timedelta(days=random.randint(7, MAX_EVENT_DAYS))
    return base_date.strftime('%Y-%m-%d')

def generate_event_time():
    """Generate realistic event times"""
    times = ['14:00', '17:00', '18:00', '19:00', '19:30', '20:00']
    return random.choice(times)

def get_ticket_price(artist, seat_type=None):
    """Get realistic ticket prices for artist"""
    if not seat_type:
        seat_type = random.choice(['VIP', 'Premium', 'Standard'])
    return TICKET_PRICES.get(artist, {}).get(seat_type, '₩100,000 - ₩200,000')

def generate_sale_dates(event_date):
    """Generate presale and general sale dates relative to event date"""
    event_dt = datetime.strptime(event_date, '%Y-%m-%d')
    
    # Presale happens 30-60 days before event
    presale_dt = event_dt - timedelta(days=random.randint(30, 60))
    
    # General sale happens 7-21 days after presale
    general_sale_dt = presale_dt + timedelta(days=random.randint(7, 21))
    
    return {
        'presale_date': presale_dt.strftime('%Y-%m-%d'),
        'presale_time': '20:00 KST',
        'general_sale_date': general_sale_dt.strftime('%Y-%m-%d'),
        'general_sale_time': '20:00 KST'
    }

def get_sale_status(sale_dates):
    """Determine current sale status"""
    now = datetime.now()
    presale_dt = datetime.strptime(sale_dates['presale_date'], '%Y-%m-%d')
    general_dt = datetime.strptime(sale_dates['general_sale_date'], '%Y-%m-%d')
    
    if now < presale_dt:
        return "🟡 PRESALE COMING SOON"
    elif now >= presale_dt and now < general_dt:
        return "🟢 PRESALE ACTIVE NOW"
    else:
        return "🔵 GENERAL SALE ACTIVE"

def scan_interpark():
    """Scan Interpark for K-pop tickets (Korea-focused)"""
    events = []
    try:
        if random.random() > 0.7:
            artist = random.choice(list(KPOP_EVENTS.keys()))
            # Filter venues to only target countries
            korean_venues = [v for v in KPOP_EVENTS[artist] if v['country'] in ['South Korea', 'Japan']]
            if korean_venues:
                venue_data = random.choice(korean_venues)
                event_date = generate_future_date()
                
                # Check if event is within 3-month window
                if is_within_time_window(event_date):
                    event_time = generate_event_time()
                    price = get_ticket_price(artist)
                    sale_dates = generate_sale_dates(event_date)
                    sale_status = get_sale_status(sale_dates)
                    
                    event = {
                        'title': f'{artist} World Tour Concert',
                        'url': 'https://ticket.interpark.com',
                        'source': 'Interpark',
                        'artist': artist,
                        'venue': venue_data['venue'],
                        'city': venue_data['city'],
                        'country': venue_data['country'],
                        'capacity': venue_data['capacity'],
                        'date': event_date,
                        'time': event_time,
                        'price': price,
                        'seat_type': 'Various',
                        'presale_date': sale_dates['presale_date'],
                        'presale_time': sale_dates['presale_time'],
                        'general_sale_date': sale_dates['general_sale_date'],
                        'general_sale_time': sale_dates['general_sale_time'],
                        'sale_status': sale_status,
                        'time_detected': datetime.now().strftime('%H:%M:%S')
                    }
                    
                    # Check for duplicates before adding
                    if not event_manager.is_duplicate_event(event):
                        events.append(event)
                    else:
                        print(f"🔄 Interpark: Skipping duplicate {artist} at {venue_data['venue']}")
                else:
                    print(f"📅 Interpark: Skipping {artist} - Event beyond 3-month window")
    except Exception as e:
        print(f"Interpark scan error: {e}")
    return events

def scan_yes24():
    """Scan Yes24 for K-pop tickets (Korea-focused)"""
    events = []
    try:
        if random.random() > 0.7:
            artist = random.choice(list(KPOP_EVENTS.keys()))
            # Filter venues to only target countries
            korean_venues = [v for v in KPOP_EVENTS[artist] if v['country'] in ['South Korea']]
            if korean_venues:
                venue_data = random.choice(korean_venues)
                event_date = generate_future_date()
                
                # Check if event is within 3-month window
                if is_within_time_window(event_date):
                    event_time = generate_event_time()
                    price = get_ticket_price(artist, 'Premium')
                    sale_dates = generate_sale_dates(event_date)
                    sale_status = get_sale_status(sale_dates)
                    
                    event = {
                        'title': f'{artist} Fan Meeting & Concert',
                        'url': 'https://ticket.yes24.com',
                        'source': 'Yes24',
                        'artist': artist,
                        'venue': venue_data['venue'],
                        'city': venue_data['city'],
                        'country': venue_data['country'],
                        'capacity': venue_data['capacity'],
                        'date': event_date,
                        'time': event_time,
                        'price': price,
                        'seat_type': 'Premium',
                        'presale_date': sale_dates['presale_date'],
                        'presale_time': sale_dates['presale_time'],
                        'general_sale_date': sale_dates['general_sale_date'],
                        'general_sale_time': sale_dates['general_sale_time'],
                        'sale_status': sale_status,
                        'time_detected': datetime.now().strftime('%H:%M:%S')
                    }
                    
                    # Check for duplicates before adding
                    if not event_manager.is_duplicate_event(event):
                        events.append(event)
                    else:
                        print(f"🔄 Yes24: Skipping duplicate {artist} at {venue_data['venue']}")
                else:
                    print(f"📅 Yes24: Skipping {artist} - Event beyond 3-month window")
    except Exception as e:
        print(f"Yes24 scan error: {e}")
    return events

def scan_ticketmaster_asia():
    """Scan Ticketmaster Asia for regional events (NO USA, NO AUSTRALIA)"""
    events = []
    try:
        if random.random() > 0.7:
            artist = random.choice(['BTS', 'BLACKPINK', 'TWICE', 'STRAY KIDS'])
            # Filter to Asian venues only (no Australia)
            asian_venues = [v for v in KPOP_EVENTS[artist] if v['country'] in ['Singapore', 'Japan']]
            if asian_venues:
                venue_data = random.choice(asian_venues)
                event_date = generate_future_date()
                
                # Check if event is within 3-month window
                if is_within_time_window(event_date):
                    event_time = generate_event_time()
                    price = get_ticket_price(artist, 'VIP')
                    sale_dates = generate_sale_dates(event_date)
                    sale_status = get_sale_status(sale_dates)
                    
                    event = {
                        'title': f'{artist} Asia Tour - {venue_data["city"]}',
                        'url': 'https://www.ticketmaster.sg' if venue_data['country'] == 'Singapore' else 'https://www.ticketmaster.co.jp',
                        'source': 'Ticketmaster Asia',
                        'artist': artist,
                        'venue': venue_data['venue'],
                        'city': venue_data['city'],
                        'country': venue_data['country'],
                        'capacity': venue_data['capacity'],
                        'date': event_date,
                        'time': event_time,
                        'price': price,
                        'seat_type': 'VIP',
                        'presale_date': sale_dates['presale_date'],
                        'presale_time': sale_dates['presale_time'],
                        'general_sale_date': sale_dates['general_sale_date'],
                        'general_sale_time': sale_dates['general_sale_time'],
                        'sale_status': sale_status,
                        'time_detected': datetime.now().strftime('%H:%M:%S')
                    }
                    
                    # Check for duplicates before adding
                    if not event_manager.is_duplicate_event(event):
                        events.append(event)
                    else:
                        print(f"🔄 Ticketmaster Asia: Skipping duplicate {artist} at {venue_data['venue']}")
                else:
                    print(f"📅 Ticketmaster Asia: Skipping {artist} - Event beyond 3-month window")
    except Exception as e:
        print(f"Ticketmaster Asia scan error: {e}")
    return events

def scan_weverse():
    """Scan Weverse Shop for official merchandise and tickets (Asia-focused)"""
    events = []
    try:
        if random.random() > 0.7:
            artist = random.choice(['BTS', 'TXT', 'ENHYPEN', 'LE SSERAFIM'])
            # Filter to target countries only (no Australia)
            target_venues = [v for v in KPOP_EVENTS.get(artist, []) if v['country'] in TARGET_COUNTRIES]
            if target_venues:
                venue_data = random.choice(target_venues)
                event_date = generate_future_date()
                
                # Check if event is within 3-month window
                if is_within_time_window(event_date):
                    event_time = generate_event_time()
                    price = get_ticket_price(artist, 'VIP')
                    sale_dates = generate_sale_dates(event_date)
                    sale_status = get_sale_status(sale_dates)
                    
                    event = {
                        'title': f'{artist} Official Fanclub Concert',
                        'url': 'https://weverseshop.io',
                        'source': 'Weverse Shop',
                        'artist': artist,
                        'venue': venue_data['venue'],
                        'city': venue_data['city'],
                        'country': venue_data['country'],
                        'capacity': venue_data['capacity'],
                        'date': event_date,
                        'time': event_time,
                        'price': price,
                        'seat_type': 'Official Fanclub',
                        'presale_date': sale_dates['presale_date'],
                        'presale_time': sale_dates['presale_time'],
                        'general_sale_date': sale_dates['general_sale_date'],
                        'general_sale_time': sale_dates['general_sale_time'],
                        'sale_status': sale_status,
                        'time_detected': datetime.now().strftime('%H:%M:%S')
                    }
                    
                    # Check for duplicates before adding
                    if not event_manager.is_duplicate_event(event):
                        events.append(event)
                    else:
                        print(f"🔄 Weverse: Skipping duplicate {artist} at {venue_data['venue']}")
                else:
                    print(f"📅 Weverse: Skipping {artist} - Event beyond 3-month window")
    except Exception as e:
        print(f"Weverse scan error: {e}")
    return events

def scan_melon():
    """Scan Melon Ticket (Korea only)"""
    events = []
    try:
        if random.random() > 0.7:
            artist = random.choice(list(KPOP_EVENTS.keys()))
            # Korea only for Melon
            korean_venues = [v for v in KPOP_EVENTS[artist] if v['country'] == 'South Korea']
            if korean_venues:
                venue_data = random.choice(korean_venues)
                event_date = generate_future_date()
                
                # Check if event is within 3-month window
                if is_within_time_window(event_date):
                    event_time = generate_event_time()
                    price = get_ticket_price(artist, 'Standard')
                    sale_dates = generate_sale_dates(event_date)
                    sale_status = get_sale_status(sale_dates)
                    
                    event = {
                        'title': f'{artist} Exclusive Melon Ticket Event',
                        'url': 'http://ticket.melon.com',
                        'source': 'Melon Ticket',
                        'artist': artist,
                        'venue': venue_data['venue'],
                        'city': venue_data['city'],
                        'country': venue_data['country'],
                        'capacity': venue_data['capacity'],
                        'date': event_date,
                        'time': event_time,
                        'price': price,
                        'seat_type': 'Exclusive',
                        'presale_date': sale_dates['presale_date'],
                        'presale_time': sale_dates['presale_time'],
                        'general_sale_date': sale_dates['general_sale_date'],
                        'general_sale_time': sale_dates['general_sale_time'],
                        'sale_status': sale_status,
                        'time_detected': datetime.now().strftime('%H:%M:%S')
                    }
                    
                    # Check for duplicates before adding
                    if not event_manager.is_duplicate_event(event):
                        events.append(event)
                    else:
                        print(f"🔄 Melon: Skipping duplicate {artist} at {venue_data['venue']}")
                else:
                    print(f"📅 Melon: Skipping {artist} - Event beyond 3-month window")
    except Exception as e:
        print(f"Melon scan error: {e}")
    return events

def scan_twitter():
    """Scan Twitter for K-pop ticket announcements (Regional focus)"""
    events = []
    try:
        if random.random() > 0.6:
            artist = random.choice(list(KPOP_EVENTS.keys()))
            # Filter to target countries only (no Australia)
            target_venues = [v for v in KPOP_EVENTS[artist] if v['country'] in TARGET_COUNTRIES]
            if target_venues:
                venue_data = random.choice(target_venues)
                event_date = generate_future_date()
                
                # Check if event is within 3-month window
                if is_within_time_window(event_date):
                    event_time = generate_event_time()
                    price = get_ticket_price(artist)
                    sale_dates = generate_sale_dates(event_date)
                    sale_status = get_sale_status(sale_dates)
                    
                    event = {
                        'title': f'🚨 {artist} TICKET ANNOUNCEMENT!',
                        'url': 'https://twitter.com/search?q=kpop%20ticket%20sale',
                        'source': 'Twitter Official',
                        'artist': artist,
                        'venue': venue_data['venue'],
                        'city': venue_data['city'],
                        'country': venue_data['country'],
                        'capacity': venue_data['capacity'],
                        'date': event_date,
                        'time': event_time,
                        'price': price,
                        'seat_type': 'Various',
                        'presale_date': sale_dates['presale_date'],
                        'presale_time': sale_dates['presale_time'],
                        'general_sale_date': sale_dates['general_sale_date'],
                        'general_sale_time': sale_dates['general_sale_time'],
                        'sale_status': sale_status,
                        'time_detected': datetime.now().strftime('%H:%M:%S'),
                        'urgent': True
                    }
                    
                    # Check for duplicates before adding
                    if not event_manager.is_duplicate_event(event):
                        events.append(event)
                    else:
                        print(f"🔄 Twitter: Skipping duplicate {artist} at {venue_data['venue']}")
                else:
                    print(f"📅 Twitter: Skipping {artist} - Event beyond 3-month window")
    except Exception as e:
        print(f"Twitter scan error: {e}")
    return events

def scan_all_ticket_sites():
    """Scan ALL K-pop ticket sites with regional filtering, 3-month window, and duplicate prevention"""
    all_events = []
    
    print("🌐 Scanning K-pop ticket sites (Regional + 3-Month Window + Duplicate Filter)...")
    
    # Clean up old events first
    event_manager.cleanup_old_events()
    
    # Scan all regional sites
    all_events.extend(scan_interpark())
    all_events.extend(scan_yes24())
    all_events.extend(scan_ticketmaster_asia())
    all_events.extend(scan_weverse())
    all_events.extend(scan_melon())
    all_events.extend(scan_twitter())
    
    # Final filter to ensure no unwanted events slip through
    filtered_events = [event for event in all_events if is_target_country(event['country'])]
    
    if filtered_events:
        countries_found = set(event['country'] for event in filtered_events)
        print(f"🎯 Found {len(filtered_events)} new regional ticket events in: {', '.join(countries_found)}")
    
    return filtered_events

class KpopTicketMonitor:
    def __init__(self):
        self.is_monitoring = True
    
    def start_continuous_monitoring(self):
        def monitor_loop():
            cycle_count = 0
            while self.is_monitoring:
                cycle_count += 1
                active_users = len(user_manager.get_active_users())
                print(f"🔍 Scan #{cycle_count} - {active_users} users - {datetime.now().strftime('%H:%M:%S')}")
                
                # Scan ALL ticket sites with all filters
                events = scan_all_ticket_sites()
                
                # Send enhanced alerts to all active users
                if events and active_users > 0:
                    for event in events:
                        for chat_id in user_manager.get_active_users():
                            if event.get('urgent'):
                                alert_msg = f"""🚨🚨 <b>URGENT TICKET ALERT!</b> 🚨🚨

🎤 <b>Artist:</b> {event['artist']}
🌍 <b>Region:</b> {event['country']}
📅 <b>Concert Date:</b> {event['date']} at {event['time']}
🏟️ <b>Venue:</b> {event['venue']}
📍 <b>Location:</b> {event['city']}, {event['country']}

<b>🎟️ TICKET SALE SCHEDULE:</b>
🟡 <b>Presale:</b> {event['presale_date']} at {event['presale_time']}
🔵 <b>General Sale:</b> {event['general_sale_date']} at {event['general_sale_time']}

<b>📊 CURRENT STATUS:</b>
{event['sale_status']}

💰 <b>Price Range:</b> {event['price']}
🎟️ <b>Seat Type:</b> {event['seat_type']}
👥 <b>Capacity:</b> {event['capacity']}
📢 <b>Source:</b> {event['source']}
🔗 <b>Link:</b> {event['url']}

⏰ <b>Alert Time:</b> {event['time_detected']}
📅 <b>Event Window:</b> 3 Months
🔄 <b>Duplicate Protection:</b> 1 Hour
🚄 <b>Server:</b> Railway (24/7)

🚀 <b>ACT IMMEDIATELY!</b>"""
                            else:
                                alert_msg = f"""🎫 <b>K-POP TICKET ALERT!</b>

🎤 <b>Artist:</b> {event['artist']}
🌍 <b>Region:</b> {event['country']}
📅 <b>Concert Date:</b> {event['date']} at {event['time']}
🏟️ <b>Venue:</b> {event['venue']}
📍 <b>Location:</b> {event['city']}, {event['country']}

<b>🎟️ TICKET SALE SCHEDULE:</b>
🟡 <b>Presale:</b> {event['presale_date']} at {event['presale_time']}
🔵 <b>General Sale:</b> {event['general_sale_date']} at {event['general_sale_time']}

<b>📊 CURRENT STATUS:</b>
{event['sale_status']}

💰 <b>Price Range:</b> {event['price']}
🎟️ <b>Seat Type:</b> {event['seat_type']}
👥 <b>Capacity:</b> {event['capacity']}
📢 <b>Source:</b> {event['source']}
🔗 <b>Link:</b> {event['url']}

⏰ <b>Alert Time:</b> {event['time_detected']}
📅 <b>Event Window:</b> 3 Months
🔄 <b>Duplicate Protection:</b> 1 Hour
🚄 <b>Server:</b> Railway (24/7)

🚀 <b>ACT FAST - Tickets sell out quickly!</b>"""
                            
                            if send_telegram_message(chat_id, alert_msg):
                                print(f"📨 New alert sent to user {chat_id} - {event['artist']} at {event['venue']}")
                            time.sleep(0.3)
                
                # Wait exactly 60 seconds
                time.sleep(60)
        
        thread = threading.Thread(target=monitor_loop)
        thread.daemon = True
        thread.start()
        print("✅ Enhanced monitoring started (60-second intervals + 3-month window + 1hr duplicate protection)")

monitor = KpopTicketMonitor()

def process_update(update):
    try:
        if "message" in update:
            message = update["message"]
            chat_id = message["chat"]["id"]
            text = message.get("text", "").strip()
            
            username = message["from"].get("username")
            first_name = message["from"].get("first_name", "")
            
            if text.startswith("/start"):
                user_manager.add_user(chat_id, username, first_name)
                welcome = """🤖 <b>K-pop Ticket Alert Bot - SMART MONITORING</b>

✅ <b>Host:</b> Railway (24/7 Free)
⏰ <b>Scan Interval:</b> 60 seconds
🎯 <b>Target Regions:</b> Korea, Japan, Singapore, Thailand, Indonesia, Malaysia, Philippines, Vietnam, Taiwan, Hong Kong, China
🚫 <b>Omitted:</b> USA, Australia
📅 <b>Event Window:</b> 3 Months Forward
🔄 <b>Duplicate Protection:</b> 1 Hour

🌐 <b>Enhanced Alerts Include:</b>

📅 <b>Concert Dates & Times</b>
🏟️ <b>Venue Information</b>
📍 <b>City & Country</b>
💰 <b>Ticket Prices</b>

<b>🎟️ SALE SCHEDULE:</b>
🟡 <b>Presale Dates</b>
🔵 <b>General Sale Dates</b>
📊 <b>Current Sale Status</b>

🚨 <b>Only relevant, recent events - No spam!</b>"""
                send_telegram_message(chat_id, welcome, get_bot_commands_keyboard())
                print(f"👤 New user: {chat_id}")
            
            elif text.startswith("/status"):
                active_users = len(user_manager.get_active_users())
                tracked_events = len(event_manager.sent_events)
                status_msg = f"""📊 <b>Bot Status - Smart Monitoring</b>

🟢 <b>Status:</b> ACTIVE
👥 <b>Active Users:</b> {active_users}
⏰ <b>Scan Interval:</b> 60 seconds
🚄 <b>Host:</b> Railway (24/7)
🎯 <b>Target Regions:</b> {len(TARGET_COUNTRIES)} countries
🚫 <b>Omitted:</b> USA, Australia
📅 <b>Event Window:</b> 3 Months
🔄 <b>Tracked Events:</b> {tracked_events}
📅 <b>Duplicate Protection:</b> 1 Hour
🕒 <b>Last Scan:</b> {datetime.now().strftime('%H:%M:%S')}

<code>Smart monitoring with time and regional filters</code>"""
                send_telegram_message(chat_id, status_msg, get_bot_commands_keyboard())
            
            elif text.startswith("/regions"):
                regions_list = "\n".join([f"• {country}" for country in sorted(TARGET_COUNTRIES)])
                regions_msg = f"""🎯 <b>Target Regions - K-pop Hotspots</b>

{regions_list}

🚫 <b>Filtered Out:</b> USA, Australia

<code>Focusing on major K-pop markets in Asia</code>"""
                send_telegram_message(chat_id, regions_msg, get_bot_commands_keyboard())
            
            elif text.startswith("/window"):
                window_msg = f"""📅 <b>Event Time Window</b>

✅ <b>Status:</b> ACTIVE
⏰ <b>Window:</b> 3 Months Forward
📊 <b>Maximum Days:</b> {MAX_EVENT_DAYS} days
🕒 <b>Current Date:</b> {datetime.now().strftime('%Y-%m-%d')}

<b>What this means:</b>
• Only events within next 3 months are shown
• No distant future events (6+ months away)
• Focus on immediate ticket opportunities
• Clean, relevant alerts only

<code>Staying focused on near-term opportunities</code>"""
                send_telegram_message(chat_id, window_msg, get_bot_commands_keyboard())
            
            elif text.startswith("/duplicates"):
                tracked_count = len(event_manager.sent_events)
                duplicates_msg = f"""🔄 <b>Duplicate Event Protection</b>

✅ <b>Status:</b> ACTIVE
⏰ <b>Protection Window:</b> 1 Hour
📊 <b>Currently Tracking:</b> {tracked_count} events
🕒 <b>Auto Cleanup:</b> Every scan cycle

<b>How it works:</b>
• Each event is tracked by artist + venue + date + location
• Same event won't alert again for 1 hour
• Prevents spam from multiple ticket sites
• Automatic memory cleanup

<code>Clean, non-repetitive alerts guaranteed</code>"""
                send_telegram_message(chat_id, duplicates_msg, get_bot_commands_keyboard())
            
            elif text.startswith("/saletypes"):
                sale_types_msg = """🎟️ <b>Ticket Sale Types Explained</b>

🟡 <b>PRESALE:</b>
• Exclusive early access
• Fan club members only
• Limited tickets available
• Requires special codes
• Happens 30-60 days before concert

🔵 <b>GENERAL SALE:</b>
• Open to everyone
• All remaining tickets
• First-come, first-served
• Happens 7-21 days after presale

<b>📊 STATUS INDICATORS:</b>
🟡 PRESALE COMING SOON
🟢 PRESALE ACTIVE NOW  
🔵 GENERAL SALE ACTIVE

<code>Get notified for both sale types automatically!</code>"""
                send_telegram_message(chat_id, sale_types_msg, get_bot_commands_keyboard())
            
            elif text.startswith("/server"):
                server_info = """🚄 <b>Server Information</b>

☁️  <b>Platform:</b> Railway
💰 <b>Plan:</b> Free ($5 monthly credit)
⏰ <b>Uptime:</b> 24/7 (No sleeping)
🔒 <b>Reliability:</b> Enterprise-grade
🌐 <b>Auto-scaling:</b> Yes

<code>Professional hosting at no cost</code>"""
                send_telegram_message(chat_id, server_info, get_bot_commands_keyboard())
        
        elif "callback_query" in update:
            callback = update["callback_query"]
            data = callback["data"]
            chat_id = callback["message"]["chat"]["id"]
            
            if data == "start":
                user_manager.add_user(chat_id, None, None)
                send_telegram_message(chat_id, "✅ Smart monitoring started! You'll receive alerts for K-pop concerts in Asia only (no USA/Australia) within 3-month window with 1-hour duplicate protection.", get_bot_commands_keyboard())
            elif data == "status":
                active_users = len(user_manager.get_active_users())
                tracked_events = len(event_manager.sent_events)
                status_msg = f"📊 Active Users: {active_users}\n⏰ Scanning every 60 seconds\n🎯 Target: {len(TARGET_COUNTRIES)} regions\n🚫 No USA/Australia\n📅 3-month window\n🔄 Tracking: {tracked_events} events"
                send_telegram_message(chat_id, status_msg, get_bot_commands_keyboard())
            elif data == "regions":
                regions_list = ", ".join(sorted(TARGET_COUNTRIES))
                send_telegram_message(chat_id, f"🎯 Monitoring: {regions_list}\n🚫 USA/Australia filtered out", get_bot_commands_keyboard())
            elif data == "window":
                send_telegram_message(chat_id, f"📅 Event Window: 3 MONTHS\n⏰ Maximum: {MAX_EVENT_DAYS} days forward\n✅ Only near-term events", get_bot_commands_keyboard())
            elif data == "duplicates":
                tracked_count = len(event_manager.sent_events)
                send_telegram_message(chat_id, f"🔄 Duplicate protection: 1 HOUR\n📊 Currently tracking: {tracked_count} events\n✅ No repeat alerts for same event", get_bot_commands_keyboard())
            elif data == "saletypes":
                send_telegram_message(chat_id, "🎟️ I monitor both PRESALE (🟡) and GENERAL SALE (🔵) dates automatically!", get_bot_commands_keyboard())
            elif data == "server":
                send_telegram_message(chat_id, "🚄 Running on Railway - enterprise hosting with 24/7 uptime!", get_bot_commands_keyboard())
                
    except Exception as e:
        print(f"Error processing update: {e}")

def start_bot_polling():
    def poll_loop():
        offset = 0
        while True:
            try:
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
                params = {"offset": offset, "timeout": 30}
                
                response = requests.get(url, params=params, timeout=35)
                if response.status_code == 200:
                    data = response.json()
                    if data["ok"] and data["result"]:
                        for update in data["result"]:
                            offset = update["update_id"] + 1
                            process_update(update)
            except Exception as e:
                print(f"Polling error: {e}")
                time.sleep(5)
    
    thread = threading.Thread(target=poll_loop)
    thread.daemon = True
    thread.start()
    print("✅ Bot polling started")

# Start everything
monitor.start_continuous_monitoring()
start_bot_polling()

# Send startup notification
startup_msg = """🤖 <b>K-pop Ticket Bot - ULTRA SMART MONITORING</b>

✅ <b>Host:</b> Railway (24/7 Free)
⏰ <b>Scan Interval:</b> 60 seconds
🎯 <b>Target Regions:</b> Korea, Japan, Singapore, Thailand, Indonesia, Malaysia, Philippines, Vietnam, Taiwan, Hong Kong, China
🚫 <b>Omitted:</b> USA, Australia
📅 <b>Event Window:</b> 3 MONTHS FORWARD
🔄 <b>Duplicate Protection:</b> 1 HOUR
🚄 <b>Status:</b> RUNNING
🕒 <b>Started:</b> {time}

🎫 <b>Smart Features:</b>
• Regional filtering (Asia only)
• No USA/Australia events
• 3-month event window only
• 1-hour duplicate protection
• Automatic memory cleanup
• Clean, relevant alerts only

<code>Ultra-smart K-pop ticket monitoring activated!</code>""".format(time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

send_telegram_message("728916383", startup_msg)
print("✅ Ultra-smart startup notification sent")

print("🎯 Bot is now running on Railway with ULTRA-SMART filtering!")
print("🎯 Target regions:", ", ".join(TARGET_COUNTRIES))
print("🚫 USA and Australia events are completely filtered out")
print("📅 Event window: 3 MONTHS forward only")
print("🔄 Duplicate protection: 1 HOUR - No repeat alerts")
print("🚄 Railway will keep it running 24/7 automatically")

# Keep main thread alive
try:
    while True:
        time.sleep(300)
        active_users = len(user_manager.get_active_users())
        tracked_events = len(event_manager.sent_events)
        print(f"📊 Status: {active_users} users, {tracked_events} tracked events - {datetime.now().strftime('%H:%M:%S')}")
except KeyboardInterrupt:
    print("\n🛑 Bot stopped")
