import os, requests, json, re
from flask import Flask, request, jsonify
from groq import Groq

app = Flask(__name__)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
D7_API_TOKEN = os.getenv("D7_API_TOKEN")
SHEET_URL = os.getenv("SHEET_WEBHOOK_URL")
D7_NUMBER = "+264817491383"

def log(m): print(m, flush=True)

WELCOME = """👉Welcome to Kahlel Group! 👋
1️⃣ 🤖 Kahlel AI - Robotics & Automation
2️⃣ 🎬 Kahlel Flix - Outdoor Cinema
3️⃣ ✈️ Afri-Ka Travels - Travel & Tours
4️⃣ 📺 Vivid Graphix - LED Display & Signage
Reply 1-4 or type name"""

MENUS = {
 "1": "🤖 *Kahlel AI*\nWe build WhatsApp bots like this!\nFrom N$1500 setup\nWhat business to automate?\nReply *Menu*",
 "2": "🎬 *Kahlel Flix*\nSmall N$1500 (30) Med N$2500 (80) Large N$4000 (150+)\nScreen+projector+sound\nWhen is event? Reply *Menu*",
 "3": "✈️ *GoGirl Transfers*\nAirport N$350, City N$150-250, Luxury N$800/day\n24/7 Female drivers\nSend pickup location! Reply *Menu*",
 "4": "📺 *Vivid Graphix*\nLED rental N$2000/day, signage\nWhat size? Reply *Menu*"
}

def extract_appointment(msg):
    """AI extracts name/date/location/people/service"""
    try:
        if not GROQ_API_KEY or "gsk_" not in GROQ_API_KEY:
            return None
        client = Groq(api_key=GROQ_API_KEY)
        prompt = f"""From: "{msg}" extract JSON ONLY: {{"service":"Kahlel AI|Kahlel Flix|GoGirl Travel|Vivid Graphix|unknown","name":"","date":"","location":"","people":"","message":"{msg}"}} If no booking intent, return {{"service":"unknown"}}. JSON only, no text."""
        c = client.chat.completions.create(model="llama-3.1-8b-instant",
            messages=[{"role":"user","content":prompt}], max_tokens=250, temperature=0.1)
        txt = c.choices[0].message.content
        m = re.search(r'\{{.*\}}', txt, re.DOTALL)
        if m:
            return json.loads(m.group())
    except Exception as e:
        log(f"Extract err {e}")
    return None

def ai_reply(msg):
    try:
        if not GROQ_API_KEY or "gsk_" not in GROQ_API_KEY: return None
        client = Groq(api_key=GROQ_API_KEY)
        c = client.chat.completions.create(model="llama-3.1-8b-instant",
            messages=[{"role":"system","content":"You are Kahlel Group Namibia. 1)AI bots N$1500+ 2)Flix N$1500-4000 3)GoGirl Airport N$350 City N$150 24/7 female drivers 4)Vivid LED N$2000/day. If booking, ask name/date/location/people. Be short friendly. End Type Menu."},
                      {"role":"user","content":msg}], max_tokens=350)
        return c.choices[0].message.content
    except Exception as e:
        log(f"Groq err {e}"); return None

def save_full(phone, service, name, date, location, people, message):
    if not SHEET_URL:
        log("No SHEET_URL"); return
    try:
        payload = {"phone":phone,"service":service,"name":name,"date":date,"location":location,"people":people,"message":message}
        r = requests.post(SHEET_URL, json=payload, timeout=10)
        log(f"SHEET SAVE {service} | {name} | {date} | {location} | {r.status_code}")
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
    if request.method=="GET": return "V7 Appointment Parser LIVE",200
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
        log(f"USER: {msg}")

        # 1,2,3,4 fast path
        if low=="1" or low.startswith("1 ") or "kahlel ai" in low:
            reply=MENUS["1"]; save_full(sender,"Kahlel AI","","","","",msg)
        elif low=="2" or low.startswith("2 ") or "flix" in low:
            reply=MENUS["2"]; save_full(sender,"Kahlel Flix","","","","",msg)
        elif low=="3" or low.startswith("3 ") or "gogirl" in low or "travel" in low or "afri" in low:
            reply=MENUS["3"]; save_full(sender,"GoGirl Travel","","","","",msg)
        elif low=="4" or low.startswith("4 ") or "vivid" in low or "led" in low:
            reply=MENUS["4"]; save_full(sender,"Vivid Graphix","","","","",msg)
        elif low in ["hello","hi","hey","dumelang","menu","start","0","welcome","help"]:
            reply=WELCOME
        else:
            # Try AI extraction for full appointment
            extracted = extract_appointment(msg)
            log(f"EXTRACTED: {extracted}")
            if extracted and extracted.get("service")!="unknown":
                save_full(sender, extracted.get("service",""), extracted.get("name",""), extracted.get("date",""), extracted.get("location",""), extracted.get("people",""), msg)
                reply = ai_reply(msg) or f"✅ Got it! Saved appointment for {extracted.get('service')} - {extracted.get('date')} {extracted.get('location')}. We'll confirm! Type Menu"
            else:
                ai = ai_reply(msg)
                reply = ai or WELCOME
                # Still save if looks like booking
                if any(k in low for k in ["book","appointment","need","tomorrow","today","airport","cinema"]):
                    save_full(sender,"Appointment","","","","",msg)

        send(sender, reply)
        return jsonify({"status":"sent"}),200
    except Exception as e:
        log(f"EXC {e}"); return jsonify({"ok":True}),200

@app.route("/")
def home(): return "Kahlel V7 Full Appointments"
@app.route("/health")
def health(): return jsonify({"groq":bool(GROQ_API_KEY and "gsk_" in GROQ_API_KEY),"sheet":bool(SHEET_URL)})

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
