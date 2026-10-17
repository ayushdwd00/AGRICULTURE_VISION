from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health_reports_per_feature_availability():
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert {"crop_diagnosis", "symptom_analysis", "weather"} <= set(body["features"])


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


def test_lazy_model_loading_behavior():
    import io
    from PIL import Image
    from modules.crop_doctor import clear_crop_doctor_cache, is_model_loaded
    from modules.symptom_model import clear_symptom_model_cache, is_symptom_model_loaded

    clear_crop_doctor_cache()
    clear_symptom_model_cache()

    # 1. Health check must not trigger model loading
    health = client.get("/api/health").json()
    assert health["status"] == "ok"
    assert health["features"]["crop_diagnosis"]["loaded"] is False
    assert health["features"]["symptom_analysis"]["loaded"] is False
    assert not is_model_loaded()
    assert not is_symptom_model_loaded()

    # 2. Symptom prediction loads only symptom model
    sym_res = client.post("/api/symptoms/predict", json={"text": "yellow leaves with brown spots"})
    assert sym_res.status_code == 200
    assert is_symptom_model_loaded()
    assert not is_model_loaded()

    # 3. Crop diagnosis loads vision model
    img = Image.new("RGB", (224, 224), color=(34, 139, 34))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    files = {"image": ("leaf.jpg", buf.getvalue(), "image/jpeg")}
    diag_res = client.post("/api/crop/diagnose", files=files)
    assert diag_res.status_code == 200
    assert is_model_loaded()

    # 4. Grad-CAM reuses vision model
    buf.seek(0)
    files_cam = {"image": ("leaf.jpg", buf.getvalue(), "image/jpeg")}
    cam_res = client.post("/api/crop/gradcam", files=files_cam)
    assert cam_res.status_code == 200
    assert "images" in cam_res.json()

