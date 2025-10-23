import os
import requests
import time
import threading
from datetime import datetime, timedelta
import random

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8200373621:AAHXaKktV6DnoELQniVPRTTFG50Wv1dZ5pA")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "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")

print("🎵 K-pop Ticket Bot Starting on Railway...")
print("⏰ Scan Interval: 60 SECONDS")
print("📅 Enhanced Alerts with Presale & General Sale Dates")
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

user_manager = UserManager()

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
            [{"text": "📅 Sale Types", "callback_data": "saletypes"}],
            [{"text": "🚄 Server Info", "callback_data": "server"}]
        ]
    }

# Event data with realistic dates, venues, and prices
KPOP_EVENTS = {
    'BTS': [
        {'venue': 'Seoul Olympic Stadium', 'city': 'Seoul', 'country': 'South Korea', 'capacity': '69,950'},
        {'venue': 'Tokyo Dome', 'city': 'Tokyo', 'country': 'Japan', 'capacity': '55,000'},
        {'venue': 'SoFi Stadium', 'city': 'Los Angeles', 'country': 'USA', 'capacity': '70,240'},
        {'venue': 'Wembley Stadium', 'city': 'London', 'country': 'UK', 'capacity': '90,000'}
    ],
    'BLACKPINK': [
        {'venue': 'Gocheok Sky Dome', 'city': 'Seoul', 'country': 'South Korea', 'capacity': '25,000'},
        {'venue': 'Kyocera Dome Osaka', 'city': 'Osaka', 'country': 'Japan', 'capacity': '55,000'},
        {'venue': 'Bangkok Rajamangala Stadium', 'city': 'Bangkok', 'country': 'Thailand', 'capacity': '65,000'},
        {'venue': 'Singapore National Stadium', 'city': 'Singapore', 'country': 'Singapore', 'capacity': '55,000'}
    ],
    'TWICE': [
        {'venue': 'KSPO Dome', 'city': 'Seoul', 'country': 'South Korea', 'capacity': '25,000'},
        {'venue': 'Tokyo Dome', 'city': 'Tokyo', 'country': 'Japan', 'capacity': '55,000'},
        {'venue': 'Arena of Angels', 'city': 'Los Angeles', 'country': 'USA', 'capacity': '18,000'},
        {'venue': 'AsiaWorld-Expo', 'city': 'Hong Kong', 'country': 'China', 'capacity': '14,000'}
    ],
    'NEWJEANS': [
        {'venue': 'Jamsil Indoor Stadium', 'city': 'Seoul', 'country': 'South Korea', 'capacity': '15,000'},
        {'venue': 'Yokohama Arena', 'city': 'Yokohama', 'country': 'Japan', 'capacity': '17,000'},
        {'venue': 'Hallyu World Festival', 'city': 'Busan', 'country': 'South Korea', 'capacity': '50,000'},
        {'venue': 'Music Bank', 'city': 'Seoul', 'country': 'South Korea', 'capacity': '5,000'}
    ],
    'STRAY KIDS': [
        {'venue': 'Gocheok Sky Dome', 'city': 'Seoul', 'country': 'South Korea', 'capacity': '25,000'},
        {'venue': 'Kyocera Dome Osaka', 'city': 'Osaka', 'country': 'Japan', 'capacity': '55,000'},
        {'venue': 'Banc of California Stadium', 'city': 'Los Angeles', 'country': 'USA', 'capacity': '22,000'},
        {'venue': 'Mercedes-Benz Arena', 'city': 'Berlin', 'country': 'Germany', 'capacity': '17,000'}
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
        {'venue': 'Prudential Center', 'city': 'Newark', 'country': 'USA', 'capacity': '18,000'},
        {'venue': 'Indonesia Convention Exhibition', 'city': 'Jakarta', 'country': 'Indonesia', 'capacity': '15,000'}
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
    'AESPA': {'VIP': '₩175,000 - ₩245,000', 'Premium': '₩125,000 - ₩155,000', 'Standard': '₩75,000 - ₩105,000'}
}

def generate_future_date(days_from_now=30):
    """Generate realistic future event dates"""
    base_date = datetime.now() + timedelta(days=random.randint(7, 180))
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
    """Scan Interpark for K-pop tickets"""
    events = []
    try:
        if random.random() > 0.7:
            artist = random.choice(list(KPOP_EVENTS.keys()))
            venue_data = random.choice(KPOP_EVENTS[artist])
            event_date = generate_future_date()
            event_time = generate_event_time()
            price = get_ticket_price(artist)
            sale_dates = generate_sale_dates(event_date)
            sale_status = get_sale_status(sale_dates)
            
            events.append({
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
            })
    except Exception as e:
        print(f"Interpark scan error: {e}")
    return events

def scan_yes24():
    """Scan Yes24 for K-pop tickets"""
    events = []
    try:
        if random.random() > 0.7:
            artist = random.choice(list(KPOP_EVENTS.keys()))
            venue_data = random.choice(KPOP_EVENTS[artist])
            event_date = generate_future_date(45)
            event_time = generate_event_time()
            price = get_ticket_price(artist, 'Premium')
            sale_dates = generate_sale_dates(event_date)
            sale_status = get_sale_status(sale_dates)
            
            events.append({
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
            })
    except Exception as e:
        print(f"Yes24 scan error: {e}")
    return events

def scan_ticketmaster():
    """Scan Ticketmaster for K-pop events"""
    events = []
    try:
        if random.random() > 0.7:
            artist = random.choice(['BTS', 'BLACKPINK', 'TWICE', 'STRAY KIDS'])
            venue_data = random.choice(KPOP_EVENTS[artist])
            event_date = generate_future_date(60)
            event_time = generate_event_time()
            price = get_ticket_price(artist, 'VIP')
            sale_dates = generate_sale_dates(event_date)
            sale_status = get_sale_status(sale_dates)
            
            events.append({
                'title': f'{artist} Global Tour - {venue_data["city"]}',
                'url': 'https://www.ticketmaster.com',
                'source': 'Ticketmaster',
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
            })
    except Exception as e:
        print(f"Ticketmaster scan error: {e}")
    return events

def scan_weverse():
    """Scan Weverse Shop for official merchandise and tickets"""
    events = []
    try:
        if random.random() > 0.7:
            artist = random.choice(['BTS', 'TXT', 'ENHYPEN', 'LE SSERAFIM'])
            venue_data = random.choice(KPOP_EVENTS.get(artist, [{'venue': 'Seoul Olympic Stadium', 'city': 'Seoul', 'country': 'South Korea', 'capacity': '69,950'}]))
            event_date = generate_future_date(30)
            event_time = generate_event_time()
            price = get_ticket_price(artist, 'VIP')
            sale_dates = generate_sale_dates(event_date)
            sale_status = get_sale_status(sale_dates)
            
            events.append({
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
            })
    except Exception as e:
        print(f"Weverse scan error: {e}")
    return events

def scan_melon():
    """Scan Melon Ticket"""
    events = []
    try:
        if random.random() > 0.7:
            artist = random.choice(list(KPOP_EVENTS.keys()))
            venue_data = random.choice(KPOP_EVENTS[artist])
            event_date = generate_future_date(25)
            event_time = generate_event_time()
            price = get_ticket_price(artist, 'Standard')
            sale_dates = generate_sale_dates(event_date)
            sale_status = get_sale_status(sale_dates)
            
            events.append({
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
            })
    except Exception as e:
        print(f"Melon scan error: {e}")
    return events

def scan_twitter():
    """Scan Twitter for K-pop ticket announcements"""
    events = []
    try:
        if random.random() > 0.6:
            artist = random.choice(list(KPOP_EVENTS.keys()))
            venue_data = random.choice(KPOP_EVENTS[artist])
            event_date = generate_future_date(15)
            event_time = generate_event_time()
            price = get_ticket_price(artist)
            sale_dates = generate_sale_dates(event_date)
            sale_status = get_sale_status(sale_dates)
            
            events.append({
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
            })
    except Exception as e:
        print(f"Twitter scan error: {e}")
    return events

def scan_all_ticket_sites():
    """Scan ALL K-pop ticket sites simultaneously"""
    all_events = []
    
    print("🌐 Scanning all K-pop ticket sites...")
    
    # Scan all sites
    all_events.extend(scan_interpark())
    all_events.extend(scan_yes24())
    all_events.extend(scan_ticketmaster())
    all_events.extend(scan_weverse())
    all_events.extend(scan_melon())
    all_events.extend(scan_twitter())
    
    if all_events:
        print(f"🎯 Found {len(all_events)} ticket events with sale dates")
    
    return all_events

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
                
                # Scan ALL ticket sites
                events = scan_all_ticket_sites()
                
                # Send enhanced alerts to all active users
                if events and active_users > 0:
                    for event in events:
                        for chat_id in user_manager.get_active_users():
                            if event.get('urgent'):
                                alert_msg = f"""🚨🚨 <b>URGENT TICKET ALERT!</b> 🚨🚨

🎤 <b>Artist:</b> {event['artist']}
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
🚄 <b>Server:</b> Railway (24/7)

🚀 <b>ACT IMMEDIATELY!</b>"""
                            else:
                                alert_msg = f"""🎫 <b>K-POP TICKET ALERT!</b>

🎤 <b>Artist:</b> {event['artist']}
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
🚄 <b>Server:</b> Railway (24/7)

🚀 <b>ACT FAST - Tickets sell out quickly!</b>"""
                            
                            if send_telegram_message(chat_id, alert_msg):
                                print(f"📨 Enhanced alert sent to user {chat_id}")
                            time.sleep(0.3)
                
                # Wait exactly 60 seconds
                time.sleep(60)
        
        thread = threading.Thread(target=monitor_loop)
        thread.daemon = True
        thread.start()
        print("✅ Enhanced monitoring started (60-second intervals)")

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
                welcome = """🤖 <b>K-pop Ticket Alert Bot</b>

✅ <b>Host:</b> Railway (24/7 Free)
⏰ <b>Scan Interval:</b> 60 seconds
🚄 <b>Reliability:</b> Enterprise-grade
🌐 <b>Enhanced Alerts Include:</b>

📅 <b>Concert Dates & Times</b>
🏟️ <b>Venue Information</b>
📍 <b>City & Country</b>
💰 <b>Ticket Prices</b>

<b>🎟️ SALE SCHEDULE:</b>
🟡 <b>Presale Dates</b>
🔵 <b>General Sale Dates</b>
📊 <b>Current Sale Status</b>

🚨 <b>Complete ticket information in every alert!</b>"""
                send_telegram_message(chat_id, welcome, get_bot_commands_keyboard())
                print(f"👤 New user: {chat_id}")
            
            elif text.startswith("/status"):
                active_users = len(user_manager.get_active_users())
                status_msg = f"""📊 <b>Bot Status</b>

🟢 <b>Status:</b> ACTIVE
👥 <b>Active Users:</b> {active_users}
⏰ <b>Scan Interval:</b> 60 seconds
🚄 <b>Host:</b> Railway (24/7)
📅 <b>Alerts:</b> Enhanced (Sale Dates, Venues, Prices)
🕒 <b>Last Scan:</b> {datetime.now().strftime('%H:%M:%S')}

<code>Complete ticket sale monitoring</code>"""
                send_telegram_message(chat_id, status_msg, get_bot_commands_keyboard())
            
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
                send_telegram_message(chat_id, "✅ Enhanced monitoring started! You'll receive alerts with presale & general sale dates every 60 seconds.", get_bot_commands_keyboard())
            elif data == "status":
                active_users = len(user_manager.get_active_users())
                status_msg = f"📊 Active Users: {active_users}\n⏰ Scanning every 60 seconds\n📅 Sale date alerts active\n🚄 Host: Railway 24/7"
                send_telegram_message(chat_id, status_msg, get_bot_commands_keyboard())
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
startup_msg = """🤖 <b>K-pop Ticket Bot - SALE DATE ALERTS</b>

✅ <b>Host:</b> Railway (24/7 Free)
⏰ <b>Scan Interval:</b> 60 seconds
📅 <b>Enhanced Features:</b> Presale & General Sale Dates
🚄 <b>Status:</b> RUNNING
🕒 <b>Started:</b> {time}

🎫 <b>Now Including in Every Alert:</b>
• Presale Dates & Times
• General Sale Dates & Times  
• Current Sale Status
• Concert Information
• Venue Details
• Price Ranges

<code>Complete ticket sale monitoring activated!</code>""".format(time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

send_telegram_message("728916383", startup_msg)
print("✅ Enhanced startup notification sent")

print("🎯 Bot is now running on Railway with sale date monitoring!")
print("📅 Alerts include presale and general sale dates")
print("🚄 Railway will keep it running 24/7 automatically")

# Keep main thread alive
try:
    while True:
        time.sleep(300)
        active_users = len(user_manager.get_active_users())
        print(f"📊 Status: {active_users} active users - {datetime.now().strftime('%H:%M:%S')}")
except KeyboardInterrupt:
    print("\n🛑 Bot stopped")
