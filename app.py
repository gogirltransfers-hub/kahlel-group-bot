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

MENU_1 = """🤖 *Kahlel AI - Robotics & Automation*
We build WhatsApp AI Bots (like this one!)
✅ Business automation
✅ AI assistants
💰 From N$1500 setup

What business do you want to automate?
Reply *Menu* for main menu"""

MENU_2 = """🎬 *Kahlel Flix - Outdoor Cinema*
✅ Inflatable 5m screen + HD projector + sound
👥 Packages:
• Small N$1500 (30 people)
• Medium N$2500 (80 people)  
• Large N$4000 (150+ people)
📍 Free transport in Windhoek

When is your event?
Reply *Menu* for main menu"""

MENU_3 = """✈️ *Afri-Ka Travels & GoGirl Transfers*
✅ Airport Hosea Kutako: N$350 (1-3 ppl)
✅ City rides Windhoek: N$150-N$250
✅ Luxury tours: N$800/day
👩 Female drivers (GoGirl) available - safe!
⏰ 24/7 - Book 2hrs ahead

Send your pickup location to book!
Reply *Menu* for main menu"""

MENU_4 = """📺 *Vivid Graphix - LED Display & Signage*
✅ LED screens rental N$2000/day for events
✅ Shop signs, lightbox, 3D letters
✅ Branding, vehicle wraps
📍 Free site visit in Windhoek

What do you need? Send details!
Reply *Menu* for main menu"""

def ai_reply(msg):
    try:
        if not GROQ_API_KEY or not GROQ_API_KEY.startswith("gsk_"):
            return None
        client = Groq(api_key=GROQ_API_KEY)
        c = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role":"system","content":"You are Kahlel Group assistant Namibia. Services: 1) Kahlel AI bots N$1500+, 2) Flix cinema N$1500-4000, 3) GoGirl airport N$350 city N$150 24/7, 4) Vivid LED N$2000/day. Be short friendly. End with Type Menu."},
                {"role":"user","content":msg}
            ],
            max_tokens=300
        )
        return c.choices[0].message.content
    except Exception as e:
        log(f"Groq error {e}")
        return None

def save_to_sheet(phone, service, message):
    if not SHEET_URL: return
    try:
        requests.post(SHEET_URL, json={"phone":phone,"service":service,"name":"","date":"","location":"","people":"","message":message}, timeout=8)
        log(f"Saved to sheet {service}")
    except: pass

def send(to, text):
    try:
        to_clean = "+" + str(to).strip().lstrip("+")
        url="https://api.d7networks.com/whatsapp/v2/send"
        headers={"Authorization": f"Bearer {D7_API_TOKEN}", "Content-Type":"application/json"}
        payload={"messages":[{"originator":D7_NUMBER,"content":{"message_type":"TEXT","text":{"body":text[:1000]}},"recipients":[{"recipient":to_clean,"recipient_type":"individual"}]}]}
        r=requests.post(url, headers=headers, json=payload, timeout=15)
        log(f"SEND {r.status_code}")
    except Exception as e:
        log(f"SEND ERR {e}")

@app.route("/webhook", methods=["POST","GET"])
def webhook():
    if request.method=="GET": return "Kahlel Fixed V5",200
    try:
        raw=request.get_data(as_text=True)
        data=json.loads(raw) if raw else {}
        sender=""; msg=""
        if "event_content" in data:
            m=data["event_content"].get("message",{})
            sender=m.get("originator","")
            txt=m.get("text",{})
            msg=txt.get("body","") if isinstance(txt,dict) else str(txt)
        if not sender or not msg:
            return jsonify({"status":"ignored"}),200
        
        sender="+"+str(sender).strip().lstrip("+")
        original=msg.strip()
        low=original.lower()
        log(f"USER '{original}' low='{low}'")

        # === STEP 1: HANDLE 1,2,3,4 FIRST - NO AI NEEDED! ===
        if low == "1" or low.startswith("1 ") or low == "1️⃣" or "kahlel ai" in low:
            reply = MENU_1
            save_to_sheet(sender, "Kahlel AI", original)
        elif low == "2" or low.startswith("2 ") or low == "2️⃣" or "kahlel flix" in low or low=="flix":
            reply = MENU_2
            save_to_sheet(sender, "Kahlel Flix", original)
        elif low == "3" or low.startswith("3 ") or low == "3️⃣" or "afri" in low or "gogirl" in low or "travel" in low:
            reply = MENU_3
            save_to_sheet(sender, "GoGirl Travel", original)
        elif low == "4" or low.startswith("4 ") or low == "4️⃣" or "vivid" in low or "led" in low:
            reply = MENU_4
            save_to_sheet(sender, "Vivid Graphix", original)
        elif low in ["hello","hi","hey","dumelang","menu","start","0","welcome","help","hi there"]:
            reply = WELCOME
        else:
            # For other questions, try AI, else welcome
            ai = ai_reply(original)
            reply = ai if ai else WELCOME + "\n\nReply 1-4 to explore!"

        log(f"REPLY: {reply[:120]}")
        send(sender, reply)
        return jsonify({"status":"sent"}),200
    except Exception as e:
        log(f"EXC {e}")
        import traceback; traceback.print_exc()
        return jsonify({"ok":True}),200

@app.route("/")
def home(): return "Kahlel FIXED V5 - 1,2,3,4 works without AI"
@app.route("/health")
def health(): return jsonify({"ok":True})

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
