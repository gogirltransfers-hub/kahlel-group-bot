import os, requests, json, sys
from flask import Flask, request, jsonify
from groq import Groq

app = Flask(__name__)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
D7_API_TOKEN = os.getenv("D7_API_TOKEN")
D7_NUMBER = "+264817491383"

def log(m):
    print(m, flush=True)

def get_reply(msg):
    try:
        client = Groq(api_key=GROQ_API_KEY)
        c = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role":"system","content":"You are Kahlel Group Assistant for GoGirl Transfers in Windhoek. Services: Airport N$350, City N$150, Luxury N$800/day. Be short, friendly, helpful."},
                {"role":"user","content":msg}
            ],
            max_tokens=250
        )
        return c.choices[0].message.content
    except Exception as e:
        log(f"Groq error {e}")
        return "Dumelang Leon! I can help with GoGirl airport transfers N$350, city rides N$150. What do you need?"

def send_whatsapp(to, text):
    try:
        # Ensure + prefix
        to_clean = str(to).replace(" ","").replace("-","")
        if not to_clean.startswith("+"):
            to_clean = "+" + to_clean
        url = "https://api.d7networks.com/whatsapp/v2/send"
        headers = {"Authorization": f"Bearer {D7_API_TOKEN}", "Content-Type": "application/json"}
        payload = {
            "messages": [{
                "originator": D7_NUMBER,
                "content": {"message_type": "TEXT", "text": {"body": text}},
                "recipients": [{"recipient": to_clean, "recipient_type": "individual"}]
            }]
        }
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        log(f"SEND to {to_clean} => {r.status_code} {r.text[:800]}")
        return r.status_code in [200,201]
    except Exception as e:
        log(f"SEND ERR {e}")
        return False

@app.route("/")
def home():
    return "Kahlel Bot LIVE FINAL"

@app.route("/webhook", methods=["POST","GET"])
def webhook():
    if request.method == "GET":
        return "Webhook Ready",200
    try:
        raw = request.get_data(as_text=True)
        log(f"RAW: {raw[:2000]}")
        data = json.loads(raw) if raw else {}
        
        sender = ""
        msg = ""
        
        # REAL D7 FORMAT (from your log)
        # data.event_content.message.originator = sender
        # data.event_content.message.text.body = msg
        try:
            if "event_content" in data and "message" in data["event_content"]:
                m = data["event_content"]["message"]
                sender = m.get("originator") or ""
                txt = m.get("text") or {}
                if isinstance(txt, dict):
                    msg = txt.get("body") or ""
                else:
                    msg = str(txt)
                log(f"Found in event_content.message: sender={sender} msg={msg}")
        except Exception as e:
            log(f"Parse event_content error {e}")

        # Fallback for other formats
        if not sender and "messages" in data:
            try:
                m = data["messages"][0]
                sender = m.get("from") or ""
                msg = m.get("text") or ""
            except:
                pass

        if not sender or not msg:
            log(f"Missing data sender={sender} msg={msg}")
            return jsonify({"status":"ignored no data"}),200

        sender = str(sender).strip()
        if not sender.startswith("+"):
            sender = "+" + sender
        
        log(f"PROCESSING {sender}: {msg}")
        reply = get_reply(str(msg))
        log(f"REPLY: {reply}")
        send_whatsapp(sender, reply)
        return jsonify({"status":"sent"}),200
    except Exception as e:
        log(f"WEBHOOK EXCEPTION {e}")
        import traceback; traceback.print_exc()
        return jsonify({"ok":True}),200

@app.route("/last")
def last():
    try:
        with open("/tmp/last.json","r") as f:
            return f.read(),200,{'Content-Type':'application/json'}
    except:
        return "No webhook yet",200

@app.route("/health")
def health():
    return jsonify({"ok":True})

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
