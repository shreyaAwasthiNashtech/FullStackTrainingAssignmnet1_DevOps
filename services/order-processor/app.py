import os
from flask import Flask, jsonify, request
import requests

app = Flask(__name__)
NOTIFICATION_SERVICE_URL = os.environ.get(
    "NOTIFICATION_SERVICE_URL", "http://notification-service:5002/notify"
)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "order-processor"}), 200


@app.route("/process", methods=["POST"])
def process_order():
    data = request.get_json(silent=True)
    if not data or not data.get("order_id"):
        return jsonify({"error": "Missing required field: order_id"}), 400

    order_id = data.get("order_id")
    notification_payload = {
        "recipient": f"user-{order_id}@example.com",
        "order_id": order_id,
        "message": f"Order {order_id} has been processed."
    }

    try:
        resp = requests.post(
            NOTIFICATION_SERVICE_URL, json=notification_payload, timeout=5
        )
        if resp.status_code != 200:
            return jsonify({
                "error": "Notification dispatch failed",
                "details": resp.text
            }), 502
    except requests.RequestException as e:
        return jsonify({
            "error": "Failed to connect to notification-service",
            "details": str(e)
        }), 503

    return jsonify({
        "status": "PROCESSED",
        "order_id": order_id,
        "message": "Order processed successfully"
    }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
