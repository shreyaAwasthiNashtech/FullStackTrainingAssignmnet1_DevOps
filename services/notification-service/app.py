import logging
import os
from flask import Flask, jsonify, request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "notification-service"
    }), 200


@app.route("/notify", methods=["POST"])
def notify():
    data = request.get_json(silent=True)
    if not data or not data.get("recipient"):
        logger.warning("Missing recipient in /notify request")
        return jsonify({"error": "Missing required field: recipient"}), 400

    recipient = data.get("recipient")
    logger.info("Notification dispatched successfully to %s", recipient)
    return jsonify({
        "status": "DISPATCHED",
        "recipient": recipient,
        "message": "Notification dispatched successfully"
    }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5002))
    app.run(host="0.0.0.0", port=port)
