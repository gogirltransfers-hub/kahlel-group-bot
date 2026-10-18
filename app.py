import os
import requests
from flask import Flask, request, jsonify
from groq import Groq
from datetime import datetime, timedelta
from collections import defaultdict, Counter

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
D7_API_TOKEN = os.getenv("D7_API_TOKEN")
D7_WHATSAPP_NUMBER = "+264817491383"
ADMIN_PIN = os.getenv("ADMIN_PIN", "007")
ADMIN_NUMBERS = ["+264817491383"]

user_sessions = {}
stats = {"total": 0, "today": 0, "languages": Counter()}

# Language detection
def detect_lang(text):
    text = text.lower()
    if any(w in text for w in ["hallo", "hoe", "dankie", "afrikaans"]):
        return "af"
    if any(w in text for w in ["mhoro", "ndapota", "shona"]):
        return "sn"
    if any(w in text for w in ["dumelang", "osh", "oshiwambo"]):
        return "ov"
    return "en"

# AI reply
def get_ai_reply(message, lang="en", phone=""):
    try:
        client = Groq(api_key=GROQ_API_KEY)
        system_prompt = f"""You are Kahlel Group Assistant, for GoGirl Transfers, Kahlel Luxury Shuttle, Kahlel Auto.
Language: {lang}. Keep replies short, friendly, with prices in NAD.
Services: Airport transfer N$350, Windhoek city N$150, Luxury shuttle N$800/day, Car sales.
Always ask how to help."""
        
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            max_tokens=300
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"AI Error: {e}")
        return "Dumelang! How can I assist you today with transfers or shuttles?"

# Send WhatsApp via D7
def send_whatsapp(to, message):
    try:
        url = "https://api.d7networks.com/whatsapp/v2/send"
        headers = {
            "Authorization": f"Bearer {D7_API_TOKEN}",
            "Content-Type": "application/json"
        }
        data = {
            "to": to,
            "from": D7_WHATSAPP_NUMBER,
            "type": "text",
            "text": message,
            "channel": "whatsapp"
        }
        r = requests.post(url, headers=headers, json=data, timeout=10)
        print(f"D7 Send to {to}: {r.status_code} - {r.text[:200]}")
        return r.status_code in [200, 201]
    except Exception as e:
        print(f"Send Error: {e}")
        return False

@app.route("/")
def home():
    return "Kahlel Group Bot is LIVE! 007 - Ready for D7 WhatsApp"

@app.route("/webhook", methods=["POST", "GET"])
def webhook():
    if request.method == "GET":
        return "Webhook Ready - Use POST from D7", 200
    
    try:
        data = request.get_json(force=True)
        print(f"Incoming: {data}")
        
        # D7 format parsing
        message_text = ""
        from_number = ""
        
        if isinstance(data, dict):
            # Try common D7 fields
            from_number = data.get("from") or data.get("sender") or data.get("mobile") or ""
            if isinstance(from_number, dict):
                from_number = from_number.get("number") or from_number.get("phone") or ""
            
            # Get message text
            if "message" in data:
                if isinstance(data["message"], str):
                    message_text = data["message"]
                elif isinstance(data["message"], dict):
                    message_text = data["message"].get("text") or data["message"].get("body") or ""
            message_text = message_text or data.get("text") or data.get("body") or data.get("content") or ""
            
            # Nested data
            if not message_text and "data" in data:
                nested = data["data"]
                if isinstance(nested, dict):
                    message_text = nested.get("text") or nested.get("message") or ""
                    from_number = from_number or nested.get("from") or ""
        
        if not message_text or not from_number:
            print(f"Missing fields - from: {from_number}, text: {message_text}")
            return jsonify({"status": "ignored - missing fields"}), 200
        
        # Clean number
        from_number = str(from_number).replace(" ", "").replace("-", "")
        if not from_number.startswith("+"):
            from_number = "+" + from_number
        
        print(f"Processing: {from_number} says: {message_text}")
        
        lang = detect_lang(message_text)
        stats["total"] += 1
        stats["today"] += 1
        stats["languages"][lang] += 1
        
        # Admin commands
        if message_text.strip() == ADMIN_PIN:
            reply = f"Admin Mode ON 007\nTotal chats: {stats['total']}\nToday: {stats['today']}\nLangs: {dict(stats['languages'])}"
            send_whatsapp(from_number, reply)
            return jsonify({"status": "admin"}), 200
        
        reply = get_ai_reply(message_text, lang, from_number)
        send_whatsapp(from_number, reply)
        
        return jsonify({"status": "sent", "to": from_number}), 200
        
    except Exception as e:
        print(f"Webhook Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 200

@app.route("/health")
def health():
    return jsonify({"status": "ok", "time": str(datetime.now())})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
