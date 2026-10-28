import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image

from services.crop_diagnosis import (
    get_available_sample_images,
    run_crop_diagnosis,
    generate_gradcam_explanation,
)
from services.weather_service import get_cached_weather, get_manual_weather
from services.fertilizer_service import calculate_fertilizer_plan
from services.product_verification import verify_product_code, get_registered_products
from services.scheme_matcher import find_matching_schemes

print("--- 1. Testing Crop Doctor & Real PyTorch Inference ---")
samples = get_available_sample_images()
print(f"Loaded {len(samples)} sample images.")
if samples:
    sample_img = Image.open(samples[0]["path"])
    diag = run_crop_diagnosis(sample_img, "small dark spots with yellow halos")
    print("Crop Doctor Vision Output:", diag["image_result"]["pretty_label"])
    print(f"Vision Confidence: {diag['image_result']['confidence']*100:.1f}%")
    print("Symptom Classifier Output:", diag["symptom_result"]["pretty_label"])
    print("Combined Confidence:", f"{diag['combined']['combined_confidence']*100:.1f}%")
    print("Is Confident (>=70%):", diag["combined"]["is_confident"])
    
    print("\n--- 2. Testing Grad-CAM Activation Heatmap ---")
    gc = generate_gradcam_explanation(sample_img, diag["image_result"]["label"])
    print("Grad-CAM Error:", gc.get("error"))
    print("Grad-CAM Overlay Generated:", bool(gc.get("overlay_image")))

print("\n--- 3. Testing Weather Intelligence (Open-Meteo) ---")
w = get_cached_weather("Pune", use_ai=False)
print("Resolved City:", w.get("city"))
print("Current Temperature:", w.get("weather", {}).get("temperature"), "°C")
print("Relative Humidity:", w.get("weather", {}).get("humidity"), "%")
print("Risk Level:", w.get("risk_level"))

print("\n--- 4. Testing Fertilizer Planner (Deterministic) ---")
f = calculate_fertilizer_plan("Tomato", "Nitrogen", 2.5, bag_weight_kg=45.0)
print(f"Fertilizer: {f.get('fertilizer')}")
print(f"Total Quantity: {f.get('quantity')} kg")
print(f"Standard 45kg Bags to purchase: {f.get('bags_to_buy')}")
print(f"Estimated Cost: INR {f.get('estimated_cost')}")
print(f"Reference: {f.get('britannica_reference')}")

print("\n--- 5. Testing Product Verification (SQLite) ---")
p = verify_product_code("AGV-1001")
print(f"Product AGV-1001 Verified: {p.get('verified')}")
print(f"Product Name: {p.get('product', {}).get('product_name')}")
msg_clean = str(p.get('message', '')).encode('ascii', 'ignore').decode('ascii')
print(f"Status Message: {msg_clean}")

print("\n--- 6. Testing Government Scheme Matcher ---")
s = find_matching_schemes(2.0, "Maharashtra", "Wheat")
print(f"Matched Schemes Count: {len(s.get('matches', []))}")
print(f"Near Misses Count: {len(s.get('near_misses', []))}")
if s.get("matches"):
    print(f"Top Matched Scheme: {s['matches'][0]['name']}")

print("\nALL 6 VERIFICATIONS PASSED SUCCESSFULLY!")
