"""Final check: calls the public entry point of every module once."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

LINES = []

def log(label: str, value: object) -> None:
    text = f"{label:<26} {value}"
    LINES.append(text)
    print(text.encode("ascii", "replace").decode("ascii"))

# Crop Doctor: vision + symptom models
from modules.crop_doctor import combine_signals, gradcam_for_image, model_status, predict_image
from modules.symptom_model import predict_symptoms, symptom_model_status
from utils.gemini import generate_description
from utils.helpers import format_percent, load_image_from_bytes

image_bytes = Path("data/sample_images/sample_tomato_early_blight.jpg").read_bytes()
image_result = predict_image(image_bytes)
log("M1 predict_image", f"{image_result['label']} {format_percent(image_result['confidence'])} "
                       f"via {image_result['model_used']} error={image_result['error']}")
text = "brown spots with dark rings on the leaves and the plants are wilting"
symptom_result = predict_symptoms(text)
log("M1 predict_symptoms", f"{symptom_result['label']} "
                           f"{format_percent(symptom_result['confidence'])} "
                           f"family={symptom_result['family']}")
combined = combine_signals(image_result, symptom_result)
log("M1 combine_signals", f"min={format_percent(combined['combined_confidence'])} "
                          f"confident={combined['is_confident']} agree={combined['agreement']}")
explanation = generate_description(image_result, symptom_result, text, combined)
log("M1 explanation", f"source={explanation['source']} chars={len(explanation['text'])}")
gradcam = gradcam_for_image(load_image_from_bytes(image_bytes), target_label=image_result["label"])
log("M1 gradcam", f"error={gradcam.get('error')} overlay={gradcam['overlay_image'].size}")
log("M1 model_status", f"{model_status()['active']} classes={model_status()['num_classes']}")
log("M1 symptom_status", f"available={symptom_model_status()['available']}")

# Weather: rule engine + AI wording
from modules.weather import weather_report

manual = weather_report("Varanasi", manual_values={"temperature": 28.4, "humidity": 84, "rainfall": 0.4})
log("M2 weather_report", f"level={manual['risk_level']} risks={[r['key'] for r in manual['risks']]} "
                         f"ai={manual['message']['source']}")

# Fertilizer: deterministic lookup
from modules.fertilizer import calculate

fertilizer = calculate("Tomato", "Nitrogen", 2.5)
log("M3 calculate", f"{fertilizer['quantity']} {fertilizer['unit']} cost={fertilizer['estimated_cost']}")

# Product verifier: SQLite registry
from modules.product_verifier import verify_product, verifier_status

verified = verify_product("AGV-1001")
log("M4 verify_product", f"found={verified['found']} verified={verified['verified']} "
                         f"registry={verifier_status()['count']}")

# Scheme matcher: static rules
from modules.subsidy_matcher import match_schemes

schemes = match_schemes(2.5, "Uttar Pradesh", "Tomato", "Any")
log("M5 match_schemes", f"matches={len(schemes['matches'])} near={len(schemes['near_misses'])}")

# Equipment rental: auth, listings, overlap-safe booking
from datetime import date, timedelta

from modules.equipment_rental import (
    cancel_booking,
    create_booking,
    list_machines,
    login_user,
)

user = login_user("farmer_demo", "farmer123")
machines = list_machines()
start = (date.today() + timedelta(days=3)).isoformat()
end = (date.today() + timedelta(days=5)).isoformat()
booking = create_booking(int(machines[-1]["id"]), int(user["user"]["id"]), start, end, "verify run")
clash = create_booking(int(machines[-1]["id"]), int(user["user"]["id"]), start, end, "verify run")
if booking["ok"]:
    cancel_booking(int(booking["booking_id"]), int(user["user"]["id"]))
log("M6 rental", f"machines={len(machines)} login={user['ok']} booking_ok={booking['ok']} "
                 f"clash_prevented={not clash['ok']}")

Path("data/evaluation/final_integration_check.txt").write_text("\n".join(LINES) + "\n", encoding="utf-8")
print("\n[ok] written data/evaluation/final_integration_check.txt")
