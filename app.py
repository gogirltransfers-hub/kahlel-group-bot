import os, requests, json, re
from datetime import datetime
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

KNOWLEDGE = """
You are Kahlel Group AI Agent Namibia.
Businesses:
1 Kahlel AI: WhatsApp bots N$1500-5000 setup, N$299-999/month. Builds automation.
2 Kahlel Flix: Outdoor cinema N$1500 (30ppl), N$2500 (80), N$4000-5000 (150+). Includes screen+projector+sound. Free Windhoek transport.
3 Afri-Ka GoGirl: Airport N$350 (1-3ppl) N$450 (4-7), City N$150-250, Luxury N$800/day. 24/7, female drivers, 2hrs advance booking.
4 Vivid Graphix: LED N$2000/day, signage, branding.

If user wants to BOOK, extract: service, name, date, location, people. Ask for missing info naturally. Be short friendly.
"""

# Simple memory per phone
user_state = {}

def ai_extract_booking(user_msg, phone):
    """Use Groq to extract booking details"""
    try:
        client = Groq(api_key=GROQ_API_KEY)
        prompt = f"""
Extract booking JSON from message: "{user_msg}"
Phone: {phone}
Return ONLY valid JSON: {{"service":"Kahlel AI|Flix|Travel|Vivid|unknown","name":"","date":"","location":"","people":"","has_booking_intent":true/false}}
If no booking intent, has_booking_intent false.
"""
        c = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role":"user","content":prompt}],
            max_tokens=200,
            temperature=0.1
        )
        txt = c.choices[0].message.content
        # Find JSON
        m = re.search(r'\{.*\}', txt, re.DOTALL)
        if m:
            return json.loads(m.group())
    except Exception as e:
        log(f"Extract err {e}")
    return {"has_booking_intent": False}

def ai_reply(msg, phone):
    try:
        client = Groq(api_key=GROQ_API_KEY)
        history = user_state.get(phone, {}).get("history","")
        c = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role":"system","content":KNOWLEDGE + f"\nHistory: {history[-300:]}"},
                {"role":"user","content":msg}
            ],
            max_tokens=350
        )
        return c.choices[0].message.content
    except Exception as e:
        log(f"Groq err {e}")
        return None

def save_to_sheet(phone, service, name, date, location, people, message):
    if not SHEET_URL:
        log("No SHEET_URL set")
        return False
    try:
        payload = {
            "phone": phone,
            "service": service,
            "name": name,
            "date": date,
            "location": location,
            "people": people,
            "message": message
        }
        r = requests.post(SHEET_URL, json=payload, timeout=10)
        log(f"SHEET SAVE {r.status_code} {r.text[:200]}")
        return r.status_code==200
    except Exception as e:
        log(f"Sheet err {e}")
        return False

def send(to, text):
    try:
        to_clean = "+" + str(to).strip().lstrip("+")
        url="https://api.d7networks.com/whatsapp/v2/send"
        headers={"Authorization": f"Bearer {D7_API_TOKEN}", "Content-Type":"application/json"}
        payload={"messages":[{"originator":D7_NUMBER,"content":{"message_type":"TEXT","text":{"body":text[:1000]}},"recipients":[{"recipient":to_clean,"recipient_type":"individual"}]}]}
        r=requests.post(url, headers=headers, json=payload, timeout=15)
        log(f"SEND {r.status_code}")
        return True
    except Exception as e:
        log(f"SEND ERR {e}")
        return False

@app.route("/webhook", methods=["POST","GET"])
def webhook():
    if request.method=="GET": return "Booking Agent Ready",200
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
        log(f"FROM {sender}: {msg}")

        # Init state
        if sender not in user_state:
            user_state[sender] = {"history":"", "book":{}}
        user_state[sender]["history"] += f"\nUser: {msg}"

        # Welcome
        if low in ["hello","hi","hey","dumelang","menu","start","0","welcome","help"]:
            reply=WELCOME
        else:
            # Check booking intent
            booking = ai_extract_booking(msg, sender)
            log(f"Booking extract: {booking}")
            
            if booking.get("has_booking_intent"):
                # Merge with existing
                b = user_state[sender].get("book",{})
                for k in ["service","name","date","location","people"]:
                    if booking.get(k): b[k]=booking[k]
                user_state[sender]["book"]=b
                
                # Save to sheet if we have enough
                if b.get("service") and (b.get("date") or b.get("location") or b.get("name")):
                    save_to_sheet(sender, b.get("service",""), b.get("name",""), b.get("date",""), b.get("location",""), b.get("people",""), msg)
                    log(f"BOOKING SAVED for {sender}")

            reply = ai_reply(msg, sender)
            if not reply:
                reply = WELCOME

        user_state[sender]["history"] += f"\nBot: {reply[:200]}"
        send(sender, reply)
        return jsonify({"status":"sent"}),200
    except Exception as e:
        log(f"EXC {e}")
        import traceback; traceback.print_exc()
        return jsonify({"ok":True}),200

@app.route("/")
def home(): return "Kahlel Booking Agent LIVE"
@app.route("/health")
def health(): return jsonify({"ok":True, "sheet_configured": bool(SHEET_URL)})

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
