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

RESERVE_LINK = "https://kahlelflix.com/products"
WEBSITE_FLIX = "https://kahlelflix.com"

# YOUR REAL IMAGES - FINAL
IMAGE_AI = "https://kahlelwebdesign.co.za/otherImages/Robot2.png"
IMAGE_FLIX = "https://www.kahlelflix.com/photos/Drive.png?469"
IMAGE_TRAVEL = "https://a.kwikweb.co.za/afrikatourstr/otherImages/images1.jpg"
IMAGE_LED = "https://kahlel.co.za/photos/ledpic3.jpg?685"

WELCOME = """👉Welcome to Kahlel Group! 👋
1️⃣ 🤖 Kahlel AI - Robots & AI Agents
2️⃣ 🎬 Kahlel Flix - Movie Under The Stars
3️⃣ ✈️ Afri-Ka Travel - Namibia Holidays
4️⃣ 📺 Vivid Graphix - LED Screens

Reply 1-4
Type MENU"""

MENUS_TEXT = {
 "1": """🤖 Kahlel AI - We Build The Future
Website: www.kahlel-ai.com

We do:
✅ AI Robots - Schools, malls, receptions
✅ AI Voice Agents - Answers calls 24/7
✅ WhatsApp AI Bots - Like this one! Auto-booking
✅ AI Automation - For your business

Turn your business into AI business.
Type DEMO + your business name.

Reply Menu""",
 "2": f"""🎬 Kahlel Flix - Movie Under The Stars ✨
Website: {WEBSITE_FLIX}
Book here: {RESERVE_LINK}

Imagine... warm night, stars above, big screen, popcorn in hand, friends laughing. That's Kahlel Flix.

We bring cinema to YOU - backyard, lodge, school, corporate.

📦 Packages: Small N$1500 (30) | Medium N$2500 (80) | Large N$4000 (150+)

🎟️ Tickets: Normal N$55
🥈 Silver N$390/y = N$27.50 + FREE popcorn Save N$3,120
👑 VIP N$490/y = N$13.75 + FREE popcorn+drink+beanbag Save N$8,415 - MOST POPULAR!

Type SILVER / VIP or RESERVE""",
 "3": """✈️ Afri-Ka Travel & Tours - See Namibia First! 🇳🇦
Website: www.afri-katours.com

Your holiday in Namibia starts here!

🌵 Sossusvlei, Swakopmund, Etosha Safaris
🏖️ Beach Holidays & Lodge Bookings
✈️ Airport N$350 | City N$150-250
🗺️ Custom Tours for Families & Groups

Send: FROM-TO + Date + People + Name

Reply Menu""",
 "4": """📺 Vivid Graphix - LED Specialists
Website: www.kahlel.co.za

✅ LED Screen Hire - Indoor & Outdoor
✅ LED Sales & Installation
✅ LED Repair & Maintenance - We fix all brands
✅ Content & Visual Support

For concerts, churches, weddings, corporate.

Tell us: Indoor/Outdoor + Size + Date?

Reply Menu"""
}

MENUS_IMAGE = {"1": IMAGE_AI, "2": IMAGE_FLIX, "3": IMAGE_TRAVEL, "4": IMAGE_LED}

def groq_reply(msg, last=None):
    low=msg.lower(); service=last or "Kahlel Group"
    if "flix" in low: service="Kahlel Flix"
    if "silver" in low or "vip" in low: service="Kahlel Flix"
    if "ai" in low or "robot" in low: service="Kahlel AI"
    if any(k in low for k in ["travel","afri-ka","airport","holiday","namibia"]): service="GoGirl Afri-Ka Travel"
    if "vivid" in low or "led" in low: service="Vivid Graphix"
    date=""; m=re.search(r'(\d{1,2}.*(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*|tomorrow|today)', low)
    if m: date=m.group(1)
    extracted={"service":service,"date":date}
    smart=None
    try:
        from groq import Groq
        client=Groq(api_key=GROQ_API_KEY)
        for MODEL in MODELS:
            try:
                sys_prompt=f"You are Kahlel Group. Last {last}. AI robots+voice bots, Flix {WEBSITE_FLIX} N$1500-4000 tickets N$55 Silver N$390=N$27.50 save N$3120 VIP N$490=N$13.75 save N$8415 Reserve {RESERVE_LINK} Travel Namibia Sossusvlei Etosha Airport N$350 Vivid LED hire repair. Be short."
                c=client.chat.completions.create(model=MODEL, messages=[{"role":"system","content":sys_prompt},{"role":"user","content":msg}], max_tokens=350, temperature=0.6)
                smart=c.choices[0].message.content; break
            except: continue
    except: pass
    return extracted, smart

def save_full(phone, service, name, date, location, people, message):
    try: requests.post(SHEET_URL, json={"phone":phone,"service":service,"name":name,"date":date,"location":location,"people":people,"message":message}, timeout=10)
    except: pass

def send_text(to, text):
    try:
        to_clean="+"+str(to).strip().lstrip("+")
        url="https://api.d7networks.com/whatsapp/v2/send"
        headers={"Authorization": f"Bearer {D7_API_TOKEN}", "Content-Type":"application/json"}
        payload={"messages":[{"originator":D7_NUMBER,"content":{"message_type":"TEXT","text":{"body":text[:1000]}},"recipients":[{"recipient":to_clean,"recipient_type":"individual"}]}]}
        requests.post(url, headers=headers, json=payload, timeout=15)
    except: pass

def send_image(to, image_url, caption):
    to_clean="+"+str(to).strip().lstrip("+")
    url="https://api.d7networks.com/whatsapp/v2/send"
    headers={"Authorization": f"Bearer {D7_API_TOKEN}", "Content-Type":"application/json"}
    
    attempts = [
        # Format 1
        {"message_type":"IMAGE","image":{"url": image_url, "caption": caption[:900]}},
        # Format 2 - link not url
        {"message_type":"IMAGE","image":{"link": image_url, "caption": caption[:900]}},
        # Format 3 - media
        {"message_type":"MEDIA","media":{"type":"image","url": image_url, "caption": caption[:900]}}
    ]
    
    for payload_content in attempts:
        try:
            payload={"messages":[{"originator":D7_NUMBER,"content":payload_content,"recipients":[{"recipient":to_clean,"recipient_type":"individual"}]}]}
            r=requests.post(url, headers=headers, json=payload, timeout=15)
            log(f"ATTEMPT {payload_content['message_type']} {r.status_code} {r.text[:300]}")
            if r.status_code == 200 and "failed" not in r.text.lower():
                return  # SUCCESS!
        except Exception as e:
            log(f"ATTEMPT ERR {e}")
            continue
    
    # If all 3 fail, send text+link (your current screenshot - works)
    log("ALL IMG FAILED - FALLBACK")
    send_text(to, f"{caption}\n\n{image_url}")
@app.route("/webhook", methods=["POST","GET"])
def webhook():
    if request.method=="GET": return f"V19 FINAL REAL IMAGES {RESERVE_LINK}",200
    raw=request.get_data(as_text=True); data=json.loads(raw) if raw else {}
    sender=""; msg=""
    if "event_content" in data:
        m=data["event_content"].get("message",{}); sender=m.get("originator",""); txt=m.get("text",{}); msg=txt.get("body","") if isinstance(txt,dict) else str(txt)
    if not sender or not msg: return jsonify({"status":"ignored"}),200
    sender="+"+str(sender).strip().lstrip("+"); low=msg.lower().strip()

    if any(k in low for k in ["reserve ticket","book ticket","reserve","booking link","products"]):
        SESSION[sender]="Kahlel Flix"; save_full(sender, "Kahlel Flix - Reserve", "", "", "", "", msg)
        send_image(sender, IMAGE_FLIX, f"🎟️ Reserve in 30 sec! 👇\nBook: {RESERVE_LINK}\n\nNormal N$55\nSilver N$27.50 + FREE popcorn\nVIP N$13.75 + FREE popcorn+drink+beanbag\n\nOr type SILVER / VIP + Name + Date!")
        return jsonify({"status":"sent"}),200

    if any(k in low for k in ["silver","vip","membership","member","join club"]):
        SESSION[sender]="Kahlel Flix"
        if "vip" in low: save_full(sender, "Kahlel Flix - VIP", "", "", "", "", msg); send_image(sender, IMAGE_FLIX, f"👑 VIP N$490/y Saves N$8,415/y! Movies N$13.75 + FREE N$130\nBook: {RESERVE_LINK}\nPay N$490 & send screenshot!")
        elif "silver" in low: save_full(sender, "Kahlel Flix - SILVER", "", "", "", "", msg); send_image(sender, IMAGE_FLIX, f"🥈 Silver N$390/y = N$27.50 + FREE popcorn Save N$3,120\nBook: {RESERVE_LINK}")
        else: send_image(sender, IMAGE_FLIX, f"We have 2 plans 007! 👇\n\n🥈 SILVER N$390/y N$27.50+popcorn Save N$3,120\n👑 VIP N$490/y N$13.75+popcorn+drink+beanbag Save N$8,415 MOST POPULAR\n\nReserve: {RESERVE_LINK}\nType SILVER or VIP")
        return jsonify({"status":"sent"}),200

    MONTHS=["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]
    has_month=any(x in low for x in MONTHS)
    is_booking=len(msg.split())>=2 and (has_month or any(k in low for k in ["book","tomorrow","today","name","from","people","am","pm","airport","demo"]) or SESSION.get(sender))
    
    if is_booking:
        extracted, smart=groq_reply(msg, SESSION.get(sender))
        SESSION[sender]=extracted["service"]; save_full(sender, extracted["service"], "", extracted["date"] or msg, "", "", msg)
        send_text(sender, smart or f"Got it! {extracted['service']} for {extracted['date'] or msg}. Book: {RESERVE_LINK}")
    elif low in ["1","2","3","4"]:
        mapping={"1":"Kahlel AI","2":"Kahlel Flix","3":"GoGirl Afri-Ka Travel","4":"Vivid Graphix"}
        sm=mapping[low]; SESSION[sender]=sm; save_full(sender, sm, "", "", "", "", f"Pressed {low}")
        send_image(sender, MENUS_IMAGE[low], MENUS_TEXT[low])
    elif low in ["hello","hi","menu","start","welcome"]:
        SESSION.pop(sender, None); send_text(sender, WELCOME)
    else:
        _, smart=groq_reply(msg, SESSION.get(sender)); send_text(sender, smart or WELCOME)
    return jsonify({"status":"sent"}),200

@app.route("/")
def home(): return f"V19 FINAL REAL IMAGES {RESERVE_LINK}"
@app.route("/health")
def health(): return jsonify({"model":MODELS[0],"images":"real"})

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
