import os, requests, json, re
from flask import Flask, request, jsonify
app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
D7_API_TOKEN = os.getenv("D7_API_TOKEN")
SHEET_URL = os.getenv("SHEET_WEBHOOK_URL")
D7_NUMBER = "+264817491383"

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

HIDE_TEXT = "👉 Want to Talk to Human? Just TYPE 'Talk to Human' and I'll connect you to Leon live!"
REVEAL_TEXT = f"📞 Leon: {CONTACT_PHONE} / {CONTACT_EMAIL}"
RESERVE_LINK = "https://kahlelflix.com/products"

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

Reply 1-4 | Type *MENU* | Type *TALK TO HUMAN* for Leon
Reply MEETING to book"""

MENUS_TEXT = {
 "1": f"""*🤖 Kahlel AI - Robots & Voice Agents*
🌐 www.kahlel-ai.com
🤖 Service Robots: Hotel, Restaurant, Cleaning
🗣️ *Voice AI:* Inbound/Outbound, 24/7, Multilingual
💼 Demo & Pricing
📅 *Book Meeting:* {CAL_LINKS['Kahlel AI']}
{HIDE_TEXT}""",
 "2": f"""*🎬 Kahlel Flix - Movie Under The Stars* ✨
🍿 What's On? Check live: https://kahlelflix.com/cp/38494/movie-schedule
🎟️ Normal Ticket *N$55* | 🥈 Silver *N$390/y = N$27.50 + FREE popcorn* | 👑 VIP *N$490/y = N$13.75 + popcorn & soda + best seats*
Book: {RESERVE_LINK}
📅 *Book Meeting:* {CAL_LINKS['Kahlel Flix']}
{HIDE_TEXT}""",
 "3": f"""*🌵 Namibia Safaris & Beyond - Kahlel Travel*
Sossusvlei Deadvlei | Swakopmund | Etosha | Twyfelfontein Himba | KAZA
*FlyNamibia Partner:* Windhoek Eros > Sossusvlei > Swakop > Twyfelfontein > Ongava > Mokuti > Windhoek (May-Nov)
NEW: Windhoek-Maun & Windhoek-Vic Falls!
🌐 www.afri-katours.com
📅 *Book Meeting:* {CAL_LINKS['Kahlel Travel']}
{HIDE_TEXT}""",
 "4": f"""*📺 Vivid Graphix - LED Specialists Windhoek, Namibia*
Indoor P1.9 | Outdoor P3.9 IP65 | Stadium P8 | Rental 3x4m + Trusses
Shelf P1.8 COB | Transparent LED | Gobo | Naked Eye 3D Any Size
DRONE FLYING LED Banner 0.6kg/sqm 1600nits 4x8m 5x10m Sale & Hire!
📅 *Book Meeting:* {CAL_LINKS['Vivid Display']}
{HIDE_TEXT}""",
}

MENUS_IMAGE = {"1": IMAGE_AI, "2": IMAGE_FLIX, "3": IMAGE_TRAVEL, "4": IMAGE_LED}

PROMPTS = {
 "Kahlel AI": f"ONLY Kahlel AI. Robots AMY ALICE TIMO SNOW SCUD PANDA + Retell Voice AI for hotels airports malls. Meeting {CAL_LINKS['Kahlel AI']}. Default {HIDE_TEXT}. Reveal phone {CONTACT_PHONE} only if asked. Outdoor=LED type not hiking. Never mention Flix travel LED. Plain URLs only, NO markdown links, NO tables.",
 "Kahlel Flix": f"ONLY Kahlel Flix Movie Under Stars. ONLY 2 PACKAGES: 55 Silver R390/year 55 tickets N$27.50 free popcorn save N$3,120 and 55 VIP R490/year 55 tickets N$13.75 popcorn soda best seats save N$8,415. Normal N$55. NEVER 1500 2500 4000 discontinued. Schedule: https://kahlelflix.com/cp/38494/movie-schedule . Booking: https://kahlelflix.com/products . EFT FNB Name Kahlel Flix Holder John Meinhert Acc 64279815319 Branch 282273 Ref Name+Plan. Send POP via Talk to Human. Plain URLs only, NO tables. Default {HIDE_TEXT}. Reveal {CONTACT_PHONE} only if asked.",
 "GoGirl Afri-Ka Travel": f"ONLY Afri-Ka Travel. Namibia Sossusvlei Swakop Etosha + FlyNamibia circuit Windhoek Eros Sossusvlei Swakop Twyfelfontein Ongava Mokuti May-Nov min2 Westair + new Windhoek-Maun Okavango + Windhoek-Vic Falls + Naturist SunEden + Medical Tourism Facelift Tummy Tuck etc. Default {HIDE_TEXT}. Reveal {CONTACT_PHONE} only if asked. Plain URLs only, NO tables. Cal {CAL_LINKS['GoGirl Afri-Ka Travel']}.",
 "Vivid Graphix": f"ONLY Vivid Graphix LED. LED hire sales repair. Products Indoor P1.9 Outdoor P3.9 IP65 Stadium P8 Rental 3x4m truss Shelf P1.8 COB Transparent 70% Gobo 40W-1500W Drone Flying LED 0.6kg/sqm 1600 nits 4x8m 5x10m sale hire Naked Eye 3D L-shaped. Default {HIDE_TEXT}. Reveal {CONTACT_PHONE} only if asked. Plain URLs only, NO tables. Cal {CAL_LINKS['Vivid Graphix']}.",
 "Kahlel Group": f"General helper Ask 1-4. Default {HIDE_TEXT}. Reveal {CONTACT_PHONE} only if asks phone. Plain URLs only."
}

def groq_reply(msg, last=None):
    low=msg.lower()
    # V20.0 FIX: If last session is set, KEEP IT - don't override to Flix!
    if last and last != "Kahlel Group":
        service = last
    else:
        service="Kahlel Group"
        if any(k in low for k in ["flix", "movie", "silver", "vip"]): service="Kahlel Flix"
        elif any(k in low for k in ["ai", "robot", "voice agent", "demo"]): service="Kahlel AI"
        elif any(k in low for k in ["travel","afri-ka","afri ka","holiday","namibia","sossusvlei","etosha","swakop","flynamibia","safari"]): service="GoGirl Afri-Ka Travel"
        elif any(k in low for k in ["vivid", "led", "display", "screen", "gobo", "drone banner", "p1.9", "p3.9"]): service="Vivid Graphix"
    
    sys_prompt=PROMPTS.get(service, PROMPTS["Kahlel Group"]) + f" STRICT phone {CONTACT_PHONE} email {CONTACT_EMAIL}."
    date=""; m=re.search(r'(\d{1,2}.*(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*|tomorrow|today)', low)
    if m: date=m.group(1)
    extracted={"service":service,"date":date}; smart=None
    try:
        from groq import Groq; client=Groq(api_key=GROQ_API_KEY)
        for MODEL in MODELS:
            try: 
                c=client.chat.completions.create(model=MODEL, messages=[{"role":"system","content":sys_prompt},{"role":"user","content":msg}], max_tokens=350, temperature=0.3)
                smart=c.choices[0].message.content
                smart=clean_whatsapp_text(smart)
                break
            except: continue
    except: pass
    return extracted, smart

def save_full(phone, service, name, date, location, people, message, lead_type="Prospect"):
    try: requests.post(SHEET_URL, json={"phone":phone,"service":service,"name":name,"date":date,"location":location,"people":people,"message":message,"lead_type":lead_type,"cal_link":CAL_LINKS.get(service,"")}, timeout=10)
    except: pass

def send_text(to, text):
    try:
        text=clean_whatsapp_text(text)
        to_clean="+"+str(to).strip().lstrip("+"); url="https://api.d7networks.com/whatsapp/v2/send"; headers={"Authorization": f"Bearer {D7_API_TOKEN}", "Content-Type":"application/json"}
        payload={"messages":[{"originator":D7_NUMBER,"content":{"message_type":"TEXT","text":{"body":text[:1000]}},"recipients":[{"recipient":to_clean,"recipient_type":"individual"}]}]}
        requests.post(url, headers=headers, json=payload, timeout=15)
    except: pass

def send_image(to, image_url, caption):
    to_clean="+"+str(to).strip().lstrip("+"); url="https://api.d7networks.com/whatsapp/v2/send"; headers={"Authorization": f"Bearer {D7_API_TOKEN}", "Content-Type":"application/json"}
    caption=clean_whatsapp_text(caption)
    payload={"messages":[{"originator":D7_NUMBER,"content":{"message_type":"ATTACHMENT","attachment":{"type":"image","url": image_url,"caption": caption[:900]}},"recipients":[{"recipient":to_clean,"recipient_type":"individual"}]}]}
    try:
        r=requests.post(url, headers=headers, json=payload, timeout=15)
        if r.status_code != 200: send_text(to, f"{caption}")
    except: send_text(to, f"{caption}")

@app.route("/webhook", methods=["POST","GET"])
def webhook():
    if request.method=="GET": return f"V20.0 ALL SERVICES FIXED {RESERVE_LINK}",200
    raw=request.get_data(as_text=True); data=json.loads(raw) if raw else {}
    sender=""; msg=""
    if "event_content" in data:
        m=data["event_content"].get("message",{}); sender=m.get("originator",""); txt=m.get("text",{}); msg=txt.get("body","") if isinstance(txt,dict) else str(txt)
        # Facebook may send attachments - get title
        if not msg and "attachments" in m:
            try: msg = m["attachments"][0].get("title","") or m["attachments"][0].get("url","")
            except: pass
    if not sender or not msg:
        # Try alternative Facebook structure
        try:
            if "entry" in data: # Facebook native
                sender = data["entry"][0]["messaging"][0]["sender"]["id"]
                msg = data["entry"][0]["messaging"][0]["message"].get("text","")
        except: pass
    if not sender or not msg: return jsonify({"status":"ignored"}),200

    sender="+"+str(sender).strip().lstrip("+"); low=msg.lower().strip()
    raw_low = raw.lower()

    # ===== V20.0 UNIVERSAL FACEBOOK DETECTOR - THIS FIXES ALL =====
    # Check FULL raw payload for service hints (Facebook ad title is in raw)
    if any(k in raw_low for k in ["afri-ka tours", "afri-ka travel", "sossusvlei", "skip long drives", "flynamibia circuit", "etosha", "namibia holiday", "swakopmund"]):
        SESSION[sender] = "GoGirl Afri-Ka Travel"
    elif any(k in raw_low for k in ["vivid graphix", "led specialists", "led displays", "p1.9", "p3.9", "drone flying led", "naked eye 3d", "kahlel.co.za"]):
        SESSION[sender] = "Vivid Graphix"
    elif any(k in raw_low for k in ["kahlel ai", "service robots", "voice agents", "alpha robotics", "robot2.png", "kahlel-ai.com"]):
        SESSION[sender] = "Kahlel AI"
    elif any(k in raw_low for k in ["kahlel flix", "movie under the stars", "drive.png", "kahlelflix.com"]):
        # Only set Flix if NOT already set to other service
        if SESSION.get(sender) not in ["GoGirl Afri-Ka Travel", "Vivid Graphix", "Kahlel AI"]:
            SESSION[sender] = "Kahlel Flix"

    if any(k in low for k in ["book meeting","appointment","book a meeting","book call","cal.com","consultation","meeting","schedule call","meet you","speak to leon"]):
        service = SESSION.get(sender, "Kahlel Group"); cal_link = CAL_LINKS.get(service, CAL_LINKS["Kahlel Group"]); save_full(sender, service+" - WANTS MEETING", "", "", "", "", msg, lead_type="HOT - Wants Meeting"); send_text(sender, f"📅 Let's meet! Book here:\n👉 {cal_link}\nFor {service}\n{HIDE_TEXT if not should_reveal_contact(msg) else REVEAL_TEXT}"); return jsonify({"status":"sent"}),200

    if any(k in low for k in ["reserve ticket","book ticket","booking link","products"]):
        if SESSION.get(sender) != "Kahlel Flix": # Don't override if already travel etc
            SESSION[sender]="Kahlel Flix"
        save_full(sender, "Kahlel Flix - Reserve", "", "", "", "", msg, "HOT - Reserve"); send_image(sender, IMAGE_FLIX, f"🎟️ Reserve in 30 sec! 👇\nBook: {RESERVE_LINK}\n📅 Meet: {CAL_LINKS['Kahlel Flix']}\n{HIDE_TEXT}"); return jsonify({"status":"sent"}),200

    if any(k in low for k in ["silver","vip","membership","member","join club","package","packages","price","pricing","how much"]):
        # Only trigger packages if session is Flix or no session
        if SESSION.get(sender, "Kahlel Flix") == "Kahlel Flix" or SESSION.get(sender) is None:
            SESSION[sender]="Kahlel Flix"
            nice_packages = f"""🎬 *Kahlel Flix - Packages (Only 2)* ✨

🥈 *55 Silver - R390/year*
- 55 Tickets
- N$27.50 per movie (was N$55)
- FREE popcorn every movie 🍿
- Save N$3,120/year 💰

👑 *55 VIP - R490/year*
- 55 Tickets  
- N$13.75 per movie (75% OFF!)
- Popcorn & soda + best seats 🥤
- Save N$8,415/year 💰💰

🎟️ *Normal Ticket: N$55*

📅 What's On?
https://kahlelflix.com/cp/38494/movie-schedule

🎟️ Book here:
{RESERVE_LINK}

{HIDE_TEXT}"""
            save_full(sender, "Kahlel Flix - Packages", "", "", "", "", msg, "HOT - Packages")
            send_text(sender, nice_packages)
            return jsonify({"status":"sent"}),200

    MONTHS=["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]; has_month=any(x in low for x in MONTHS)
    is_booking=len(msg.split())>=2 and (has_month or any(k in low for k in ["book","tomorrow","today","name","from","people","am","pm","airport","demo"]) or SESSION.get(sender))
    if is_booking:
        extracted, smart=groq_reply(msg, SESSION.get(sender)); SESSION[sender]=extracted["service"]; save_full(sender, extracted["service"], "", extracted["date"] or msg, "", "", msg, "Prospect")
        if should_reveal_contact(msg): smart = (smart or "") + f"\n\n{REVEAL_TEXT}"
        send_text(sender, smart or f"Got it! {extracted['service']} {HIDE_TEXT}")
    elif low in ["1","2","3","4"]:
        mapping={"1":"Kahlel AI","2":"Kahlel Flix","3":"GoGirl Afri-Ka Travel","4":"Vivid Graphix"}; sm=mapping[low]; SESSION[sender]=sm; save_full(sender, sm, "", "", "", "", f"Pressed {low}", "Cold - Browsing"); send_image(sender, MENUS_IMAGE[low], MENUS_TEXT[low])
    elif low in ["hello","hi","menu","start","welcome"]:
        # If we already detected service from Facebook ad, DON'T reset to welcome!
        if SESSION.get(sender) and SESSION.get(sender) != "Kahlel Group":
            extracted, smart=groq_reply(msg, SESSION.get(sender))
            send_text(sender, smart or MENUS_TEXT.get({"Kahlel AI":"1","Kahlel Flix":"2","GoGirl Afri-Ka Travel":"3","Vivid Graphix":"4"}.get(SESSION.get(sender),"2"), WELCOME))
        else:
            SESSION.pop(sender, None); send_text(sender, WELCOME)
    else:
        _, smart=groq_reply(msg, SESSION.get(sender))
        if should_reveal_contact(msg): smart = (smart or "") + f"\n\n{REVEAL_TEXT}"
        else:
            if CONTACT_PHONE in (smart or ""): smart = smart.replace(CONTACT_PHONE, "").replace(CONTACT_EMAIL, "") + f"\n\n{HIDE_TEXT}"
        send_text(sender, smart or WELCOME)
    return jsonify({"status":"sent"}),200

@app.route("/")
def home(): return f"V20.0 FIXED READY {CONTACT_PHONE}"
@app.route("/health")
def health(): return jsonify({"model":MODELS[0],"contact":CONTACT_PHONE,"cal":CAL_LINKS})

if __name__=="__main__": app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
