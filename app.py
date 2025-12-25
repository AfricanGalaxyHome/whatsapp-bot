from flask import Flask, request
import firebase_admin
from firebase_admin import credentials, firestore

# -------------------------
# Flask app
# -------------------------
app = Flask(__name__)

# -------------------------
# Firebase initialization
# -------------------------
cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# -------------------------
# Webhook route
# -------------------------
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
            entry = data["entry"][0]
            changes = entry["changes"][0]
            value = changes["value"]
            messages = value.get("messages")

            if messages:
                msg = messages[0]
                phone = msg["from"]
                text = msg["text"]["body"]

                # Save to Firestore
                db.collection("messages").add({
                    "phone": phone,
                    "message": text,
                    "platform": "whatsapp",
                    "timestamp": firestore.SERVER_TIMESTAMP
                })

                print(f"Saved message from {phone}: {text}")

        except Exception as e:
            print("Error processing message:", e)

        return "ok", 200


# -------------------------
# Run app
# -------------------------
if __name__ == "__main__":
    app.run(port=5000, debug=True)
