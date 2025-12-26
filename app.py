# app.py
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request

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
# 3. Test connection
# -----------------------------
try:
    collections = db.collections()
    print("Connected to Firebase! Collections in Firestore:")
    for col in collections:
        print("-", col.id)
except Exception as e:
    print("Error connecting to Firestore:", e)

# -----------------------------
# 4. Flask app
# -----------------------------
app = Flask(__name__)

# -----------------------------
# 5. Auto-reply function
# -----------------------------
def send_whatsapp_reply(phone, text):
    reply_text = f"Hi! You said: {text}"
    print(f"Would send to {phone}: {reply_text}")
    # Later: real WhatsApp API call goes here
    
    def get_conversation(phone):
    """
    Get conversation memory for a user
    """
    doc_ref = db.collection("conversations").document(phone)
    doc = doc_ref.get()

    if doc.exists:
        return doc.to_dict()
    return None


def save_conversation(phone, last_message, last_response, state="active"):
    """
    Save or update conversation memory
    """
    db.collection("conversations").document(phone).set({
        "phone": phone,
        "last_message": last_message,
        "last_response": last_response,
        "state": state,
        "updated_at": firestore.SERVER_TIMESTAMP
    }, merge=True)


# -----------------------------
# 6. Webhook route
# -----------------------------
@app.route("/webhook", methods=["GET", "POST"])
def webhook():

    # 🔐 Meta verification (GET)
    if request.method == "GET":
        verify_token = "CALVIN_SECRET_TOKEN"
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == verify_token:
            return challenge, 200
        return "verification failed", 403

    # 📩 Incoming WhatsApp messages (POST)
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

                        # 🔍 Check conversation memory
                        conversation = get_conversation(phone)

                        if not conversation:
                            # New user
                            reply = "Hi 👋 Welcome to African Galaxy Home! How can I help you today?"
                            state = "new"
                        else:
                            # Existing user
                            reply = f"I hear you 👍 You said: {text}"
                            state = "active"

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
# 7. Run app
# -----------------------------
if __name__ == "__main__":
    app.run(port=5000, debug=True)
