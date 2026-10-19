import os, requests, json, re
from flask import Flask, request, jsonify

app = Flask(__name__)
SHEET_URL = os.getenv("SHEET_WEBHOOK_URL")
D7_API_TOKEN = os.getenv("D7_API_TOKEN")
D7_NUMBER = "+264817491383"

def log(m): print(m, flush=True)

WELCOME = """👉Welcome to Kahlel Group! 👋
1️⃣ 🤖 Kahlel AI
2️⃣ 🎬 Kahlel Flix
3️⃣ ✈️ Afri-Ka Travels
4️⃣ 📺 Vivid Graphix
Reply 1-4"""

MENUS = {"1":"🤖 Kahlel AI\nFrom N$1500\nReply Menu","2":"🎬 Flix N$1500-4000\nReply Menu","3":"✈️ GoGirl Airport N$350 City N$150-250\nReply Menu","4":"📺 Vivid LED N$2000/day\nReply Menu"}

def hard_extract(msg):
    low = msg.lower()
    # defaults
    service = "GoGirl Travel" if "gogirl" in low or "airport" in low or "travel" in low else "Appointment"
    if "flix" in low: service="Kahlel Flix"
    if "vivid" in low or "led" in low: service="Vivid Graphix"
    if "kahlel ai" in low or "bot" in low: service="Kahlel AI"
    
    # name
    name = ""
    m = re.search(r'name\s*[:=]?\s*([A-Za-z]+)', msg, re.I)
    if m: name = m.group(1)
    
    # people
    people = ""
    m = re.search(r'(\d+)\s*people', low)
    if m: people = m.group(1)
    
    # date
    date = ""
    m = re.search(r'(tomorrow\s*\d*\s*am|tomorrow\s*\d*\s*pm|today\s*\d*\s*am|\d+\s*am|\d+\s*pm)', low)
    if m: date = m.group(1)
    else:
        if "tomorrow" in low: date="tomorrow"
        if "today" in low: date="today"
    
    # location from X to Y
    location = ""
    m = re.search(r'from\s+(.+?)\s+to\s+([^,]+)', msg, re.I)
    if m:
        location = f"{m.group(1).strip()} to {m.group(2).strip()}"
    else:
        m = re.search(r'from\s+([A-Za-z ]+)', msg, re.I)
        if m: location = m.group(1).strip()
    
    result = {"service":service,"name":name,"date":date,"location":location,"people":people}
    log(f"REGEX RESULT: {result}")
    return result

def save_full(phone, service, name, date, location, people, message):
    if not SHEET_URL:
        log("NO SHEET_URL!"); return
    payload = {"phone":phone,"service":service,"name":name,"date":date,"location":location,"people":people,"message":message}
    try:
        r = requests.post(SHEET_URL, json=payload, timeout=10)
        log(f"SAVED FINAL: {service}|{name}|{date}|{location}|{people} -> {r.status_code} {r.text[:100]}")
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
    if request.method=="GET": return "V10 HARD REGEX",200
    try:
        raw=request.get_data(as_text=True)
        data=json.loads(raw) if raw else {}
        sender=""; msg=""
        if "event_content" in data:
            m=data["event_content"].get("message",{})
            sender=m.get("originator","")
            txt=m.get("text",{})
            msg=txt.get("body","") if isinstance(txt,dict) else str(txt)
        if not sender or not msg: return jsonify({"status":"ignored"}),200
        sender="+"+str(sender).strip().lstrip("+")
        low=msg.lower().strip()
        log(f"USER RAW: {msg}")

        is_booking = len(msg.split())>3 and any(k in low for k in ["appointment","book","tomorrow","today","name","from","people","am","pm"])

        if is_booking:
            ext = hard_extract(msg)
            save_full(sender, ext["service"], ext["name"], ext["date"], ext["location"], ext["people"], msg)
            reply = f"✅ Appointment saved!\nService: {ext['service']}\nName: {ext['name']}\nDate: {ext['date']}\nLocation: {ext['location']}\nPeople: {ext['people']}\n\nWe'll confirm shortly! Type Menu"
        elif low in ["1","2","3","4"]:
            reply=MENUS[low]; save_full(sender, MENUS[low][:10], "", "", "", "", msg)
        elif low in ["hello","hi","menu","start","welcome"]:
            reply=WELCOME
        else:
            reply=WELCOME

        send(sender, reply)
        return jsonify({"status":"sent"}),200
    except Exception as e:
        log(f"EXC {e}"); import traceback; traceback.print_exc(); return jsonify({"ok":True}),200

@app.route("/")
def home(): return "V10"
@app.route("/health")
def health(): return jsonify({"sheet":bool(SHEET_URL)})

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
