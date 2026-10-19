import os, requests, json, re, time
from flask import Flask, request, jsonify

app = Flask(__name__)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
D7_API_TOKEN = os.getenv("D7_API_TOKEN")
SHEET_URL = os.getenv("SHEET_WEBHOOK_URL")
D7_NUMBER = "+264817491383"
OWNER_NUMBER = "+264812945081"  # your number for alerts

def log(m): print(m, flush=True)

# FIXED NAME: 3. GoGirl Afri-Ka Travel
WELCOME = """👉Welcome to Kahlel Group! 👋
1️⃣ 🤖 Kahlel AI - Robotics & Automation
2️⃣ 🎬 Kahlel Flix - Outdoor Cinema
3️⃣ ✈️ GoGirl Afri-Ka Travel - Airport & City Transfers
4️⃣ 📺 Vivid Graphix - LED & Signage

Reply 1-4 or describe your booking (e.g. Book GoGirl tomorrow 5am from Kleine Kuppe to airport, name Leon, 2 people)"""

MENUS = {
 "1": "🤖 *Kahlel AI*\nWe build WhatsApp bots like this one! From N$1500 setup + N$500/mo.\nWhat business do you want to automate?\n\nReply *Menu*",
 "2": "🎬 *Kahlel Flix*\nOutdoor Cinema: Small N$1500 (30 ppl) Med N$2500 (80) Large N$4000 (150+)\nIncludes screen, projector, sound.\nWhen is your event? Reply *Menu*",
 "3": "✈️ *GoGirl Afri-Ka Travel*\nAirport Transfers N$350, City N$150-250, Luxury N$800/day\n24/7 Female drivers, safe & reliable.\nSend your pickup location? Reply *Menu*",
 "4": "📺 *Vivid Graphix*\nLED Display rental N$2000/day, signage, branding.\nWhat size/event? Reply *Menu*"
}

def hard_extract(msg):
    low=msg.lower()
    service="GoGirl Afri-Ka Travel"
    if "flix" in low: service="Kahlel Flix"
    elif "vivid" in low or "led" in low: service="Vivid Graphix"
    elif "kahlel ai" in low or "bot" in low: service="Kahlel AI"
    name=""; people=""; date=""; location=""
    m=re.search(r'name\s*[:=]?\s*([A-Za-z]+)', msg, re.I)
    if m: name=m.group(1).capitalize()
    m=re.search(r'(\d+)\s*people', low)
    if m: people=m.group(1)
    m=re.search(r'(tomorrow\s*\d*\s*am|tomorrow\s*\d*\s*pm|today\s*\d*\s*am|\d+\s*am|\d+\s*pm)', low)
    if m: date=m.group(1)
    else:
        if "tomorrow" in low: date="tomorrow"
        elif "today" in low: date="today"
    m=re.search(r'from\s+(.+?)\s+to\s+([^,]+)', msg, re.I)
    if m: location=f"{m.group(1).strip()} to {m.group(2).strip()}"
    else:
        m=re.search(r'from\s+([^,]+)', msg, re.I)
        if m: location=m.group(1).strip()
    return {"service":service,"name":name,"date":date,"location":location,"people":people}

def groq_extract_and_reply(msg):
    try:
        from groq import Groq
        if not GROQ_API_KEY or "gsk_" not in GROQ_API_KEY: 
            return hard_extract(msg), None
        client=Groq(api_key=GROQ_API_KEY)
        # Extraction
        prompt=f"""Extract from "{msg}" as JSON: {{"service":"GoGirl Afri-Ka Travel|Kahlel Flix|Vivid Graphix|Kahlel AI","name":"","date":"","location":"","people":""}}. Return JSON only."""
        c=client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role":"user","content":prompt}], max_tokens=250, temperature=0.1)
        txt=c.choices[0].message.content
        log(f"GROQ EXTRACT RAW: {txt}")
        m=re.search(r'\{{.*\}}', txt, re.DOTALL)
        if m:
            gj=json.loads(m.group())
            # fill gaps with regex
            r=hard_extract(msg)
            for k in ["name","date","location","people","service"]:
                if not gj.get(k): gj[k]=r.get(k,"")
            extracted=gj
        else:
            extracted=hard_extract(msg)
        
        # Smart reply
        sys="You are Kahlel Group Namibia assistant. 1)Kahlel AI bots N$1500+ 2)Kahlel Flix cinema N$1500-4000 3)GoGirl Afri-Ka Travel Airport N$350 City N$150-250 female drivers 24/7 4)Vivid LED N$2000/day. If appointment, confirm with name/date/location/people warmly. Be short, friendly, professional. End with Type Menu for other services."
        c2=client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role":"system","content":sys},{"role":"user","content":msg}], max_tokens=400, temperature=0.7)
        smart_reply=c2.choices[0].message.content
        return extracted, smart_reply
    except Exception as e:
        log(f"Groq err {e}")
        return hard_extract(msg), None

def save_full(phone, service, name, date, location, people, message):
    try:
        payload={"phone":phone,"service":service,"name":name,"date":date,"location":location,"people":people,"message":message}
        r=requests.post(SHEET_URL, json=payload, timeout=10)
        log(f"SAVED {service}|{name}|{date}|{location}|{people} {r.status_code}")
        return r.status_code==200
    except Exception as e:
        log(f"SHEET ERR {e}"); return False

def send(to, text):
    try:
        to_clean="+"+str(to).strip().lstrip("+")
        url="https://api.d7networks.com/whatsapp/v2/send"
        headers={"Authorization": f"Bearer {D7_API_TOKEN}", "Content-Type":"application/json"}
        payload={"messages":[{"originator":D7_NUMBER,"content":{"message_type":"TEXT","text":{"body":text[:1000]}},"recipients":[{"recipient":to_clean,"recipient_type":"individual"}]}]}
        requests.post(url, headers=headers, json=payload, timeout=15)
        log(f"SENT to {to_clean}: {text[:80]}")
    except Exception as e:
        log(f"SEND ERR {e}")

@app.route("/webhook", methods=["POST","GET"])
def webhook():
    if request.method=="GET": return "V12 GoGirl Afri-Ka + Groq LIVE",200
    try:
        raw=request.get_data(as_text=True); data=json.loads(raw) if raw else {}
        sender=""; msg=""
        if "event_content" in data:
            m=data["event_content"].get("message",{}); sender=m.get("originator",""); txt=m.get("text",{}); msg=txt.get("body","") if isinstance(txt,dict) else str(txt)
        if not sender or not msg: return jsonify({"status":"ignored"}),200
        sender="+"+str(sender).strip().lstrip("+"); low=msg.lower().strip()
        log(f"USER: {msg}")

        is_booking = len(msg.split())>3 and any(k in low for k in ["appointment","book","tomorrow","today","name","from","people","am","pm","airport","transfer"])

        if is_booking:
            extracted, smart = groq_extract_and_reply(msg)
            log(f"FINAL EXTRACTED: {extracted}")
            save_full(sender, extracted["service"], extracted["name"], extracted["date"], extracted["location"], extracted["people"], msg)
            
            # 1. Smart Groq reply to customer
            if smart:
                reply=smart
            else:
                reply=f"✅ *Booking Confirmed!*\n\nService: {extracted['service']}\nName: {extracted['name'] or 'Not given'}\nDate: {extracted['date'] or 'Not given'}\nPickup: {extracted['location'] or 'Not given'}\nPeople: {extracted['people'] or '1'}\n\nWe will call you shortly to confirm. Thank you for choosing {extracted['service']}! 🙏\n\nType *Menu* for other services."
            send(sender, reply)
            
            # 2. AUTO WhatsApp confirmation to Leon (customer gets 2nd message)
            time.sleep(1)
            confirm_msg=f"🔔 *Confirmation - {extracted['service']}*\n\nHi {extracted['name'] or 'there'}! Your transfer is scheduled:\n📅 {extracted['date']}\n📍 {extracted['location']}\n👥 {extracted['people']} people\n\nDriver will contact you 1hr before. Questions? Reply here.\nGoGirl Afri-Ka Travel Team ✈️"
            send(sender, confirm_msg)
            
            # 3. Alert owner
            try:
                owner_alert=f"NEW BOOKING! {extracted['service']} | {extracted['name']} | {extracted['date']} | {extracted['location']} | {extracted['people']} ppl | {sender}"
                send(OWNER_NUMBER, owner_alert)
            except: pass

        elif low in ["1","2","3","4"]:
            reply=MENUS[low]
            service_map={"1":"Kahlel AI","2":"Kahlel Flix","3":"GoGirl Afri-Ka Travel","4":"Vivid Graphix"}
            save_full(sender, service_map[low], "", "", "", "", f"Pressed {low} - interested in {service_map[low]}")
            send(sender, reply)
        elif low in ["hello","hi","hey","menu","start","0","welcome","dumelang"]:
            send(sender, WELCOME)
        else:
            # Groq smart for general questions
            _, smart = groq_extract_and_reply(msg)
            reply = smart or WELCOME
            send(sender, reply)

        return jsonify({"status":"sent"}),200
    except Exception as e:
        log(f"EXC {e}"); import traceback; traceback.print_exc(); return jsonify({"ok":True}),200

@app.route("/")
def home(): return "Kahlel V12 - GoGirl Afri-Ka Travel + Groq + Auto Confirm"
@app.route("/health")
def health(): return jsonify({"groq":bool(GROQ_API_KEY and "gsk_" in GROQ_API_KEY),"sheet":bool(SHEET_URL),"d7":bool(D7_API_TOKEN)})

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
