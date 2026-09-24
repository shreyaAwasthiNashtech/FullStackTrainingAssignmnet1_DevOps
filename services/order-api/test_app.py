import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

app_path = Path(__file__).resolve().parent / "app.py"
spec = importlib.util.spec_from_file_location("order_api_app", app_path)
order_api_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(order_api_module)
app = order_api_module.app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["service"] == "order-api"


def test_orders_no_payload(client):
    response = client.post("/orders", json={})
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_orders_missing_field(client):
    response = client.post(
        "/orders", json={"order_id": "ORD-1", "item": "Widget"}
    )
    assert response.status_code == 400


@patch("requests.post")
def test_orders_success(mock_post, client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "PROCESSED"}
    mock_post.return_value = mock_response

    payload = {"order_id": "ORD-1", "item": "Widget", "amount": 100}
    response = client.post("/orders", json=payload)
    assert response.status_code == 202
    data = response.get_json()
    assert data["status"] == "PROCESSED"
    assert data["order_id"] == "ORD-1"
