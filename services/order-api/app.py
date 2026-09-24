import os
from flask import Flask, jsonify, request
import requests

app = Flask(__name__)
ORDER_PROCESSOR_URL = os.environ.get(
    "ORDER_PROCESSOR_URL", "http://order-processor:5001/process"
)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "order-api"}), 200


@app.route("/orders", methods=["POST"])
def create_order():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid or missing JSON payload"}), 400

    order_id = data.get("order_id")
    item = data.get("item")
    amount = data.get("amount")

    if not order_id or not item or amount is None:
        return jsonify(
            {"error": "Missing required fields: order_id, item, amount"}
        ), 400

    try:
        resp = requests.post(ORDER_PROCESSOR_URL, json=data, timeout=5)
        if resp.status_code != 200:
            return jsonify({
                "error": "Order processing failed downstream",
                "details": resp.text
            }), 502
    except requests.RequestException as e:
        return jsonify({
            "error": "Failed to connect to order-processor",
            "details": str(e)
        }), 503

    return jsonify({
        "status": "PROCESSED",
        "order_id": order_id,
        "message": "Order accepted and processed successfully"
    }), 202


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
