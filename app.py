import os, requests, json
from flask import Flask, request, jsonify
from groq import Groq

app = Flask(__name__)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
D7_API_TOKEN = os.getenv("D7_API_TOKEN")
D7_NUMBER = "+264817491383"

def log(m): print(m, flush=True)

WELCOME = """👉Welcome to Kahlel Group! 👋
1️⃣ 🤖 Kahlel AI - Robotics & Automation
2️⃣ 🎬 Kahlel Flix - Outdoor Cinema
3️⃣ ✈️ Afri-Ka Travels - Travel & Tours
4️⃣ 📺 Vivid Graphix - LED Display & Signage
Reply 1-4 or type name"""

MENU1 = """🤖 *Kahlel AI - Robotics & Automation*
We build WhatsApp AI Bots like this one!
- Business automation
- AI assistants
- From N$1500 setup
What business do you want to automate?
Type *Menu* to go back"""

MENU2 = """🎬 *Kahlel Flix - Outdoor Cinema*
- Screen + projector + sound
- Birthdays, weddings, schools
- N$1500 - N$5000
We bring cinema to YOU!
Type *Menu* to go back"""

MENU3 = """✈️ *Afri-Ka Travels - GoGirl Transfers*
- Airport: N$350
- City: N$150
- Luxury: N$800/day
- Female drivers available!
Send your pickup location to book!
Type *Menu* to go back"""

MENU4 = """📺 *Vivid Graphix - LED Display & Signage*
- LED screens for events
- Shop signs & branding
- Digital displays
Tell me what you need!
Type *Menu* to go back"""

def send(to, text):
    try:
        to_clean = "+" + str(to).strip().lstrip("+")
        url="https://api.d7networks.com/whatsapp/v2/send"
        headers={"Authorization": f"Bearer {D7_API_TOKEN}", "Content-Type":"application/json"}
        payload={"messages":[{"originator":D7_NUMBER,"content":{"message_type":"TEXT","text":{"body":text}},"recipients":[{"recipient":to_clean,"recipient_type":"individual"}]}]}
        r=requests.post(url, headers=headers, json=payload, timeout=15)
        print(f"SEND {r.status_code}", flush=True)
        return True
    except Exception as e:
        print(f"SEND ERR {e}", flush=True)
        return False

@app.route("/webhook", methods=["POST","GET"])
def webhook():
    if request.method=="GET": return "Ready",200
    try:
        raw=request.get_data(as_text=True)
        print(f"RAW {raw[:1500]}", flush=True)
        data=json.loads(raw) if raw else {}
        sender=""; msg=""
        if "event_content" in data:
            m=data["event_content"].get("message",{})
            sender=m.get("originator","")
            txt=m.get("text",{})
            msg=txt.get("body","") if isinstance(txt,dict) else str(txt)
        if not sender or not msg:
            return jsonify({"status":"no data"}),200
        sender="+"+str(sender).strip().lstrip("+")
        original=msg.strip()
        low=original.lower()
        print(f"USER SENT: '{original}' -> low='{low}'", flush=True)

        # FIXED LOGIC - CHECK NUMBER FIRST!
        if low == "1" or low.startswith("1 ") or low == "1️⃣":
            reply=MENU1
            print("BRANCH 1", flush=True)
        elif low == "2" or low.startswith("2 "):
            reply=MENU2
            print("BRANCH 2", flush=True)
        elif low == "3" or low.startswith("3 "):
            reply=MENU3
            print("BRANCH 3", flush=True)
        elif low == "4" or low.startswith("4 "):
            reply=MENU4
            print("BRANCH 4", flush=True)
        elif "kahlel ai" in low or low=="ai" or "robot" in low or "automation" in low:
            reply=MENU1
        elif "flix" in low or "cinema" in low or "movie" in low:
            reply=MENU2
        elif "afri" in low or "travel" in low or "gogirl" in low or "transfer" in low:
            reply=MENU3
        elif "vivid" in low or "led" in low or "signage" in low or "graphix" in low:
            reply=MENU4
        else:
            # Only show welcome for hello/menu
            if low in ["hello","hi","hey","dumelang","menu","start","0","welcome","help"]:
                reply=WELCOME
            else:
                # For anything else, try Groq then menu
                try:
                    client=Groq(api_key=GROQ_API_KEY)
                    c=client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role":"system","content":"You are Kahlel Group assistant, short friendly"},{"role":"user","content":original}], max_tokens=200)
                    reply=c.choices[0].message.content
                except:
                    reply=WELCOME+"\n\nReply 1-4 please"

        print(f"REPLYING: {reply[:100]}", flush=True)
        send(sender, reply)
        return jsonify({"status":"sent"}),200
    except Exception as e:
        print(f"ERR {e}", flush=True)
        import traceback; traceback.print_exc()
        return jsonify({"ok":True}),200

@app.route("/")
def home(): return "Kahlel Bot Menu FIXED V2"
@app.route("/health")
def health(): return jsonify({"ok":True})

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
