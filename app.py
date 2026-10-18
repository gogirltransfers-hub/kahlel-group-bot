import os, requests, json, sys
from flask import Flask, request, jsonify
from groq import Groq

app = Flask(__name__)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
D7_API_TOKEN = os.getenv("D7_API_TOKEN")
D7_NUMBER = "+264817491383"

def log(m):
    print(m, flush=True)

WELCOME_MENU = """👉Welcome to Kahlel Group! 👋

1️⃣ 🤖 Kahlel AI - Robotics & Automation
2️⃣ 🎬 Kahlel Flix - Outdoor Cinema  
3️⃣ ✈️ Afri-Ka Travels - Travel & Tours
4️⃣ 📺 Vivid Graphix - LED Display & Signage

Reply 1-4 or type name"""

MENUS = {
    "1": """🤖 *Kahlel AI - Robotics & Automation*
We build:
• WhatsApp AI Bots (like this one!)
• GoGirl Transfers automation
• Custom business AI assistants

Cost: From N$1500 setup
Type *Kahlel AI* to learn more or *Menu* to go back""",
    "2": """🎬 *Kahlel Flix - Outdoor Cinema*
• Inflatable screen + projector + sound
• Perfect for birthdays, weddings, schools
• Packages: N$1500 - N$5000

We bring cinema to YOU!
Type *Flix* to book or *Menu* to go back""",
    "3": """✈️ *Afri-Ka Travels & GoGirl Transfers*
• Airport transfers: N$350
• City rides: N$150  
• Luxury tours: N$800/day
• Female drivers available

Type your pickup location or *Menu* to go back""",
    "4": """📺 *Vivid Graphix - LED & Signage*
• LED screens for events
• Shop signs, branding
• Digital displays

Get a quote now!
Type *Vivid* for quote or *Menu* to go back"""
}

def get_ai_reply(msg):
    try:
        client = Groq(api_key=GROQ_API_KEY)
        c = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role":"system","content":f"You are Kahlel Group Assistant. Menu: {WELCOME_MENU}. Services details: {MENUS}. Always be short, friendly, Namibian vibe. If user asks for service, give details. If confused, show Menu."},
                {"role":"user","content":msg}
            ],
            max_tokens=300
        )
        return c.choices[0].message.content
    except Exception as e:
        log(f"Groq error {e}")
        return None

def send_whatsapp(to, text):
    try:
        to_clean = str(to).replace(" ","")
        if not to_clean.startswith("+"):
            to_clean = "+" + to_clean
        url = "https://api.d7networks.com/whatsapp/v2/send"
        headers = {"Authorization": f"Bearer {D7_API_TOKEN}", "Content-Type": "application/json"}
        payload = {"messages": [{"originator": D7_NUMBER,"content": {"message_type":"TEXT","text":{"body":text}},"recipients": [{"recipient": to_clean,"recipient_type":"individual"}]}]}
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        log(f"SEND {r.status_code} {r.text[:500]}")
        return True
    except Exception as e:
        log(f"SEND ERR {e}")
        return False

@app.route("/")
def home():
    return "Kahlel Bot with Menu LIVE"

@app.route("/webhook", methods=["POST","GET"])
def webhook():
    if request.method=="GET":
        return "Webhook Ready",200
    try:
        raw = request.get_data(as_text=True)
        log(f"RAW: {raw[:2000]}")
        data = json.loads(raw) if raw else {}
        sender=""; msg=""
        if "event_content" in data and "message" in data["event_content"]:
            m = data["event_content"]["message"]
            sender = m.get("originator") or ""
            txt = m.get("text") or {}
            msg = txt.get("body") if isinstance(txt, dict) else str(txt)
        if not sender or not msg:
            return jsonify({"status":"ignored"}),200
        sender = "+" + str(sender).strip().lstrip("+")
        text = str(msg).strip().lower()
        log(f"From {sender}: {msg} -> lower: {text}")

        reply = ""
        # MENU LOGIC
        if text in ["hello","hi","hey","dumelang","menu","start","0","welcome"] or len(text)<2:
            reply = WELCOME_MENU
        elif text in ["1","1️⃣","kahlel ai","ai","robotics","automation","bot"]:
            reply = MENUS["1"]
        elif text in ["2","2️⃣","kahlel flix","flix","cinema","outdoor","movie"]:
            reply = MENUS["2"]
        elif text in ["3","3️⃣","afrika","afri-ka","travels","travel","gogirl","transfer","ride"]:
            reply = MENUS["3"]
        elif text in ["4","4️⃣","vivid","vivid graphix","led","signage","display"]:
            reply = MENUS["4"]
        else:
            # Try Groq AI, fallback to menu
            ai = get_ai_reply(msg)
            if ai:
                reply = ai
            else:
                # If user typed 1-4 in sentence
                if "1" in text: reply = MENUS["1"]
                elif "2" in text: reply = MENUS["2"]
                elif "3" in text: reply = MENUS["3"]
                elif "4" in text: reply = MENUS["4"]
                else: reply = WELCOME_MENU + "\n\nI didn't understand - Reply 1-4 please"

        log(f"REPLY: {reply[:200]}")
        send_whatsapp(sender, reply)
        return jsonify({"status":"sent"}),200
    except Exception as e:
        log(f"EXC {e}")
        import traceback; traceback.print_exc()
        return jsonify({"ok":True}),200

@app.route("/health")
def health():
    return jsonify({"ok":True})

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
