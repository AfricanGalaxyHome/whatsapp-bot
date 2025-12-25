from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        verify_token = "CALVIN_SECRET_TOKEN"
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == verify_token:
            return challenge, 200
        return "verification failed", 403

    if request.method == "POST":
        data = request.get_json()
        print("Webhook Received:", data)
        return "ok", 200

if __name__ == "__main__":
    app.run(port=5000, debug=True)
