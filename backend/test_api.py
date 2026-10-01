from datetime import date, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.main import app
from utils.database import RENTAL_DB_PATH, execute

client = TestClient(app)


def test_health_reports_per_feature_availability():
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert {"crop_diagnosis", "symptom_analysis", "weather", "equipment"} <= set(
        body["features"]
    )


def test_static_feature_options_are_exposed():
    fertilizer = client.get("/api/fertilizer/options")
    schemes = client.get("/api/schemes/options")
    assert fertilizer.status_code == schemes.status_code == 200
    assert "crops" in fertilizer.json()
    assert "deficiencies" in fertilizer.json()
    assert "regions" in schemes.json()
    assert "categories" in schemes.json()


def test_weather_manual_values_use_existing_risk_rules():
    response = client.get(
        "/api/weather",
        params={
            "city": "Test Farm",
            "temperature": 35,
            "humidity": 82,
            "rainfall": 1,
            "use_ai": False,
        },
    )
    incomplete = client.get(
        "/api/weather", params={"city": "Test Farm", "temperature": 35}
    )
    assert response.status_code == 200
    assert response.json()["weather"]["temperature"] == 35
    assert response.json()["weather"]["humidity"] == 82
    assert response.json()["risk_level"] == "MODERATE"
    assert "bacterial" in {risk["key"] for risk in response.json()["risks"]}
    assert incomplete.status_code == 422


def test_structured_validation_and_image_validation():
    invalid_symptoms = client.post("/api/symptoms/predict", json={"text": "x"})
    invalid_image = client.post(
        "/api/crop/diagnose",
        files={"image": ("leaf.png", b"not an image", "image/png")},
    )
    assert invalid_symptoms.status_code == 422
    assert invalid_image.status_code == 400
    assert "traceback" not in invalid_image.text.lower()


def test_rental_routes_require_authentication():
    response = client.get("/api/rental/auth/me")
    assert response.status_code == 401


def test_rental_auth_machine_crud_and_booking_overlap():
    suffix = uuid4().hex[:10]
    owner_id = farmer_id = machine_id = None
    try:
        owner = client.post(
            "/api/rental/auth/register",
            json={"username": f"apiowner{suffix}", "password": "testpass123", "role": "owner"},
        )
        farmer = client.post(
            "/api/rental/auth/register",
            json={"username": f"apifarmer{suffix}", "password": "testpass123", "role": "farmer"},
        )
        assert owner.status_code == farmer.status_code == 201
        owner_id = owner.json()["user"]["id"]
        farmer_id = farmer.json()["user"]["id"]
        owner_headers = {"Authorization": f"Bearer {owner.json()['access_token']}"}
        farmer_headers = {"Authorization": f"Bearer {farmer.json()['access_token']}"}
        machine = client.post(
            "/api/rental/machines",
            headers=owner_headers,
            json={
                "name": f"API test tractor {suffix}",
                "machine_type": "Tractor",
                "hourly_rate": 500,
                "daily_rate": 3000,
                "location": "Test location",
            },
        )
        assert machine.status_code == 201
        machine_id = machine.json()["machine"]["id"]
        start = (date.today() + timedelta(days=40)).isoformat()
        end = (date.today() + timedelta(days=41)).isoformat()
        booking_payload = {"start_date": start, "end_date": end}
        created = client.post(
            f"/api/rental/machines/{machine_id}/bookings",
            headers=farmer_headers,
            json=booking_payload,
        )
        clash = client.post(
                f"/api/rental/machines/{machine_id}/bookings",
                headers=farmer_headers,
                json=booking_payload,
            )
        assert created.status_code == 201
        assert clash.status_code == 409
        assert "already booked" in clash.json()["detail"]
    finally:
        if machine_id:
            execute(RENTAL_DB_PATH, "DELETE FROM machines WHERE id = ?", (machine_id,))
        if owner_id:
            execute(RENTAL_DB_PATH, "DELETE FROM users WHERE id = ?", (owner_id,))
        if farmer_id:
            execute(RENTAL_DB_PATH, "DELETE FROM users WHERE id = ?", (farmer_id,))
