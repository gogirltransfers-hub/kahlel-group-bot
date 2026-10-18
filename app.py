import os, requests
from flask import Flask, request, jsonify
from groq import Groq

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
D7_API_TOKEN = os.getenv("D7_API_TOKEN")
D7_NUMBER = "+264817491383"
ADMIN_PIN = os.getenv("ADMIN_PIN", "007")

def get_reply(msg):
    try:
        client = Groq(api_key=GROQ_API_KEY)
        c = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are Kahlel Group Assistant. GoGirl Transfers N$350 airport, N$150 city, Luxury N$800/day. Be short friendly."},
                {"role": "user", "content": msg}
            ],
            max_tokens=250
        )
        return c.choices[0].message.content
    except Exception as e:
        print(f"Groq error: {e}")
        return "Dumelang! How can I help with transfers today?"

def send_whatsapp(to, text):
    try:
        url = "https://api.d7networks.com/whatsapp/v2/send"
        headers = {"Authorization": f"Bearer {D7_API_TOKEN}", "Content-Type": "application/json"}
        payload = {
            "messages": [{
                "originator": D7_NUMBER,
                "content": {"message_type": "TEXT", "text": {"body": text}},
                "recipients": [{"recipient": to, "recipient_type": "individual"}]
            }]
        }
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        print(f"D7 SEND to {to}: {r.status_code} - {r.text[:500]}")
        return r.status_code in [200, 201]
    except Exception as e:
        print(f"Send error: {e}")
        return False

@app.route("/")
def home():
    return "Kahlel Bot LIVE! 007"

@app.route("/webhook", methods=["POST", "GET"])
def webhook():
    if request.method == "GET":
        return "Webhook Ready", 200
    try:
        data = request.get_json(force=True)
        print(f"WEBHOOK DATA: {data}")
        msg = ""
        sender = ""
        if isinstance(data, dict):
            # D7 inbound format
            if "messages" in data:
                m = data["messages"][0] if isinstance(data["messages"], list) else data
                sender = m.get("from") or m.get("originator") or ""
                content = m.get("content") or {}
                msg = content.get("text") or content.get("body") or m.get("text") or ""
            else:
                sender = data.get("from") or data.get("sender") or data.get("mobile") or ""
                msg = data.get("text") or data.get("body") or data.get("message") or ""
                if isinstance(msg, dict):
                    msg = msg.get("text") or msg.get("body") or ""
                if isinstance(sender, dict):
                    sender = sender.get("number") or ""
        if not msg or not sender:
            print(f"Missing - sender:{sender} msg:{msg}")
            return jsonify({"status": "ignored"}), 200
        sender = str(sender).replace(" ", "")
        if not sender.startswith("+"):
            sender = "+" + sender
        print(f"REPLYING to {sender}: {msg}")
        if str(msg).strip() == ADMIN_PIN:
            send_whatsapp(sender, "Admin ON 007")
            return jsonify({"status": "admin"}), 200
        reply = get_reply(str(msg))
        send_whatsapp(sender, reply)
        return jsonify({"status": "sent"}), 200
    except Exception as e:
        print(f"Webhook error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"ok": True}), 200

@app.route("/health")
def health():
    return jsonify({"ok": True})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
