import os, requests, json, re, time
from flask import Flask, request, jsonify
app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
D7_API_TOKEN = os.getenv("D7_API_TOKEN")
SHEET_URL = os.getenv("SHEET_WEBHOOK_URL")
D7_NUMBER = "+264817491383"
OWNER_NUMBER = "+264812945081"

def log(m): print(m, flush=True)

# --- SESSION MEMORY TO STOP LOOP ---
SESSION = {}

# --- NEW GROQ MODELS (old llama 3.3 is dead) ---
MODELS = ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "llama-3.1-8b-instant"]

WELCOME = """👉Welcome to Kahlel Group! 👋
1️⃣ 🤖 Kahlel AI - Robotics & Automation
2️⃣ 🎬 Kahlel Flix - Outdoor Cinema
3️⃣ ✈️ Afri-Ka Travel - Travel & Tours
4️⃣ 📺 Vivid Graphix - LED Display & Signage

Reply 1-4 or type your booking (e.g. Book Afri-Ka tomorrow 5am, name Leon)
Type MENU to go back"""

MENUS = {
 "1": "🤖 Kahlel AI\nWebsite: www.kahlel-ai.com\nBots from N$1500 + N$500/mo\n\nWhat business?\nReply Menu",
 "2": "🎬 Kahlel Flix\nWebsite: www.kahlelflix.com\nSmall N$1500 (30 ppl)\nMedium N$2500 (80 ppl)\nLarge N$4000 (150+ ppl)\nProjector+Sound+Screen\n\nWhen is event?\nReply Menu",
 "3": "✈️ Afri-Ka Travel\nWebsite: www.afri-katours.com\nAirport N$350 | City N$150-250\n24/7 female drivers, safe, child seats\n\nSend pickup FROM-TO + Date/Time + Name?\nReply Menu",
 "4": "📺 Vivid Graphix\nWebsite: www.kahlel.co.za\nLED N$2000/day, stage, signage, branding\n\nWhat size?\nReply Menu"
}

def hard_extract(msg, last_service=None):
    low=msg.lower()
    service=last_service or "GoGirl Afri-Ka Travel"
    if "flix" in low and "gogirl" not in low and "airport" not in low:
        service="Kahlel Flix"
    elif "vivid" in low or ("led" in low and "airport" not in low):
        service="Vivid Graphix"
    elif "kahlel ai" in low or ("bot" in low and "airport" not in low):
        service="Kahlel AI"
    if any(k in low for k in ["gogirl","afri-ka","afrika","airport","hosea kutako","transfer"]):
        service="GoGirl Afri-Ka Travel"
    name=""; people=""; date=""; location=""
    m=re.search(r'name\s*[:=]?\s*([A-Za-z]+)', msg, re.I)
    if m: name=m.group(1).capitalize()
    m=re.search(r'(\d+)\s*people', low)
    if m: people=m.group(1)
    # catches 6 november, 6th nov, nov 6
    m=re.search(r'(\d{1,2}(?:st|nd|rd|th)?\s*(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*|\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*\d{1,2}|tomorrow|today|\d+\s*am|\d+\s*pm)', low)
    if m: date=m.group(1)
    if not date and any(x in low for x in ["january","february","march","april","may","june","july","august","september","october","november","december"]):
        date=msg.strip()
    m=re.search(r'from\s+(.+?)\s+to\s+([^,]+?)(?:,|\s+name|\s+\d+\s+people|$)', msg, re.I)
    if m: location=f"{m.group(1).strip()} to {m.group(2).strip()}"
    log(f"REGEX {service}|{name}|{date}|{location}|{people} last={last_service}")
    return {"service":service,"name":name,"date":date,"location":location,"people":people}

def groq_extract_and_reply(msg, last_service=None):
    extracted=hard_extract(msg, last_service)
    smart_reply=None
    try:
        from groq import Groq
        if not GROQ_API_KEY or "gsk_" not in GROQ_API_KEY:
            log("No Groq key")
            return extracted, None
        client=Groq(api_key=GROQ_API_KEY)
        for MODEL in MODELS:
            try:
                prompt=f'Extract JSON only: Service=GoGirl Afri-Ka Travel|Kahlel Flix|Vivid Graphix|Kahlel AI, name, date, location, people from "{msg}". Last service {last_service}. Return {{"service":"","name":"","date":"","location":"","people":""}} only.'
                c=client.chat.completions.create(model=MODEL, messages=[{"role":"user","content":prompt}], max_tokens=300, temperature=0.1)
                txt=c.choices[0].message.content
                log(f"GROQ RAW {MODEL}: {txt}")
                m=re.search(r'\{{.*\}}', txt, re.DOTALL)
                if m:
                    gj=json.loads(m.group())
                    for k in ["name","date","location","people"]:
                        if gj.get(k): extracted[k]=gj[k]
                    if gj.get("service") and last_service is None and gj["service"]:
                        extracted["service"]=gj["service"]
                # smart reply
                sys_prompt=f"""You are Kahlel Group Namibia assistant. Last chosen service: {last_service or extracted['service']}.
1. Kahlel AI Website www.kahlel-ai.com N$1500+500/mo
2. Kahlel Flix Website www.kahlelflix.com Small N$1500 (30ppl) Medium N$2500 (80) Large N$4000 (150+). Includes projector+sound+screen. If user just gave date like '6 november' and last service is Kahlel Flix, DO NOT show main menu. Reply: 'Perfect! Kahlel Flix for 6 November. How many people, location/venue, and your name?' 
3. Afri-Ka Travel Website www.afri-katours.com Airport N$350 City N$150-250
4. Vivid Graphix Website www.kahlel.co.za LED N$2000/day
Be short, friendly. Don't loop to welcome if date given."""
                c2=client.chat.completions.create(model=MODEL, messages=[{"role":"system","content":sys_prompt},{"role":"user","content":msg}], max_tokens=350, temperature=0.6)
                smart_reply=c2.choices[0].message.content
                log(f"GROQ REPLY {MODEL}: {smart_reply[:150]}")
                break
            except Exception as e:
                log(f"Model {MODEL} fail {e}")
                continue
    except Exception as e:
        log(f"Groq lib err {e}")
    return extracted, smart_reply

def save_full(phone, service, name, date, location, people, message):
    try:
        payload={"phone":phone,"service":service,"name":name,"date":date,"location":location,"people":people,"message":message}
        r=requests.post(SHEET_URL, json=payload, timeout=10)
        log(f"SAVED {service}|{name}|{date}|{location}|{people} {r.status_code}")
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
    if request.method=="GET": return "V16 FIXED MODEL gpt-oss-20b + No Loop",200
    try:
        raw=request.get_data(as_text=True); data=json.loads(raw) if raw else {}
        sender=""; msg=""
        if "event_content" in data:
            m=data["event_content"].get("message",{}); sender=m.get("originator",""); txt=m.get("text",{}); msg=txt.get("body","") if isinstance(txt,dict) else str(txt)
        if not sender or not msg: return jsonify({"status":"ignored"}),200
        sender="+"+str(sender).strip().lstrip("+"); low=msg.lower().strip()
        log(f"USER: {msg} sess={SESSION.get(sender)}")
        
        MONTHS = ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]
        has_month = any(x in low for x in MONTHS)
        is_date_short = bool(re.search(r'\d+\s*(nov|dec|jan|feb|mar|apr|may|jun|jul|aug|sep|oct)', low))
        
        is_booking = len(msg.split())>=2 and (any(k in low for k in ["appointment","book","tomorrow","today","name","from","people","am","pm","airport","transfer"]) or has_month or is_date_short or (SESSION.get(sender) and len(msg.split())>=1))

        if is_booking:
            last = SESSION.get(sender)
            extracted, smart = groq_extract_and_reply(msg, last)
            SESSION[sender] = extracted["service"]
            save_full(sender, extracted["service"], extracted["name"], extracted["date"] or msg, extracted["location"], extracted["people"], msg)
            reply = smart or f"Got it! {extracted['service']} for {extracted['date'] or msg}. How many people & venue? Name?"
            send(sender, reply)
        elif low in ["1","2","3","4"] and len(low)==1:
            mapping={"1":"Kahlel AI","2":"Kahlel Flix","3":"GoGirl Afri-Ka Travel","4":"Vivid Graphix"}
            sm=mapping[low]
            SESSION[sender]=sm
            save_full(sender, sm, "", "", "", "", f"Pressed {low}")
            send(sender, MENUS[low])
        elif low in ["hello","hi","menu","start","welcome"]:
            SESSION.pop(sender, None)
            send(sender, WELCOME)
        else:
            last = SESSION.get(sender)
            _, smart = groq_extract_and_reply(msg, last)
            send(sender, smart or WELCOME)
        return jsonify({"status":"sent"}),200
    except Exception as e:
        log(f"EXC {e}"); return jsonify({"ok":True}),200

@app.route("/")
def home(): return "V16 FIXED gpt-oss-20b Afri-Ka www.afri-katours.com"
@app.route("/health")
def health(): return jsonify({"groq":bool(GROQ_API_KEY and "gsk_" in GROQ_API_KEY),"sheet":bool(SHEET_URL),"model":MODELS[0]})

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
