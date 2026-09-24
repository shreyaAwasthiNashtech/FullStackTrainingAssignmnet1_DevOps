import logging
import os
from flask import Flask, jsonify, request
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

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
        logger.warning("Invalid or missing JSON payload in /orders")
        return jsonify({"error": "Invalid or missing JSON payload"}), 400

    order_id = data.get("order_id")
    item = data.get("item")
    amount = data.get("amount")

    if not order_id or not item or amount is None:
        logger.warning("Validation failed for order request: %s", data)
        return jsonify(
            {"error": "Missing required fields: order_id, item, amount"}
        ), 400

    logger.info("Forwarding order %s to %s", order_id, ORDER_PROCESSOR_URL)
    try:
        resp = requests.post(ORDER_PROCESSOR_URL, json=data, timeout=5)
        if resp.status_code != 200:
            logger.error(
                "Downstream error from order-processor for %s: %s",
                order_id,
                resp.text,
            )
            return jsonify({
                "error": "Order processing failed downstream",
                "details": resp.text
            }), 502
    except requests.RequestException as e:
        logger.error(
            "Connection failure to order-processor for %s: %s",
            order_id,
            str(e),
        )
        return jsonify({
            "error": "Failed to connect to order-processor",
            "details": str(e)
        }), 503

    logger.info("Order %s accepted and processed", order_id)
    return jsonify({
        "status": "PROCESSED",
        "order_id": order_id,
        "message": "Order accepted and processed successfully"
    }), 202


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
