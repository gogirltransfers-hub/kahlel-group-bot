import os, requests, json, sys
from flask import Flask, request, jsonify
from groq import Groq

app = Flask(__name__)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
D7_API_TOKEN = os.getenv("D7_API_TOKEN")
D7_NUMBER = "+264817491383"

def log(msg):
    print(msg, flush=True)
    sys.stdout.flush()

def get_reply(msg):
    try:
        client = Groq(api_key=GROQ_API_KEY)
        c = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role":"system","content":"You are Kahlel Group Assistant. GoGirl N$350 airport. Short friendly."},{"role":"user","content":msg}],
            max_tokens=200
        )
        return c.choices[0].message.content
    except Exception as e:
        log(f"GROQ ERR {e}")
        return "Dumelang! How can I help?"

def send_whatsapp(to, text):
    try:
        url="https://api.d7networks.com/whatsapp/v2/send"
        headers={"Authorization": f"Bearer {D7_API_TOKEN}", "Content-Type":"application/json"}
        payload={"messages":[{"originator":D7_NUMBER,"content":{"message_type":"TEXT","text":{"body":text}},"recipients":[{"recipient":to,"recipient_type":"individual"}]}]}
        r=requests.post(url, headers=headers, json=payload, timeout=15)
        log(f"SEND to {to} => {r.status_code} {r.text[:800]}")
        return True
    except Exception as e:
        log(f"SEND ERR {e}")
        return False

@app.route("/")
def home():
    return "Kahlel Bot LIVE DEBUG"

@app.route("/webhook", methods=["POST","GET"])
def webhook():
    if request.method=="GET":
        return "Webhook Ready",200
    try:
        raw = request.get_data(as_text=True)
        log(f"==== WEBHOOK RAW DATA ====\n{raw[:3000]}\n====")
        # Save to file
        try:
            with open("/tmp/last.json","w") as f:
                f.write(raw)
        except:
            pass
        data = {}
        try:
            data = json.loads(raw) if raw else {}
        except:
            data = request.get_json(force=True, silent=True) or {}
        log(f"PARSED JSON: {json.dumps(data)[:2000]}")
        # Extract
        sender=""; msg=""
        # Try many formats
        if isinstance(data, dict):
            # common D7 inbound: messages array
            if "messages" in data and isinstance(data["messages"], list):
                m=data["messages"][0]
                sender=m.get("from") or m.get("originator") or m.get("sender") or ""
                # content may be nested
                cont=m.get("content") or {}
                if isinstance(cont, dict):
                    txt=cont.get("text") or cont.get("body") or {}
                    if isinstance(txt, dict):
                        msg=txt.get("body") or txt.get("text") or ""
                    else:
                        msg=str(txt)
                msg = msg or m.get("text") or m.get("body") or ""
            # Try root
            if not sender:
                sender=data.get("from") or data.get("sender") or data.get("phone") or ""
            if not msg:
                msg=data.get("text") or data.get("body") or data.get("message") or ""
                if isinstance(msg, dict):
                    msg=msg.get("body") or msg.get("text") or ""
        log(f"EXTRACTED sender={sender} msg={msg}")
        if not msg:
            # If still no msg, try to find any text field in raw
            log("No msg found, using raw as msg for test")
            msg = raw[:500] if raw else "Hello"
        if not sender:
            log("No sender found - cannot reply, but will try test send")
            return jsonify({"status":"no sender"}),200
        sender=str(sender).replace(" ","")
        if not sender.startswith("+"):
            sender="+"+sender
        log(f"REPLYING to {sender}")
        reply=get_reply(str(msg))
        log(f"REPLY TEXT: {reply}")
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
            return f.read(), 200, {'Content-Type':'application/json'}
    except:
        return "No webhook yet",200

@app.route("/test")
def test_send():
    to=request.args.get("to")
    if not to:
        return "Use /test?to=+2648..."
    send_whatsapp(to, "Test OK from Kahlel Bot - SEND works!")
    return f"Test sent to {to} - check phone + Render logs"

@app.route("/health")
def health():
    return jsonify({"ok":True})

if __name__=="__main__":
    port=int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0",port=port)
