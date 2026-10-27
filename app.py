import os, requests, json, re
from flask import Flask, request, jsonify
app = Flask(__name__)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
D7_API_TOKEN = os.getenv("D7_API_TOKEN")
SHEET_URL = os.getenv("SHEET_WEBHOOK_URL")
D7_NUMBER = "+264817491383"
def log(m): print(m, flush=True)
SESSION = {}
MODELS = ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "llama-3.1-8b-instant"]
CONTACT_PHONE = "+264812086309"
CONTACT_EMAIL = "info@kahlel.co.za"
def should_reveal_contact(msg):
    triggers = ["phone", "number", "contact", "call me", "email", "e-mail", "payment proof", "talk to human", "human", "agent", "reach you"]
    return any(k in msg.lower() for k in triggers)
def clean_whatsapp_text(t):
    if not t: return t
    t = re.sub(r'\[([^\]]+)\]\((https?://[^\)]+)\)', r'\2', t)
    t = re.sub(r'\((https://[^\)]+)\)', r'\n\1', t)
    t = re.sub(r'\|---.*', '', t)
    return t.strip()
HIDE_TEXT = "👉 Want to Talk to Live Agent? Just TYPE *Talk to Human* and I'll connect you to Leon live! 🍿"
REVEAL_TEXT = f"📞 Call Leon now: *0812086309* (clickable)"
RESERVE_LINK = "https://www.nam-events.com/explore/movie-magic-under-the-stars"
MEMBERSHIP_LINK = "https://kahlelflix.com/p/1065605/kahlel-flix-membership"
SCHEDULE_LINK = "https://kahlelflix.com/cp/38494/movie-schedule"
CAL_LINKS = {
 "Kahlel AI": "https://cal.com/leon-feris-fvlga3/kahlel-ai-robots-and-voice-ai",
 "GoGirl Afri-Ka Travel": "https://cal.com/leon-feris-fvlga3/afri-ka-tours-coloboration-call",
 "Kahlel Travel": "https://cal.com/leon-feris-fvlga3/afri-ka-tours-coloboration-call",
 "Kahlel Flix": "https://cal.com/leon-feris-fvlga3/outdoor-cinema",
 "Vivid Graphix": "https://cal.com/leon-feris-fvlga3/led-displays",
 "Vivid Display": "https://cal.com/leon-feris-fvlga3/led-displays",
 "Kahlel Group": "https://cal.com/leon-feris-fvlga3/kahlel-ai-robots-and-voice-ai"
}
IMAGE_AI = "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=600"
IMAGE_FLIX = "https://www.kahlelflix.com/photos/Drive.png?469"
IMAGE_TRAVEL = "https://a.kwikweb.co.za/afrikatourstr/otherImages/images1.jpg"
IMAGE_LED = "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=600"

WELCOME = """👉 *Welcome to Kahlel Group!* 👋

We're happy you're here.

1️⃣ 🤖 *Kahlel AI* - Robots & AI Agents
2️⃣ 🎬 *Kahlel Flix* - Movie Under The Stars
3️⃣ ✈️ *Afri-Ka Travel* - Namibia Holidays
4️⃣ 📺 *Vivid Graphix* - LED Screens
Reply 1-4 | Type *MENU* | Type *TALK TO HUMAN* for Leon"""

FLIX_CLEAN = f"""🎬 *SATURDAY DOUBLE - The Lion King + The Notebook* ✨

💰 *NORMAL:* N$99 for BOTH movies!

💎 *MEMBERSHIP - SAVE EVERY WEEKEND:*
🥈 *Silver* - N$49.50 only (50% OFF) + FREE Popcorn 🍿
👑 *VIP* - N$24.75 only (75% OFF) + FREE Popcorn + FREE Water + Best Beanbags

*This Saturday you save N$74.25 with VIP!*

1️⃣ *Become Member:* {MEMBERSHIP_LINK}
2️⃣ *Book Ticket (N$99 or N$24.75 if VIP):* {RESERVE_LINK}
3️⃣ *Schedule:* {SCHEDULE_LINK}

Popcorn & Beanbags limited - Reply BOOK to reserve!

{HIDE_TEXT}
"""
FLIX_SILVER = f"""🥈 *SILVER MEMBERSHIP - Most Popular*

Pay ONLY N$49.50 per movie (50% OFF normal N$99)
FREE Popcorn every time 🍿

👉 Join here: {MEMBERSHIP_LINK}
{HIDE_TEXT}
"""
FLIX_VIP = f"""👑 *VIP MEMBERSHIP - Best Value*

Pay ONLY N$24.75 per movie (75% OFF!)

👉 Join here: {MEMBERSHIP_LINK}
{HIDE_TEXT}
"""
TRAVEL_CLEAN = f"""*🌵 Namibia Safaris & Beyond - Kahlel Travel*
Sossusvlei Deadvlei | Swakopmund | Etosha | Twyfelfontein Himba | KAZA
🌐 www.afri-katours.com
📅 *Book Meeting:* https://cal.com/leon-feris-fvlga3/afri-ka-tours-coloboration-call
{HIDE_TEXT}"""
VIVID_CLEAN = f"""*📺 Vivid Graphix - LED Specialists*
Indoor P1.9 | Outdoor P3.9 IP65 | Stadium P8
🌐 www.kahlel.co.za
📅 *Book Meeting:* https://cal.com/leon-feris-fvlga3/led-displays
{HIDE_TEXT}"""
AI_CLEAN = f"""*🤖 Kahlel AI - Robots & Voice Agents*
🌐 www.kahlel-ai.com
🤖 Service Robots: Hotel, Restaurant
🗣️ *Voice AI:* Inbound/Outbound, 24/7, Multilingual
📅 *Book Meeting:* {CAL_LINKS['Kahlel AI']}
{HIDE_TEXT}"""
MENUS_TEXT = {"1": AI_CLEAN, "2": FLIX_CLEAN, "3": TRAVEL_CLEAN, "4": VIVID_CLEAN}
MENUS_IMAGE = {"1": IMAGE_AI, "2": IMAGE_FLIX, "3": IMAGE_TRAVEL, "4": IMAGE_LED}
BANNED = "CRITICAL: NEVER mention cleaning services. ONLY 4 services: 1) Kahlel AI 2) Kahlel Flix 3) Afri-Ka Travel 4) Vivid Graphix LED."
PROMPTS = {
 "Kahlel AI": f"{BANNED} You are Kahlel AI ONLY. Meeting {CAL_LINKS['Kahlel AI']}. Default {HIDE_TEXT}.",
 "Kahlel Flix": f"{BANNED} You are Kahlel Flix ONLY. Silver 50% N$49.50, VIP 75% N$24.75. Membership {MEMBERSHIP_LINK} Booking {RESERVE_LINK}. Default {HIDE_TEXT}.",
 "GoGirl Afri-Ka Travel": f"{BANNED} You are GoGirl Afri-Ka Travel ONLY. Cal {CAL_LINKS['GoGirl Afri-Ka Travel']}. Default {HIDE_TEXT}.",
 "Vivid Graphix": f"{BANNED} You are Vivid Graphix LED ONLY. Cal {CAL_LINKS['Vivid Graphix']}. Default {HIDE_TEXT}.",
 "Kahlel Group": f"{BANNED} You are Kahlel Group helper. ONLY show menu: 1 AI 2 Flix 3 Travel 4 LED. Default {HIDE_TEXT}."
}
def groq_reply(msg, last=None):
 low=msg.lower()
 if last and last != "Kahlel Group": service = last
 else: service="Kahlel Group"
 if any(k in low for k in ["flix", "movie", "silver", "vip", "cinema", "popcorn"]): service="Kahlel Flix"
 elif any(k in low for k in ["ai", "robot", "voice agent"]): service="Kahlel AI"
 elif any(k in low for k in ["travel","holiday","namibia","safari"]): service="GoGirl Afri-Ka Travel"
 elif any(k in low for k in ["vivid", "led", "display", "screen"]): service="Vivid Graphix"
 sys_prompt=PROMPTS.get(service, PROMPTS["Kahlel Group"])
 date=""; m=re.search(r'(\d{1,2}.*(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)|tomorrow|today)', low)
 if m: date=m.group(1)
 extracted={"service":service,"date":date}; smart=None
 try:
  from groq import Groq; client=Groq(api_key=GROQ_API_KEY)
  for MODEL in MODELS:
   try:
    c=client.chat.completions.create(model=MODEL, messages=[{"role":"system","content":sys_prompt},{"role":"user","content":msg}], max_tokens=350, temperature=0.2)
    smart=c.choices[0].message.content; smart=clean_whatsapp_text(smart); break
   except: continue
 except: pass
 return extracted, smart
def save_full(phone, service, name, date, location, people, message, lead_type="Prospect"):
 try: requests.post(SHEET_URL, json={"phone":phone,"service":service,"name":name,"date":date,"location":location,"people":people,"message":message,"lead_type":lead_type,"cal_link":CAL_LINKS.get(service,"")}, timeout=10)
 except: pass
def send_text(to, text):
 try:
  text=clean_whatsapp_text(text); to_clean="+"+str(to).strip().lstrip("+"); url="https://api.d7networks.com/whatsapp/v2/send"; headers={"Authorization": f"Bearer {D7_API_TOKEN}", "Content-Type":"application/json"}
  payload={"messages":[{"originator":D7_NUMBER,"content":{"message_type":"TEXT","text":{"body":text[:1000]}},"recipients":[{"recipient":to_clean,"recipient_type":"individual"}]}]}
  requests.post(url, headers=headers, json=payload, timeout=15)
 except: pass
def send_image(to, image_url, caption):
 to_clean="+"+str(to).strip().lstrip("+"); url="https://api.d7networks.com/whatsapp/v2/send"; headers={"Authorization": f"Bearer {D7_API_TOKEN}", "Content-Type":"application/json"}
 caption=clean_whatsapp_text(caption)
 payload={"messages":[{"originator":D7_NUMBER,"content":{"message_type":"ATTACHMENT","attachment":{"type":"image","url": image_url,"caption": caption[:900]}},"recipients":[{"recipient":to_clean,"recipient_type":"individual"}]}]}
 try:
  r=requests.post(url, headers=headers, json=payload, timeout=15)
  log(f"IMAGE SEND {r.status_code} {r.text[:200]}")
  if r.status_code != 200: send_text(to, caption)
 except Exception as e:
  log(f"IMAGE FAIL {e}"); send_text(to, caption)

FLIX_DETAILED_TRIGGERS = ["movie", "flix", "cinema", "silver", "vip", "membership", "popcorn", "discount", "price", "cost", "ticket", "show", "film"]

@app.route("/webhook", methods=["POST","GET"])
def webhook():
 if request.method=="GET": return f"V21.0 FIXED {RESERVE_LINK}",200
 raw=request.get_data(as_text=True); data=json.loads(raw) if raw else {}
 sender=""; msg=""
 if "event_content" in data:
  m=data["event_content"].get("message",{}); sender=m.get("originator",""); txt=m.get("text",{}); msg=txt.get("body","") if isinstance(txt,dict) else str(txt)
  if not msg and "attachments" in m:
   try: att=m["attachments"][0]; msg = att.get("title","") or att.get("description","") or ""
   except: pass
 if not sender or not msg:
  try:
   if "entry" in data: sender = data["entry"][0]["messaging"][0]["sender"]["id"]; msg = data["entry"][0]["messaging"][0]["message"].get("text","")
  except: pass
 if not sender or not msg: return jsonify({"status":"ignored"}),200
 sender="+"+str(sender).strip().lstrip("+"); low=msg.lower().strip(); raw_low = raw.lower()
 log(f"MSG {sender}: {msg} | RAW {raw_low[:600]}")
 # 0. HUMAN FIRST - WORKS ANYWHERE
 if should_reveal_contact(msg):
  save_full(sender, SESSION.get(sender) or "Wants Human", "", "", "", "", msg, "HOT - Wants Human")
  send_text(sender, REVEAL_TEXT + f"\n\nOr book: {CAL_LINKS.get(SESSION.get(sender), CAL_LINKS['Kahlel Group'])}")
  return jsonify({"status":"human_revealed"}),200
 is_fb_ad_click = ("can i get more info on this" in low or "fb.me" in raw_low or "skip long drives" in raw_low or "explore namibia by air" in raw_low or "afri-ka tours & travel" in raw_low or "afri-katours.com" in raw_low)
 if is_fb_ad_click:
  SESSION.pop(sender, None); save_full(sender, "Facebook Ad Click - AfriKa", "", "", "", "", msg, "Facebook Ad Lead"); send_text(sender, WELCOME); return jsonify({"status":"fb_menu_sent"}),200
 # 1. MAIN MENU 1-4 ALWAYS WINS
 m_num = re.match(r'^\D*([1-4])\D*', low)
 if m_num and len(low) < 10:
  num = m_num.group(1)
  mapping={"1":"Kahlel AI","2":"Kahlel Flix","3":"GoGirl Afri-Ka Travel","4":"Vivid Graphix"}
  sm=mapping[num]
  SESSION[sender]=sm
  save_full(sender, sm, "", "", "", "", f"Pressed {num}", "Cold - Browsing")
  send_image(sender, MENUS_IMAGE[num], MENUS_TEXT[num])
  return jsonify({"status":"menu_sent"}),200
 # 2. FLIX INTERNAL WORDS ONLY
 if SESSION.get(sender) == "Kahlel Flix" and "silver" in low:
  save_full(sender, "Kahlel Flix - Wants Silver", "", "", "", "", msg, "HOT - Wants Membership"); send_text(sender, FLIX_SILVER); return jsonify({"status":"silver_sent"}),200
 if SESSION.get(sender) == "Kahlel Flix" and "vip" in low:
  save_full(sender, "Kahlel Flix - Wants VIP", "", "", "", "", msg, "HOT - Wants Membership"); send_text(sender, FLIX_VIP); return jsonify({"status":"vip_sent"}),200
 # 3. FLIX TRIGGER
 if any(k in low for k in FLIX_DETAILED_TRIGGERS):
  SESSION[sender]="Kahlel Flix"; save_full(sender, "Kahlel Flix - Clean", "", "", "", "", msg, "HOT - Flix"); send_image(sender, IMAGE_FLIX, FLIX_CLEAN); return jsonify({"status":"flix_clean_sent"}),200
 if any(k in low for k in ["book meeting","appointment","book a meeting","book call","cal.com","consultation","meeting","schedule call","meet you","speak to leon"]):
  service = SESSION.get(sender, None)
  if not service or service == "Kahlel Group" or "Random" in str(service):
   all_links = f"""📅 *Book a Meeting with Leon:*
1️⃣ 🤖 *Kahlel AI Robots:* {CAL_LINKS['Kahlel AI']}
2️⃣ 🎬 *Kahlel Flix Cinema:* {CAL_LINKS['Kahlel Flix']}
3️⃣ ✈️ *Afri-Ka Travel:* {CAL_LINKS['GoGirl Afri-Ka Travel']}
4️⃣ 📺 *Vivid LED:* {CAL_LINKS['Vivid Graphix']}
👉 Reply 1-4 to select service first!
{HIDE_TEXT}"""
   save_full(sender, "Wants Meeting - All Links", "", "", "", "", msg, lead_type="HOT - Wants Meeting"); send_text(sender, all_links)
  else:
   cal_link = CAL_LINKS.get(service, CAL_LINKS["Kahlel Group"]); save_full(sender, service+" - WANTS MEETING", "", "", "", "", msg, lead_type="HOT - Wants Meeting"); send_text(sender, f"📅 Let's meet! Book here:\n👉 {cal_link}\nFor {service}\n{HIDE_TEXT}")
  return jsonify({"status":"sent"}),200
 if any(k in low for k in ["reserve ticket","book ticket","booking link"]):
  SESSION[sender]="Kahlel Flix"; save_full(sender, "Kahlel Flix - Reserve", "", "", "", "", msg, "HOT - Reserve"); send_image(sender, IMAGE_FLIX, FLIX_CLEAN); return jsonify({"status":"sent"}),200
 MONTHS=["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]; has_month=any(x in low for x in MONTHS)
 is_booking=len(msg.split())>=2 and (has_month or any(k in low for k in ["book","tomorrow","today","name","from","people","am","pm","airport","demo"]) or SESSION.get(sender))
 if is_booking:
  extracted, smart=groq_reply(msg, SESSION.get(sender)); SESSION[sender]=extracted["service"]; save_full(sender, extracted["service"], "", extracted["date"] or msg, "", "", msg, "Prospect")
  send_text(sender, smart or f"Got it! {extracted['service']} {HIDE_TEXT}")
 elif low in ["hello","hi","menu","start","welcome","more info","tell me more","information","info","more information","details","tell me","how much"]:
  SESSION.pop(sender, None); send_text(sender, WELCOME)
 else:
  if SESSION.get(sender):
   _, smart=groq_reply(msg, SESSION.get(sender))
   if smart and "cleaning" in smart.lower(): send_text(sender, WELCOME)
   else:
    send_text(sender, smart or WELCOME)
  else:
   SESSION.pop(sender, None); save_full(sender, "Random -> Menu", "", "", "", "", msg, "Cold - Random"); send_text(sender, WELCOME)
 return jsonify({"status":"sent"}),200

@app.route("/")
def home(): return f"V21.0 FIXED READY {CONTACT_PHONE}"
@app.route("/health")
def health(): return jsonify({"model":MODELS[0],"contact":CONTACT_PHONE,"cal":CAL_LINKS, "version":"V21.0"})
if __name__=="__main__": app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
