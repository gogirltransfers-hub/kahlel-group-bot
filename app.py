from flask import Flask, request, jsonify
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# D7 Networks config
D7_API_KEY = 'your_d7_api_key'
D7_URL = 'https://api.d7networks.com/whatsapp/v1/messages'

# Google Sheets config
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('creds.json', scope)
client = gspread.authorize(creds)
sheet = client.open('KahlelFlixLogs').sheet1

# Retell AI config
RESELL_AI_URL = 'your_retell_ai_url'

@app.route('/webhook', methods=['POST'])
def webhook():
    msg = request.json['message']
    phone = msg['from']
    text = msg['text'].strip().lower()

    # Log in Google Sheets
    sheet.append_row([phone, text, ''])

    if text == 'hi' or text == 'hello':
        reply = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone,
            "type": "text",
            "text": {
                "body": "👉 🎬 *Saturday Double Feature!*\n1. The Lion King\n2. Notebook\n\n*VIP Members*: N$24.75 only!\nReply:\n- BOOK (tickets)\n- VIP (membership)"
            }
        }
    elif text == 'book':
        reply = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone,
            "type": "text",
            "text": {
                "body": "✅ Seats reserved!\nLink: kahlelgroup.com/tickets\n\n*Want VIP deals?* Reply VIP"
            }
        }
    elif text == 'vip':
        reply = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone,
            "type": "text",
            "text": {
                "body": "🔥 *VIP Membership*: N$24.75 Saturday only!\nLink: kahlelgroup.com/vip\n\nReply BOOK to reserve"
            }
        }
    else:
        # Retell AI fallback
        r = requests.post(RESELL_AI_URL, json={'text': text})
        reply_text = r.json()['reply']
        reply = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone,
            "type": "text",
            "text": {
                "body": reply_text
            }
        }

    # Send via D7
    headers = {'Authorization': f'Bearer {D7_API_KEY}'}
    requests.post(D7_URL, json=reply, headers=headers)

    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True)
