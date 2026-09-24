import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

app_path = Path(__file__).resolve().parent / "app.py"
spec = importlib.util.spec_from_file_location("order_processor_app", app_path)
order_processor_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(order_processor_module)
app = order_processor_module.app


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
    assert data["service"] == "order-processor"


def test_process_no_order_id(client):
    response = client.post("/process", json={})
    assert response.status_code == 400
    assert "error" in response.get_json()


@patch("requests.post")
def test_process_success(mock_post, client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "DISPATCHED"}
    mock_post.return_value = mock_response

    response = client.post("/process", json={"order_id": "ORD-100"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "PROCESSED"
    assert data["order_id"] == "ORD-100"
