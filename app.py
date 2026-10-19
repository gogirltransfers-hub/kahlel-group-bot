import os, requests, json, re, time
from flask import Flask, request, jsonify
app = Flask(__name__)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
D7_API_TOKEN = os.getenv("D7_API_TOKEN")
SHEET_URL = os.getenv("SHEET_WEBHOOK_URL")
D7_NUMBER = "+264817491383"
OWNER_NUMBER = "+264812945081"
def log(m): print(m, flush=True)

WELCOME = """👉Welcome to Kahlel Group! 👋
1️⃣ 🤖 Kahlel AI - Robotics & Automation
2️⃣ 🎬 Kahlel Flix - Outdoor Cinema
3️⃣ ✈️ Afri-Ka Travel - Travel & Tours
4️⃣ 📺 Vivid Graphix - LED Display & Signage

Reply 1-4 or type your booking (e.g. Book Afri-Ka tomorrow 5am, name Leon)
Type MENU to go back"""

MENUS = {
 "1": "🤖 Kahlel AI\nWebsite: www.kahlel-ai.com\nBots from N$1500 + N$500/mo\nAuto-replies, bookings, Sheets CRM\n\nWhat business?\nReply Menu",
 "2": "🎬 Kahlel Flix\nWebsite: www.kahlelflix.com\nSmall N$1500 (30 ppl)\nMedium N$2500 (80 ppl)\nLarge N$4000 (150+ ppl)\nProjector+Sound+Screen\n\nWhen is event?\nReply Menu",
 "3": "✈️ Afri-Ka Travel\nWebsite: www.afri-katours.com\nAirport N$350 | City N$150-250\n24/7 female drivers, safe, child seats\nHosea Kutako ↔ Windhoek\n\nSend pickup FROM-TO + Date/Time + Name?\nReply Menu",
 "4": "📺 Vivid Graphix\nWebsite: www.kahlel.co.za\nLED N$2000/day, stage, signage, branding\n\nWhat size?\nReply Menu"
}

def hard_extract(msg):
    low=msg.lower()
    service="GoGirl Afri-Ka Travel"
    if "flix" in low and "gogirl" not in low and "airport" not in low and "transfer" not in low:
        service="Kahlel Flix"
    elif "vivid" in low or ("led" in low and "airport" not in low):
        service="Vivid Graphix"
    elif "kahlel ai" in low or ("bot" in low and "airport" not in low):
        service="Kahlel AI"
    if any(k in low for k in ["gogirl","afri-ka","afrika","airport","hosea kutako","transfer","kleine kuppe"]):
        service="GoGirl Afri-Ka Travel"
    name=""; people=""; date=""; location=""
    m=re.search(r'name\s*[:=]?\s*([A-Za-z]+)', msg, re.I)
    if m: name=m.group(1).capitalize()
    m=re.search(r'(\d+)\s*people', low)
    if m: people=m.group(1)
    m=re.search(r'(tomorrow\s*\d*\s*am|tomorrow\s*\d*\s*pm|today\s*\d*\s*am|today\s*\d*\s*pm|\d+\s*am|\d+\s*pm)', low)
    if m: date=m.group(1)
    else:
        if "tomorrow" in low: date="tomorrow"
        elif "today" in low: date="today"
    m=re.search(r'from\s+(.+?)\s+to\s+([^,]+?)(?:,|\s+name|\s+\d+\s+people|$)', msg, re.I)
    if m: location=f"{m.group(1).strip()} to {m.group(2).strip()}"
    else:
        m=re.search(r'from\s+([^,]+?)(?:,|\s+name|$)', msg, re.I)
        if m: location=m.group(1).strip()
    log(f"REGEX {service}|{name}|{date}|{location}|{people}")
    return {"service":service,"name":name,"date":date,"location":location,"people":people}

def groq_extract_and_reply(msg):
    MODEL="llama-3.3-70b-versatile"
    extracted=hard_extract(msg)
    smart_reply=None
    try:
        from groq import Groq
        if not GROQ_API_KEY or "gsk_" not in GROQ_API_KEY:
            return extracted, None
        client=Groq(api_key=GROQ_API_KEY)
        try:
            prompt=f'Extract JSON only: Service=GoGirl Afri-Ka Travel|Kahlel Flix|Vivid Graphix|Kahlel AI, name, date, location, people from "{msg}". Return {{"service":"","name":"","date":"","location":"","people":""}} only.'
            c=client.chat.completions.create(model=MODEL, messages=[{"role":"user","content":prompt}], max_tokens=300, temperature=0.1)
            txt=c.choices[0].message.content
            log(f"GROQ RAW: {txt}")
            m=re.search(r'\{{.*\}}', txt, re.DOTALL)
            if m:
                gj=json.loads(m.group())
                for k in ["name","date","location","people"]:
                    if gj.get(k): extracted[k]=gj[k]
                if "gogirl" not in msg.lower() and "airport" not in msg.lower():
                    if gj.get("service"): extracted["service"]=gj["service"]
        except Exception as e:
            log(f"Groq extract fail {e}")
        try:
            sys_prompt="""You are Kahlel Group Namibia assistant. 4 brands:

1. Kahlel AI - WhatsApp bots. Website: www.kahlel-ai.com. Setup N$1500 + N$500/mo

2. Kahlel Flix - Outdoor Cinema. Website: www.kahlelflix.com. Small N$1500, Medium N$2500, Large N$4000. Windhoek + surrounds. Instagram @kahlelflix

3. Afri-Ka Travel - Airport Transfers. Website: www.afri-katours.com. Airport N$350, City N$150-250, Hourly N$200, Luxury N$800/day. 24/7 female drivers, safe for women & kids, child seats. Coverage: Windhoek to Hosea Kutako Airport.

4. Vivid Graphix - LED & Signage. Website: www.kahlel.co.za. LED N$2000/day

If asked about prices/websites, answer from above. If booking Afri-Ka, confirm with name/date/location/people. Short, friendly. End with Type Menu."""
            c2=client.chat.completions.create(model=MODEL, messages=[{"role":"system","content":sys_prompt},{"role":"user","content":msg}], max_tokens=400, temperature=0.6)
            smart_reply=c2.choices[0].message.content
            log(f"GROQ REPLY: {smart_reply[:100]}")
        except Exception as e:
            log(f"Groq reply fail {e}")
    except Exception as e:
        log(f"Groq lib err {e}")
    return extracted, smart_reply

def save_full(phone, service, name, date, location, people, message):
    try:
        payload={"phone":phone,"service":service,"name":name,"date":date,"location":location,"people":people,"message":message}
        r=requests.post(SHEET_URL, json=payload, timeout=10)
        log(f"SAVED {service}|{name}|{date}|{location}|{people} {r.status_code}")
    except Exception as e:
        log(f"SHEET ERR {e}")

def send(to, text):
    try:
        to_clean="+"+str(to).strip().lstrip("+")
        url="https://api.d7networks.com/whatsapp/v2/send"
        headers={"Authorization": f"Bearer {D7_API_TOKEN}", "Content-Type":"application/json"}
        payload={"messages":[{"originator":D7_NUMBER,"content":{"message_type":"TEXT","text":{"body":text[:1000]}},"recipients":[{"recipient":to_clean,"recipient_type":"individual"}]}]}
        requests.post(url, headers=headers, json=payload, timeout=15)
    except: pass

@app.route("/webhook", methods=["POST","GET"])
def webhook():
    if request.method=="GET": return "V14 FINAL Emoji + Websites",200
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
            save_full(sender, extracted["service"], extracted["name"], extracted["date"], extracted["location"], extracted["people"], msg)
            reply=smart or f"Booking Confirmed!\nService: {extracted['service']}\nName: {extracted['name'] or 'Guest'}\nDate: {extracted['date']}\nPickup: {extracted['location']}\nPeople: {extracted['people'] or '1'}\n\nWe will confirm shortly! Type Menu"
            send(sender, reply)
            time.sleep(1)
            confirm=f"Confirmation - {extracted['service']}\nHi {extracted['name'] or 'there'}! Scheduled: {extracted['date']} | {extracted['location']} | {extracted['people']} ppl. Driver contacts 1hr before. GoGirl Team"
            send(sender, confirm)
            try: send(OWNER_NUMBER, f"NEW BOOKING {extracted['service']} | {extracted['name']} | {extracted['date']} | {extracted['location']} | {extracted['people']} | {sender}")
            except: pass
        elif low in ["1","2","3","4"] and len(low)==1:
            reply=MENUS[low]; sm={"1":"Kahlel AI","2":"Kahlel Flix","3":"GoGirl Afri-Ka Travel","4":"Vivid Graphix"}[low]
            save_full(sender, sm, "", "", "", "", f"Pressed {low}")
            send(sender, reply)
        elif low in ["hello","hi","menu","start","welcome"]:
            send(sender, WELCOME)
        else:
            _, smart = groq_extract_and_reply(msg)
            send(sender, smart or WELCOME)
        return jsonify({"status":"sent"}),200
    except Exception as e:
        log(f"EXC {e}"); return jsonify({"ok":True}),200

@app.route("/")
def home(): return "V14 FINAL Afri-Ka www.afri-katours.com"
@app.route("/health")
def health(): return jsonify({"groq":bool(GROQ_API_KEY and "gsk_" in GROQ_API_KEY),"sheet":bool(SHEET_URL)})

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
