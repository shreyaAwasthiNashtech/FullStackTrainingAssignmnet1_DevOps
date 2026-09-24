import importlib.util
from pathlib import Path
import pytest

app_path = Path(__file__).resolve().parent / "app.py"
spec = importlib.util.spec_from_file_location(
    "notification_service_app", app_path
)
notification_service_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notification_service_module)
app = notification_service_module.app


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
    assert data["service"] == "notification-service"


def test_notify_no_recipient(client):
    response = client.post("/notify", json={})
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_notify_success(client):
    response = client.post("/notify", json={"recipient": "user@example.com"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "DISPATCHED"
    assert data["recipient"] == "user@example.com"
