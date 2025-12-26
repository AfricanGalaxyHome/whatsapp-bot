# app.py
import os
from openai import OpenAI
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -----------------------------
# 1. Initialize Firebase safely
# -----------------------------
cred = credentials.Certificate("firebase-key.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

# -----------------------------
# 2. Connect to Firestore
# -----------------------------
db = firestore.client()

# -----------------------------
# 3. Flask app
# -----------------------------
app = Flask(__name__)

# -----------------------------
# Auto-reply sender (stub)
# -----------------------------
def send_whatsapp_reply(phone, text):
    print(f"Would send to {phone}: {text}")
    # Later: replace with real WhatsApp API call


# -----------------------------
# Conversation memory helpers
# -----------------------------
def get_conversation(phone):
    doc_ref = db.collection("conversations").document(phone)
    doc = doc_ref.get()

    if doc.exists:
        return doc.to_dict()
    return None


def save_conversation(phone, last_message, last_response, state="active"):
    db.collection("conversations").document(phone).set({
        "phone": phone,
        "last_message": last_message,
        "last_response": last_response,
        "state": state,
        "updated_at": firestore.SERVER_TIMESTAMP
    }, merge=True)

# -----------------------------
# Fast& Safe Saved responses
#------------------------------

def detect_intent(text):
    text = text.lower()

    if any(word in text for word in ["hi", "hello", "hey"]):
        return "greeting"

    if any(word in text for word in ["price", "cost", "how much"]):
        return "pricing"

    if any(word in text for word in ["laptop", "pc", "computer"]):
        return "products"

    if any(word in text for word in ["location", "where", "address"]):
        return "location"

    if any(word in text for word in ["agent", "human", "call"]):
        return "human"

    return "unknown"

# -----------------------------
# Webhook route
# -----------------------------
@app.route("/webhook", methods=["GET", "POST"])
def webhook():

    # 🔐 Meta verification
    if request.method == "GET":
        verify_token = "CALVIN_SECRET_TOKEN"
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == verify_token:
            return challenge, 200
        return "verification failed", 403

    # 📩 Incoming WhatsApp messages
    if request.method == "POST":
        data = request.get_json()
        print("Webhook Received:", data)

        try:
            entry = data.get("entry", [])[0]
            changes = entry.get("changes", [])[0]
            value = changes.get("value", {})
            messages = value.get("messages", [])

            if messages:
                msg = messages[0]
                phone = msg.get("from")
                text = msg.get("text", {}).get("body")

                if phone and text:
                    # Save raw message
                    db.collection("messages").add({
                        "phone": phone,
                        "message": text,
                        "platform": "whatsapp",
                        "timestamp": firestore.SERVER_TIMESTAMP
                    })

                    # Conversation logic
                    conversation = get_conversation(phone)

                    if not conversation:
                        reply = "Hi 👋 Welcome to African Galaxy Home! How can I help you today?"
                        state = "new"
                    else:
                        intent = detect_intent(text)
                        state = "active"

                        if intent == "greeting":
                            reply = "Hi 👋 Welcome to African Galaxy Home! How can I help you today?"

                        elif intent == "products":
                            reply = "💻 We sell laptops, gaming accessories, and computer equipment. What are you looking for?"

                        elif intent == "pricing":
                            reply = "💰 Prices depend on the product. Please tell me which item you're interested in."

                        elif intent == "location":
                            reply = "📍 We operate online in South Africa. Delivery options are available."

                        elif intent == "human":
                            reply = "☎️ No problem! I’ll connect you to a human agent shortly."

                        else:
                            reply = "🤖 I didn’t fully understand that. Could you please explain a bit more?"

                    # Send reply
                    send_whatsapp_reply(phone, reply)

                    # Save conversation memory
                    save_conversation(
                        phone=phone,
                        last_message=text,
                        last_response=reply,
                        state=state
                    )

        except Exception as e:
            print("Error processing message:", e)

        return "ok", 200


# -----------------------------
# Run app
# -----------------------------
if __name__ == "__main__":
    app.run(port=5000, debug=True)
