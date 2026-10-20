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

# LOCKED REAL CONTACT
CONTACT_PHONE = "+264812086309"
CONTACT_EMAIL = "info@kahlel.co.za"
RESERVE_LINK = "https://kahlelflix.com/products"

# CAL.COM LINKS - PER SERVICE
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

Reply 1-4 | Type MENU | Type MEETING to book"""

MENUS_TEXT = {
 "1": f"""🤖 Kahlel AI - We Build The Future
Website: kahlel-ai.com

✅ AI Robots | Voice Agents | WhatsApp Bots | Automation
Type DEMO + your business name.

📅 Book Meeting: {CAL_LINKS['Kahlel AI']}
Contact: {CONTACT_PHONE} / {CONTACT_EMAIL}
Reply Menu""",
 "2": f"""🎬 Kahlel Flix - Movie Under The Stars ✨
Book: {RESERVE_LINK}

📦 Small N$1500 | Medium N$2500 | Large N$4000
🎟️ Normal N$55 | Silver N$390= N$27.50 | VIP N$490= N$13.75

📅 Book Meeting: {CAL_LINKS['Kahlel Flix']}
Contact: {CONTACT_PHONE} / Type SILVER / VIP""",
 "3": f"""✈️ Afri-Ka Travel - See Namibia First! 🇳🇦
Website: afri-katours.com

🌵 Sossusvlei | Swakopmund | Etosha | Beach | Transfers N$150-350

📅 Book Meeting: {CAL_LINKS['GoGirl Afri-Ka Travel']}
Contact: {CONTACT_PHONE} / Send FROM-TO + Date""",
 "4": f"""📺 Vivid Graphix - LED Specialists
Website: kahlel.co.za

✅ Hire | Sales & Install | Repair all brands

📅 Book Meeting: {CAL_LINKS['Vivid Graphix']}
Contact: {CONTACT_PHONE} / Tell Indoor/Outdoor + Size?"""
}

MENUS_IMAGE = {"1": IMAGE_AI, "2": IMAGE_FLIX, "3": IMAGE_TRAVEL, "4": IMAGE_LED}

PROMPTS = {
 "Kahlel AI": f"ONLY Kahlel AI. Contact {CONTACT_PHONE} {CONTACT_EMAIL}. Cal {CAL_LINKS['Kahlel AI']}. ONLY AI Robots, Voice AI, WhatsApp Bots, Automation. NEVER mention Flix tickets, travel, LED. For DEMO ask business name. If meeting requested give Cal link.",
 "Kahlel Flix": f"ONLY Kahlel Flix. Contact {CONTACT_PHONE}. Book {RESERVE_LINK}. Cal {CAL_LINKS['Kahlel Flix']}. ONLY Movie Under Stars, packages N$1500/2500/4000, tickets N$55 Silver N$390 VIP N$490. NEVER mention robots, travel, LED.",
 "GoGirl Afri-Ka Travel": f"ONLY Afri-Ka Travel. Contact {CONTACT_PHONE}. Cal {CAL_LINKS['GoGirl Afri-Ka Travel']}. ONLY Namibia holidays Sossusvlei Etosha Swakopmund transfers N$150-350. NEVER mention Flix kahlelflix.com/products, LED, AI.",
 "Vivid Graphix": f"ONLY Vivid LED. Contact {CONTACT_PHONE} {CONTACT_EMAIL}. Cal {CAL_LINKS['Vivid Graphix']}. ONLY LED hire sales repair. NEVER mention Flix tickets travel robots. Use only {CONTACT_PHONE}.",
 "Kahlel Group": f"General helper. Contact {CONTACT_PHONE} {CONTACT_EMAIL}. Cal links: AI {CAL_LINKS['Kahlel AI']} etc. Ask 1-4. Do not mix. Never +27 12 345 678."
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
    if request.method=="GET": return f"V19.7 CAL {RESERVE_LINK}",200
    raw=request.get_data(as_text=True); data=json.loads(raw) if raw else {}
    sender=""; msg=""
    if "event_content" in data:
        m=data["event_content"].get("message",{}); sender=m.get("originator",""); txt=m.get("text",{}); msg=txt.get("body","") if isinstance(txt,dict) else str(txt)
    if not sender or not msg: return jsonify({"status":"ignored"}),200
    sender="+"+str(sender).strip().lstrip("+"); low=msg.lower().strip()

    # CAL.COM BOOKING INTENT - PRIORITY
    if any(k in low for k in ["book meeting","appointment","book a meeting","book call","cal.com","consultation","meeting","schedule call","meet you","speak to leon"]):
        service = SESSION.get(sender, "Kahlel Group")
        cal_link = CAL_LINKS.get(service, CAL_LINKS["Kahlel Group"])
        save_full(sender, service+" - WANTS MEETING", "", "", "", "", msg, lead_type="HOT - Wants Meeting")
        send_text(sender, f"📅 Let's meet! Book directly here — pick your time:\n\n👉 {cal_link}\n\nFor {service} — I will prepare for you. What date works?\nContact {CONTACT_PHONE}")
        return jsonify({"status":"sent"}),200

    if any(k in low for k in ["reserve ticket","book ticket","reserve","booking link","products"]):
        SESSION[sender]="Kahlel Flix"; save_full(sender, "Kahlel Flix - Reserve", "", "", "", "", msg, "HOT - Reserve"); send_image(sender, IMAGE_FLIX, f"🎟️ Reserve in 30 sec! 👇\nBook: {RESERVE_LINK}\n📅 Or book meeting: {CAL_LINKS['Kahlel Flix']}\nContact {CONTACT_PHONE}"); return jsonify({"status":"sent"}),200

    if any(k in low for k in ["silver","vip","membership","member","join club"]):
        SESSION[sender]="Kahlel Flix"
        if "vip" in low: save_full(sender, "Kahlel Flix - VIP", "", "", "", "", msg, "HOT - VIP"); send_image(sender, IMAGE_FLIX, f"👑 VIP N$490/y Saves N$8,415/y! Book: {RESERVE_LINK}\n📅 Meet: {CAL_LINKS['Kahlel Flix']}")
        elif "silver" in low: save_full(sender, "Kahlel Flix - SILVER", "", "", "", "", msg, "HOT - Silver"); send_image(sender, IMAGE_FLIX, f"🥈 Silver N$390/y = N$27.50 + FREE popcorn Save N$3,120\nBook: {RESERVE_LINK}\nMeet: {CAL_LINKS['Kahlel Flix']}")
        else: send_image(sender, IMAGE_FLIX, f"We have 2 plans! 🥈 SILVER N$390 Save N$3,120 👑 VIP N$490 Save N$8,415 Reserve: {RESERVE_LINK} Meet: {CAL_LINKS['Kahlel Flix']}")
        return jsonify({"status":"sent"}),200

    MONTHS=["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]; has_month=any(x in low for x in MONTHS)
    is_booking=len(msg.split())>=2 and (has_month or any(k in low for k in ["book","tomorrow","today","name","from","people","am","pm","airport","demo"]) or SESSION.get(sender))
    if is_booking:
        extracted, smart=groq_reply(msg, SESSION.get(sender)); SESSION[sender]=extracted["service"]; save_full(sender, extracted["service"], "", extracted["date"] or msg, "", "", msg, "Prospect"); send_text(sender, smart or f"Got it! {extracted['service']} Contact {CONTACT_PHONE} Meet {CAL_LINKS.get(extracted['service'],'')}")
    elif low in ["1","2","3","4"]:
        mapping={"1":"Kahlel AI","2":"Kahlel Flix","3":"GoGirl Afri-Ka Travel","4":"Vivid Graphix"}; sm=mapping[low]; SESSION[sender]=sm; save_full(sender, sm, "", "", "", "", f"Pressed {low}", "Cold - Browsing"); send_image(sender, MENUS_IMAGE[low], MENUS_TEXT[low])
    elif low in ["hello","hi","menu","start","welcome"]:
        SESSION.pop(sender, None); send_text(sender, WELCOME)
    else:
        _, smart=groq_reply(msg, SESSION.get(sender)); send_text(sender, smart or WELCOME)
    return jsonify({"status":"sent"}),200

@app.route("/")
def home(): return f"V19.7 CAL READY {CONTACT_PHONE}"
@app.route("/health")
def health(): return jsonify({"model":MODELS[0],"contact":CONTACT_PHONE,"cal":CAL_LINKS})

if __name__=="__main__": app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
