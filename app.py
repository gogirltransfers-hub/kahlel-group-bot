import os, requests, json, re
from flask import Flask, request, jsonify
app = Flask(__name__)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
D7_API_TOKEN = os.getenv("D7_API_TOKEN")
SHEET_URL = os.getenv("SHEET_WEBHOOK_URL")
D7_NUMBER = "+264817491383"
def log(m): print(m, flush=True)
SESSION = {}
MODELS = ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "llama-3.1-8b-instant"]
CONTACT_PHONE = "+264812086309"
CONTACT_EMAIL = "info@kahlel.co.za"
def should_reveal_contact(msg):
    triggers = ["phone", "number", "contact", "call me", "email", "e-mail", "give me", "pop", "payment proof", "talk to human", "human", "agent", "reach you"]
    return any(k in msg.lower() for k in triggers)
def clean_whatsapp_text(t):
    if not t: return t
    t = re.sub(r'\[([^\]]+)\]\((https?://[^\)]+)\)', r'\2', t)
    t = re.sub(r'\((https://[^\)]+)\)', r'\n\1', t)
    t = re.sub(r'\|---.*', '', t)
    return t.strip()
HIDE_TEXT = "👉 Want to Talk to Live Agent? Just TYPE *Talk to Human* and I'll connect you to Leon live! 🍿"
REVEAL_TEXT = f"📞 Call Leon now: *0812086309* (clickable)"
RESERVE_LINK = "https://www.nam-events.com/explore/movie-magic-under-the-stars"
MEMBERSHIP_LINK = "https://kahlelflix.com/p/1065605/kahlel-flix-membership"
SCHEDULE_LINK = "https://kahlelflix.com/cp/38494/movie-schedule"
CAL_LINKS = {
 "Kahlel AI": "https://cal.com/leon-feris-fvlga3/kahlel-ai-robots-and-voice-ai",
 "GoGirl Afri-Ka Travel": "https://cal.com/leon-feris-fvlga3/afri-ka-tours-coloboration-call",
 "Kahlel Travel": "https://cal.com/leon-feris-fvlga3/afri-ka-tours-coloboration-call",
 "Kahlel Flix": "https://cal.com/leon-feris-fvlga3/outdoor-cinema",
 "Vivid Graphix": "https://cal.com/leon-feris-fvlga3/led-displays",
 "Vivid Display": "https://cal.com/leon-feris-fvlga3/led-displays",
 "Kahlel Group": "https://cal.com/leon-feris-fvlga3/kahlel-ai-robots-and-voice-ai"
}
IMAGE_AI = "https://kahlelwebdesign.co.za/otherImages/Robot2.png"
IMAGE_FLIX = "https://www.kahlelflix.com/photos/Drive.png?469"
IMAGE_TRAVEL = "https://a.kwikweb.co.za/afrikatourstr/otherImages/images1.jpg"
IMAGE_LED = "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=600"

WELCOME = """👉 *Welcome to Kahlel Group!* 👋
1️⃣ 🤖 *Kahlel AI* - Robots & AI Agents
2️⃣ 🎬 *Kahlel Flix* - Movie Under The Stars
3️⃣ ✈️ *Afri-Ka Travel* - Namibia Holidays
4️⃣ 📺 *Vivid Graphix* - LED Screens
Reply 1-4 | Type *MENU* | Type *TALK TO HUMAN* for Leon"""

# --- SATURDAY DOUBLE FEATURE - NEW CONVERTING FLOW ---
FLIX_CLEAN = f"""🎬 *SATURDAY DOUBLE - The Lion King + The Notebook* ✨

💰 *NORMAL:* N$99 for BOTH movies!

💎 *MEMBERSHIP - SAVE EVERY WEEKEND:*
🥈 *Silver* - N$49.50 only (50% OFF) + FREE Popcorn 🍿
👑 *VIP* - N$24.75 only (75% OFF) + FREE Popcorn + FREE Water + Best Beanbags

*This Saturday you save N$74.25 with VIP!*

1️⃣ *Become Member:* {MEMBERSHIP_LINK}
2️⃣ *Book Ticket (N$99 or N$24.75 if VIP):* {RESERVE_LINK}
3️⃣ *Schedule:* {SCHEDULE_LINK}

Popcorn & Beanbags limited - Reply BOOK to reserve!

{HIDE_TEXT}
"""

FLIX_SILVER = f"""🥈 *SILVER MEMBERSHIP - Most Popular*

Pay ONLY N$49.50 per movie (50% OFF normal N$99)
FREE Popcorn every time 🍿
Pays for itself in 2 movies

👉 Join here: {MEMBERSHIP_LINK}
Once you pay, send me proof and I'll reserve your Silver beanbag for Saturday. How many seats?

{HIDE_TEXT}
"""

FLIX_VIP = f"""👑 *VIP MEMBERSHIP - Best Value*

Pay ONLY N$24.75 per movie (75% OFF!)
FREE Popcorn + FREE Water + Best Beanbags
This Saturday: You save N$74.25 instantly!

👉 Join here: {MEMBERSHIP_LINK}
Once you pay, send me proof and I'll instantly upgrade your Saturday ticket to N$24.75 and reserve your beanbag. How many VIP seats?

{HIDE_TEXT}
"""

TRAVEL_CLEAN = f"""*🌵 Namibia Safaris & Beyond - Kahlel Travel*
Sossusvlei Deadvlei | Swakopmund | Etosha | Twyfelfontein Himba | KAZA
*FlyNamibia Partner:* Windhoek Eros > Sossusvlei > Swakop > Twyfelfontein > Ongava > Mokuti > Windhoek (May-Nov)
NEW: Windhoek-Maun & Windhoek-Vic Falls! Naturist and medical safaris SA.
🌐 www.afri-katours.com
📅 *Book Meeting:* https://cal.com/leon-feris-fvlga3/afri-ka-tours-coloboration-call
{HIDE_TEXT}"""

VIVID_CLEAN = f"""*📺 Vivid Graphix - LED Specialists Windhoek, Namibia*
Indoor P1.9 | Outdoor P3.9 IP65 | Stadium P8 | Rental 3x4m + Trusses
Shelf P1.8 COB | Transparent LED | Gobo | Naked Eye 3D Any Size
DRONE FLYING LED Banner 0.6kg/sqm 1600nits 4x8m 5x10m Sale & Hire!
🌐 www.kahlel.co.za
📅 *Book Meeting:* https://cal.com/leon-feris-fvlga3/led-displays
{HIDE_TEXT}"""

AI_CLEAN = f"""*🤖 Kahlel AI - Robots & Voice Agents*
🌐 www.kahlel-ai.com
🤖 Service Robots: Hotel, Restaurant
🗣️ *Voice AI:* Inbound/Outbound, 24/7, Multilingual
💼 Demo & Pricing
📅 *Book Meeting:* {CAL_LINKS['Kahlel AI']}
{HIDE_TEXT}"""

MENUS_TEXT = {"1": AI_CLEAN, "2": FLIX_CLEAN, "3": TRAVEL_CLEAN, "4": VIVID_CLEAN}
MENUS_IMAGE = {"1": IMAGE_AI, "2": IMAGE_FLIX, "3": IMAGE_TRAVEL, "4": IMAGE_LED}
BANNED = "CRITICAL: NEVER mention cleaning services, house cleaning, maintenance, janitorial. Kahlel Group DOES NOT OFFER cleaning. ONLY 4 services: 1) Kahlel AI Robots & Voice AI 2) Kahlel Flix Movie Under Stars 3) Afri-Ka Travel Namibia 4) Vivid Graphix LED. If unsure show MENU 1-4."
PROMPTS = {
 "Kahlel AI": f"{BANNED} You are Kahlel AI ONLY. Robots AMY ALICE TIMO SNOW + Retell Voice AI. Meeting {CAL_LINKS['Kahlel AI']}. Default {HIDE_TEXT}. Reveal {CONTACT_PHONE} only if asked. Plain URLs only.",
 "Kahlel Flix": f"{BANNED} You are Kahlel Flix ONLY. 2 PACKAGES ONLY: Silver 50% discount N$49.50 free popcorn, VIP 75% discount N$24.75 popcorn water best seats. Normal N$99 double feature. Membership {MEMBERSHIP_LINK} Schedule {SCHEDULE_LINK} Booking {RESERVE_LINK}. Plain URLs only. Default {HIDE_TEXT}.",
 "GoGirl Afri-Ka Travel": f"{BANNED} You are GoGirl Afri-Ka Travel ONLY. FlyNamibia Circuit Windhoek Eros > Sossusvlei > Swakop > Twyfelfontein > Ongava > Mokuti May-Nov + Windhoek-Maun + Windhoek-Vic Falls + Naturist and medical safaris SA + Classic 9 days. Plain URLs only. Cal {CAL_LINKS
