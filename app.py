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

# V19.9 SMART HYBRID - CONTACTS HIDDEN UNLESS ASKED
CONTACT_PHONE = "+264812086309"
CONTACT_EMAIL = "info@kahlel.co.za"
HIDDEN_MODE = True

def should_reveal_contact(msg):
    triggers = ["phone", "number", "contact", "call me", "email", "e-mail", "give me", "pop", "payment proof", "talk to human", "human", "agent", "reach you"]
    return any(k in msg.lower() for k in triggers)

REVEAL_TEXT = f"📞 Reach Leon: {CONTACT_PHONE} / {CONTACT_EMAIL}\n📅 Book: Talk to Human button - I'll connect with transcript!"
HIDE_TEXT = "👉 Want to Talk to Human? Click Talk to Human and I'll connect you to Leon live with full chat history!"
RESERVE_LINK = "https://kahlelflix.com/products"

CAL_LINKS = {
 "Kahlel AI": "https://cal.com/leon-feris-fvlga3/kahlel-ai-robots-and-voice-ai",
 "GoGirl Afri-Ka Travel": "https://cal.com/leon-feris-fvlga3/afri-ka-tours-coloboration-call",
 "Kahlel Flix": "https://cal.com/leon-feris-fvlga3/outdoor-cinema",
 "Vivid Graphix": "https://cal.com/leon-feris-fvlga3/led-displays",
 "Kahlel Group": "https://cal.com/leon-feris-fvlga3/kahlel-ai-robots-and-voice-ai"
}

IMAGE_AI = "https://kahlelwebdesign.co.za/otherImages/Robot2.png"
IMAGE_FLIX = "https://www.kahlelflix.com/photos/Drive.png?469"
IMAGE_TRAVEL = "https://a.kwikweb.co.za/afrikatourstr/otherImages/images1.jpg"
IMAGE_LED = "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=600"

WELCOME = """👉Welcome to Kahlel Group! 👋
1️⃣ 🤖 Kahlel AI - Robots & AI Agents
2️⃣ 🎬 Kahlel Flix - Movie Under The Stars
3️⃣ ✈️ Afri-Ka Travel - Namibia Holidays
4️⃣ 📺 Vivid Graphix - LED Screens

Reply 1-4 | Type MENU | Type TALK TO HUMAN for Leon
Reply MEETING to book"""

MENUS_TEXT = {
 "1": f"""🤖 Kahlel AI - We Build The Future
We sell Alpha Robotics: AMY ALICE TIMO SNOW SCUD PANDA + Retell Voice AI Agents.
For hotels, airports, malls, warehouse. AI Consulting & WhatsApp bots.
Type DEMO + your business name.
📅 Book Meeting: {CAL_LINKS['Kahlel AI']}
{HIDE_TEXT}
Reply Menu""",
 "2": f"""🎬 Kahlel Flix - Movie Under The Stars ✨
🍿 What's On? Check live: https://kahlelflix.com/cp/38494/movie-schedule
📦 Small N$1500 | Medium N$2500 | Large N$4000
🎟️ Normal N$55 | Silver N$390= N$27.50+popcorn | VIP N$490= N$13.75+best seats
Book: {RESERVE_LINK}
📅 Book Meeting: {CAL_LINKS['Kahlel Flix']}
{HIDE_TEXT}""",
 "3": f"""✈️ Afri-Ka Travel - See Namibia First! 🇳🇦
afri-katours.com
🌵 Sossusvlei Deadvlei | Swakopmund | Etosha | Twyfelfontein Himba | KAZA
FlyNamibia Partner: Windhoek Eros > Sossusvlei > Swakop > Twyfelfontein > Ongava > Mokuti > Windhoek (May-Nov). NEW: Windhoek-Maun Okavango & Windhoek-Vic Falls!
Partners: Naturist Safaris SA + Surgical Bliss SA Facelift Tummy Tuck Breast Rhinoplasty Mommy Makeover
Send FROM-TO + Date + People
📅 Book: {CAL_LINKS['GoGirl Afri-Ka Travel']}
{HIDE_TEXT}""",
 "4": f"""📺 Vivid Graphix - LED Specialists Windhoek
1 Indoor P1.9 2 Outdoor P3.9 IP65 3 Stadium P8 4 Rental 3x4m with trusses signature 5 Shelf LED P1.8 COB 6 Transparent 70% 7 Gobo 40W-1500W 8 DRONE FLYING LED - One drone lightweight flexible mesh LED banner 0.6kg/sqm 1600 nits 360° 4x8m 5x10m sale & hire 9 Naked Eye 3D L-shaped
Tell Indoor/Outdoor + Size?
📅 Book: {CAL_LINKS['Vivid Graphix']}
{HIDE_TEXT}"""
}

MENUS_IMAGE = {"1": IMAGE_AI, "2": IMAGE_FLIX, "3": IMAGE_TRAVEL, "4": IMAGE_LED}

PROMPTS = {
 "Kahlel AI": f"ONLY Kahlel AI. Sell Alpha Robotics AMY ALICE TIMO SNOW SCUD PANDA + Retell Voice. Hotels airports malls. Meeting {CAL_LINKS['Kahlel AI']}. Default {HIDE_TEXT}. Reveal phone {CONTACT_PHONE} only if user asks phone. Outdoor word = LED type not hiking. Never mention Flix travel LED.",
 "Kahlel Flix": f"ONLY Kahlel Flix. Movie Under Stars packages 1500/2500/4000 tickets 55 Silver 390 VIP 490. Whats On always say check https://kahlelflix.com/cp/38494/movie-schedule friendly. EFT FNB Name Kahlel Flix Holder John Meinhert Acc 64279815319 Branch 282273 Ref Name+Plan. Send POP via Talk to Human. Book {RESERVE_LINK}. Default {HIDE_TEXT}. Reveal {CONTACT_PHONE} only if asked.",
 "GoGirl Afri-Ka Travel": f"ONLY Afri-Ka Travel. Namibia Sossusvlei Swakop Etosha + FlyNamibia circuit Windhoek Eros Sossusvlei Swakop Twyfelfontein Ongava Mokuti May-Nov min2 Westair + new Windhoek-Maun Okavango + Windhoek-Vic Falls + Naturist SunEden Kruger clothes-free private + Medical Tourism Facelift Tummy Tuck Breast Rhinoplasty Mommy Makeover Skype all-inclusive HPCSA. Default {HIDE_TEXT}. Reveal {CONTACT_PHONE} only if asked. Cal {CAL_LINKS['GoGirl Afri-Ka Travel']}.",
 "Vivid Graphix": f"ONLY Vivid LED. LED hire sales repair. Outdoor indoor alone = LED TYPE never hiking. Products Indoor Outdoor Stadium Rental 3x4m truss Shelf COB Transparent 70% Gobo 40W-1500W Drone Flying LED one drone lightweight mesh 0.6kg/sqm 1600 nits 4x8m 5x10m sale hire pilot Naked Eye 3D L-shaped. Default {HIDE_TEXT}. Reveal {CONTACT_PHONE} only if asked. Cal {CAL_LINKS['Vivid Graphix']}.",
 "Kahlel Group": f"General helper Ask 1-4. Default {HIDE_TEXT}. Reveal {CONTACT_PHONE} only if asks phone. Outdoor means LED type. Never +27 12 345 678."
}

def groq_reply(msg, last=None):
    low=msg.lower(); service=last or "Kahlel Group"
    if "flix" in low or "movie" in low or "silver" in low or "vip" in low: service="Kahlel Flix"
    elif "ai" in low or "robot" in low or "demo" in low: service="Kahlel AI"
    elif any(k in low for k in ["travel","afri-ka","holiday","namibia","sossusvlei","etosha"]): service="GoGirl Afri-Ka Travel"
    elif "vivid" in low or "led" in low or "indoor" in low: service="Vivid Graphix"
    sys_prompt=PROMPTS.get(service, PROMPTS["Kahlel Group"]) + f" STRICT phone {CONTACT_PHONE} email {CONTACT_EMAIL}."
    date=""; m=re.search(r'(\d{1,2}.*(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*|tomorrow|today)', low)
    if m: date=m.group(1)
    extracted={"service":service,"date":date}; smart=None
    try:
        from groq import Groq; client=Groq(api_key=GROQ_API_KEY)
        for MODEL in MODELS:
            try: c=client.chat.completions.create(model=MODEL, messages=[{"role":"system","content":sys_prompt},{"role":"user","content":msg}], max_tokens=350, temperature=0.4); smart=c.choices[0].message.content; break
            except: continue
    except: pass
    return extracted, smart

def save_full(phone, service, name, date, location, people, message, lead_type="Prospect"):
    try: requests.post(SHEET_URL, json={"phone":phone,"service":service,"name":name,"date":date,"location":location,"people":people,"message":message,"lead_type":lead_type,"cal_link":CAL_LINKS.get(service,"")}, timeout=10)
    except: pass

def send_text(to, text):
    try:
        to_clean="+"+str(to).strip().lstrip("+"); url="https://api.d7networks.com/whatsapp/v2/send"; headers={"Authorization": f"Bearer {D7_API_TOKEN}", "Content-Type":"application/json"}
        payload={"messages":[{"originator":D7_NUMBER,"content":{"message_type":"TEXT","text":{"body":text[:1000]}},"recipients":[{"recipient":to_clean,"recipient_type":"individual"}]}]}
        requests.post(url, headers=headers, json=payload, timeout=15)
    except: pass

def send_image(to, image_url, caption):
    to_clean="+"+str(to).strip().lstrip("+"); url="https://api.d7networks.com/whatsapp/v2/send"; headers={"Authorization": f"Bearer {D7_API_TOKEN}", "Content-Type":"application/json"}
    payload={"messages":[{"originator":D7_NUMBER,"content":{"message_type":"ATTACHMENT","attachment":{"type":"image","url": image_url,"caption": caption[:900]}},"recipients":[{"recipient":to_clean,"recipient_type":"individual"}]}]}
    try:
        r=requests.post(url, headers=headers, json=payload, timeout=15)
        if r.status_code != 200: send_text(to, f"{caption}")
    except: send_text(to, f"{caption}")

@app.route("/webhook", methods=["POST","GET"])
def webhook():
    if request.method=="GET": return f"V19.9 SMART HYBRID {RESERVE_LINK}",200
    raw=request.get_data(as_text=True); data=json.loads(raw) if raw else {}
    sender=""; msg=""
    if "event_content" in data:
        m=data["event_content"].get("message",{}); sender=m.get("originator",""); txt=m.get("text",{}); msg=txt.get("body","") if isinstance(txt,dict) else str(txt)
    if not sender or not msg: return jsonify({"status":"ignored"}),200
    sender="+"+str(sender).strip().lstrip("+"); low=msg.lower().strip()

    if any(k in low for k in ["book meeting","appointment","book a meeting","book call","cal.com","consultation","meeting","schedule call","meet you","speak to leon"]):
        service = SESSION.get(sender, "Kahlel Group")
        cal_link = CAL_LINKS.get(service, CAL_LINKS["Kahlel Group"])
        save_full(sender, service+" - WANTS MEETING", "", "", "", "", msg, lead_type="HOT - Wants Meeting")
        send_text(sender, f"📅 Let's meet! Book here:\n👉 {cal_link}\nFor {service}\n{HIDE_TEXT if not should_reveal_contact(msg) else REVEAL_TEXT}")
        return jsonify({"status":"sent"}),200

    if any(k in low for k in ["reserve ticket","book ticket","reserve","booking link","products"]):
        SESSION[sender]="Kahlel Flix"; save_full(sender, "Kahlel Flix - Reserve", "", "", "", "", msg, "HOT - Reserve"); send_image(sender, IMAGE_FLIX, f"🎟️ Reserve in 30 sec! 👇\nBook: {RESERVE_LINK}\n📅 Meet: {CAL_LINKS['Kahlel Flix']}\n{HIDE_TEXT}"); return jsonify({"status":"sent"}),200

    if any(k in low for k in ["silver","vip","membership","member","join club"]):
        SESSION[sender]="Kahlel Flix"
        if "vip" in low: save_full(sender, "Kahlel Flix - VIP", "", "", "", "", msg, "HOT - VIP"); send_image(sender, IMAGE_FLIX, f"👑 VIP N$490/y Saves N$8,415/y! Book: {RESERVE_LINK}\nMeet: {CAL_LINKS['Kahlel Flix']}\n{HIDE_TEXT}")
        elif "silver" in low: save_full(sender, "Kahlel Flix - SILVER", "", "", "", "", msg, "HOT - Silver"); send_image(sender, IMAGE_FLIX, f"🥈 Silver N$390/y = N$27.50 + FREE popcorn Save N$3,120\nBook: {RESERVE_LINK}\nMeet: {CAL_LINKS['Kahlel Flix']}\n{HIDE_TEXT}")
        else: send_image(sender, IMAGE_FLIX, f"We have 2 plans! 🥈 SILVER N$390 Save N$3,120 👑 VIP N$490 Save N$8,415 Reserve: {RESERVE_LINK} Meet: {CAL_LINKS['Kahlel Flix']}")
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
        SESSION.pop(sender, None); send_text(sender, WELCOME)
    else:
        _, smart=groq_reply(msg, SESSION.get(sender))
        if should_reveal_contact(msg):
            smart = (smart or "") + f"\n\n{REVEAL_TEXT}"
        else:
            if CONTACT_PHONE in (smart or ""):
                smart = smart.replace(CONTACT_PHONE, "").replace(CONTACT_EMAIL, "") + f"\n\n{HIDE_TEXT}"
        send_text(sender, smart or WELCOME)
    return jsonify({"status":"sent"}),200

@app.route("/")
def home(): return f"V19.9 SMART HYBRID READY {CONTACT_PHONE}"
@app.route("/health")
def health(): return jsonify({"model":MODELS[0],"contact":CONTACT_PHONE,"cal":CAL_LINKS})

if __name__=="__main__": app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
