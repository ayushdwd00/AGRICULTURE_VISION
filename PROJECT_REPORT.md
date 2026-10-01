# AgriVision — Project Report Notes

**Project:** AgriVision — Smart Agriculture Super-App
**Type:** Full-stack agriculture application (React + TypeScript, FastAPI, Python)
**Scope:** 1 core AI module (Crop Doctor) + 6 supporting modules + dashboard/navigation
**Environment used for all measurements:** Windows, Python 3.13.0, `torch 2.14.0+cpu`,
`torchvision 0.29.0+cpu`, `streamlit 1.50.0`, `scikit-learn 1.8.0`, **CPU only** (no NVIDIA GPU).

---

## 1. Objective

Give a farmer one place to:

1. detect crop disease from a leaf photo, and see *why* the model decided that
   (Grad-CAM),
2. describe symptoms in words (typed or dictated) and have a second model
   classify them,
3. combine both signals with an explicit confidence rule and get a
   farmer-friendly explanation,
4. monitor weather-driven disease risk, calculate
   fertilizer needs, verify a product, find matching government schemes and rent
   equipment.

---

## 2. Architecture

```text
React + TypeScript frontend (frontend/)
        | HTTP / JSON + validated image uploads
        +---- FastAPI adapter (backend/main.py)
                    |
                    +---- modules/  (existing feature logic)
                    |       crop_doctor.py     symptom_model.py   weather.py
                    |       fertilizer.py      product_verifier.py
                    |       subsidy_matcher.py equipment_rental.py
                    +---- utils/ (Gemini, Grad-CAM, databases, helpers)
                    +---- data/ + models/ (existing datasets, SQLite, checkpoints)

Streamlit app (app.py) remains as a migration fallback; it is not needed to
run the React + FastAPI web application.
```

Nothing in `modules/` imports Streamlit, so the same functions are reused by the
`training/` scripts and the UI. Every external dependency (Gemini, Open-Meteo)
sits behind a **graceful fallback**, so a missing key never breaks the app.

---

## 3. Module 1 — Crop Doctor (core AI module)

### 3.1 Pretrained model (no training from scratch)

* Repository: `Daksh159/plant-disease-mobilenetv2` (Hugging Face, Apache-2.0),
  downloaded by `training/download_model.py` via `huggingface_hub`.
* The repository ships only `mobilenetv2_plant.pth`; the 38 class names in
  `models/class_names.json` are written from the canonical alphabetically sorted
  PlantVillage list (the order `ImageFolder` used during the original training).
* Architecture rebuilt exactly (verified by inspecting the checkpoint):
  `models.mobilenet_v2` with `classifier[1] = Sequential(Dropout(0.2), Linear(1280, 38))`
  → state-dict keys `classifier.1.1.weight` / `classifier.1.1.bias` (shape `38 × 1280`).
* **Original training data (by the model author):** the “New Plant Diseases
  Dataset (Augmented)” — PlantVillage, ~87,000 images, 38 balanced classes,
  reported ≈95 % validation accuracy.

### 3.2 Baseline verification **before** fine-tuning
`training/baseline_inference.py` loads the checkpoint and the six sample leaf
photos in `data/sample_images/` (copied from the Kaggle dataset, labels known) and
prints class, confidence, top-3 candidates and a Grad-CAM overlay.

Result: **6/6 sample labels correct** (100 %), e.g.

| image | predicted | confidence |
|---|---|---|
| `sample_pepper_bacterial_spot.jpg` | `Pepper,_bell___Bacterial_spot` | 99.9 % |
| `sample_potato_late_blight.jpg` | `Potato___Late_blight` | 100.0 % |
| `sample_tomato_early_blight.jpg` | `Tomato___Early_blight` | 83.4 % |
| `sample_tomato_healthy.jpg` | `Tomato___healthy` | 100.0 % |
| `sample_tomato_mosaic_virus.jpg` | `Tomato___Tomato_mosaic_virus` | 97.4 % |
| `sample_tomato_yellow_leaf_curl.jpg` | `Tomato___Tomato_Yellow_Leaf_Curl_Virus` | 100.0 % |

Evidence: `data/evaluation/baseline_inference.json`, overlays in
`data/evaluation/gradcam_samples/`.

### 3.3 Additional agriculture dataset
`training/download_dataset.py` downloads `emmarex/plantdisease` with `kagglehub`
(anonymous download works; the local kagglehub cache is reused) and copies a
**balanced, deterministic subset**: 30 train + 10 val images per class, 15 classes
→ **450 train / 150 val** images (~0.01 GB) in `data/dataset/`.

Folder names of that dataset differ slightly from the canonical labels
(`Tomato_Early_blight` vs `Tomato___Early_blight`), so
`utils.helpers.canonical_from_dataset_folder` normalises them. The 15 local
folders are then mapped into the **global 38-class index space** by
`modules.crop_doctor.build_image_folder_dataset`, so the fine-tuned model keeps
the pretrained model's output structure.

### 3.4 Fine-tuning (`training/fine_tune.py`)
Transfer learning only — the backbone stays frozen, exactly as the brief requires:

| setting | value |
|---|---|
| start checkpoint | `models/mobilenetv2_plant.pth` |
| frozen | entire MobileNetV2 backbone (`model.features`) |
| trained | 38-way classifier head only → **48,678 of 2,272,550 params (2.1 %)** |
| optimiser | Adam, lr = 1e-3, weight decay 1e-4, `StepLR` (γ = 0.5) |
| epochs / batch | 5 / 32 (≈28 s per epoch on CPU) |
| augmentation | RandomResizedCrop + flip + rotation + mild colour jitter |
| validation | 150 images, best epoch kept (`val_accuracy`) |
| output | `models/agrivision_cnn.pth` (state dict + metadata: epoch, val accuracy, config) |
| configurable | `--epochs`, `--batch-size`, `--lr`, `--dataset`, `--unfreeze-blocks`, `--seed`, … |

An optional second phase (`--unfreeze-blocks N`) unfreezes the last N inverted
residual blocks at a 0.3× learning rate for anyone with a GPU.

### 3.5 Before / after evaluation (`training/evaluate.py`)
Same validation split, same transform, both checkpoints loaded into the same
architecture:

| metric | before (pretrained) | after (fine-tuned) | change |
|---|---|---|---|
| accuracy | 93.33 % | **96.00 %** | **+2.67 pp** |
| cross-entropy loss | 0.2290 | **0.2181** | **−0.0110** |
| mean confidence | 92.13 % | 93.19 % | +1.06 pp |

Per-class highlights (fine-tuned): Bell Pepper both classes 1.00 F1, Potato all
three classes 1.00 F1, Tomato Early blight 0.947, Tomato Late blight 1.00. The
only noteworthy confusion is Tomato Bacterial spot ↔ Tomato Early blight /
Septoria leaf spot, which is a well-known look-alike group.

Artifacts written by the script:

* `data/evaluation/evaluation_summary.json` — all metrics + deltas
* `data/evaluation/evaluation_before_after.txt` — the printed comparison table
* `data/evaluation/classification_report_before.txt` / `_after.txt`
* `data/evaluation/confusion_matrix_before.png` / `_after.png` — seaborn heat maps
  drawn with `figsize=(20, 20)`
* `data/evaluation/metrics_comparison.png` — accuracy / loss bar comparison
* `data/evaluation/fine_tune_history.json` — per-epoch train/val loss, accuracy,
  learning rate, seconds, trainable parameter count
* `data/evaluation/dataset_manifest.json` — which images were copied for training

The confusion matrix is drawn with `figsize=(20, 20)`; because the additional
Kaggle dataset contains 15 of the 38 PlantVillage classes, the matrix shows the
classes present in the split by default. `python training/evaluate.py --full-matrix`
forces the complete 38 × 38 layout (rows/columns without samples are empty).

### 3.6 Grad-CAM (`utils/gradcam.py`)
Implemented from scratch with PyTorch only (no extra package):

```text
Image -> model forward (activations captured from model.features[-1] by a forward hook)
      -> target class (predicted class by default)
      -> gradients of that class score w.r.t. the activation map (torch.autograd.grad)
      -> channel weights = mean of gradients over spatial dims
      -> heat map = ReLU(sum(weights * activations)), normalised to [0, 1]
      -> resized to the input size, JET colour map, alpha-blended over the original
```

`gradcam_overlay()` returns `overlay_image`, `heatmap_image` and `original_image`
as PIL images, so the Crop Doctor page can simply `st.image()` them side by side
(Original image | Grad-CAM overlay | raw heat map). Verified on all six sample
leaf photos (overlays in `data/evaluation/gradcam_samples/`).

### 3.7 Image inference API
```python
from modules.crop_doctor import predict_image
predict_image(image_bytes)   # -> {"label": "Tomato___Early_blight", "confidence": 0.93,
                             #     "pretty_label": "Tomato - Early blight", "crop": "Tomato",
                             #     "condition": "Early blight", "is_healthy": False,
                             #     "category": "fungal", "severity": "Moderate",
                             #     "top_predictions": [...], "model_used": "agrivision_cnn.pth",
                             #     "error": None}
```
It loads `models/agrivision_cnn.pth` when present (otherwise the pretrained
checkpoint), `models/class_names.json`, uses the same 224×224 ImageNet
normalisation as the original training, caches the model with `lru_cache`, and
never raises: missing model / invalid image / inference failure are returned in
the `"error"` key.

### 3.8 Symptom classifier (`modules/symptom_model.py`)
* Dataset: `data/symptoms.csv`, built by `training/build_symptom_dataset.py` —
  **210 rows / 10 classes** (18 rows per class) covering Nitrogen, Phosphorus and
  Potassium deficiency, Fungal leaf spot/blight, Bacterial infection, Viral
  infection, Pest attack, Water stress, Heat/sunlight stress and Healthy crop.
* Features: TF-IDF (word 1–2 grams) of the farmer's text **plus the five binary
  symptom features** required by the brief — leaf colour change, spot pattern,
  wilting, leaf curling, stunted growth. The binaries are derived from the text by
  documented keyword rules (`extract_symptom_flags`), and the same function is
  used to build the CSV, so training and inference can never drift apart
  (0 mismatches reported by the training script).
* Model: scikit-learn `RandomForestClassifier` (300 trees, balanced class weights)
  inside a `ColumnTransformer` pipeline, saved to
  `models/agrivision_symptom_model.pkl` together with its metadata.
* Measured: **held-out accuracy 92.9 %** (42 test rows) and
  **5-fold cross-validation 89.1 % ± 8.3 %**.
* `predict_symptoms(text)` → `{"label", "confidence", "family", "severity",
  "advice", "flags", "cues", "error", ...}`.
* Confidence is deliberately conservative: clear, detailed descriptions cross the
  70 % threshold, while short/vague text stays below it and correctly triggers the
  “uncertain → ask for detail / consult an expert” path.

### 3.10 Crop Doctor confidence logic & UI
* Fusion rule (exactly as specified):
  `combined_confidence = min(image_confidence, symptom_confidence)`; threshold
  **0.70**.
  * `>= 0.70` → an AI explanation is generated (Gemini, or the labelled offline
    fallback when no key/network is available).
  * `< 0.70` → **“Prediction uncertain. Please provide a clearer image / symptom
    description, or consult an agricultural expert.”** and no AI diagnosis is
    produced.
* If the two models disagree (compatibility table in
  `IMAGE_TO_SYMPTOM_COMPATIBILITY`), the disagreement note is shown in the UI and
  passed to Gemini, whose prompt instructs it to present **both** possibilities
  instead of a single confident answer. The classifier output is never silently
  overridden.
* Error handling: missing checkpoint, missing symptom model, invalid/blank image,
  Gemini failure, Grad-CAM failure and generic inference errors all produce
  friendly messages — verified by driving the page with empty input and with an
  invalid file.
* UI blocks (top to bottom): model status chips → upload + preview → symptom box
  (+ voice) → progress bar & spinners → **Diagnosis Result** (disease,
  confidence, symptom analysis, symptom confidence, severity, combined
  confidence) → uncertainty / disagreement banners → **AI Explanation** →
  **Visual Explanation** (Original image | Grad-CAM overlay | raw heat map) →
  top-3 candidates → the exact Gemini prompt → session diagnosis history.

---

## 4. Module 3 — Weather & Pest Early Warning (API + rules + Gemini)

`modules/weather.py`, no geolocation — the user types a city:

```text
City -> Open-Meteo Geocoding API -> coordinates -> Current Weather API
     -> rule engine (deterministic) -> risk flags -> Gemini wording (or fallback)
```

Rules (each surfaced with the literal condition that fired):

| risk | condition | level |
|---|---|---|
| Fungal disease | humidity > 80 % **and** 20 °C ≤ T ≤ 30 °C | HIGH |
| Fungal watch | humidity ≥ 70 % **and** 18 °C ≤ T ≤ 32 °C | MODERATE |
| Heat stress | T > 35 °C | HIGH |
| Bacterial spread | rain > 0 **and** T ≥ 22 °C | MODERATE |
| Spraying caution | wind ≥ 8 m/s | MODERATE |
| Cold stress | T < 10 °C | MODERATE |

Verified: T 28 / H 84 → HIGH fungal; T 38 → HIGH heat; T 15 / H 60 → LOW;
T 25 / H 75 / rain 3 mm / wind 9 m/s → three MODERATE flags; T 6 → cold stress.
Unknown city or missing key: a 404-style message (“City 'x' was not found…”) plus
a **manual values** mode where the same rule engine runs on typed
temperature/humidity/rainfall.

### 3.9 Voice input
The symptom box has a 🎙️ **Voice input** panel implemented with the browser
**Web Speech API** (`webkitSpeechRecognition`) inside a Streamlit HTML component:
start/stop button, live transcript and a copy button. Because a raw HTML component
cannot return a value to Streamlit, the transcript is copied and pasted into the
symptom box; if the browser or the embedded frame blocks the microphone the panel
says so and typing/pasting is always available. No separate speech model is
trained (as required by the brief).

### 3.11 Gemini explanation (`utils/gemini.py`)
`generate_description(image_result, symptom_result, symptom_text, combined)`
sends exactly the information the brief requires: image label + confidence,
symptom label + confidence, the extracted symptom features, the farmer's raw
words, the combined confidence and the agree/disagree flag. It asks for a
**3–4 sentence farmer-friendly diagnosis** and, when the models disagree, to
mention both possibilities instead of pretending certainty.

`SAFETY_RULES` in the same file forbid the model from replacing the classifier's
answer, inventing schemes/doses/verification results, or promising chemical
dosages. The prompt is stored with the diagnosis and can be inspected on the page
(“Prompt sent to Gemini”).

Model selection: `GEMINI_MODEL` in `.env` (default `gemini-2.0-flash`). The wrapper
supports both the current `google-genai` SDK and the legacy
`google-generativeai` package, and returns a labelled **offline fallback** text
built from the classifier outputs if either the key is missing or the call fails.

---

## 5. Module 4 — Fertilizer Calculator (**deterministic, not ML**)

`data/fertilizer_data.json` is the whole "model": 9 crops (Tomato, Potato, Wheat,
Rice, Maize, Onion, Cotton, Mustard, Sugarcane) × N/P/K entries plus shared
micronutrient products (zinc sulphate, sulphur, borax, lime/gypsum, FYM), each with
fertilizer name, dosage per acre, unit, indicative price and an application note.
The module performs only:

```text
quantity       = dosage_per_acre x land_size_acres      (hectares -> acres x 2.47105)
estimated_cost = quantity x cost_per_unit
```

Verified: Tomato + Nitrogen + 2.5 acres → **112.5 kg Urea, ≈ ₹675**;
Wheat + Potassium + 1 hectare → 39.54 kg MOP for 2.47 acres ≈ ₹1,344;
Onion + Zinc + 0.5 acre → 5 kg zinc sulphate ≈ ₹300; unknown crop and negative
land size both return friendly errors instead of crashing.

**Gemini is never used in this module** and the page states this explicitly, with
an audit-trail expander showing the exact lookup row and computation.

---

## 6. Module 5 — Product Verifier (SQLite)

* `utils/database.py` creates `data/products.db` and seeds **10 demo products**
  (fungicides, fertilizers, bio-inputs) with code, name, manufacturer, batch,
  expiry, status (Verified / Recalled / Suspended) and registration date.
* `modules/product_verifier.py` normalises the code, looks it up, parses the expiry
  date and reports **🟢 Product Verified**, an expiry warning, a recall warning, or
  **⚠️ Product not found in registry**.
* QR codes on the pack are decoded with OpenCV's built-in `QRCodeDetector`; a full
  URL payload is reduced to the product code (`…?code=AGV-1002 → AGV-1002`).
  Barcode (EAN/UPC) decoding is not part of the installed stack, so manual entry is
  the documented fallback.
* Verified: `AGV-1001` → verified; `AGV-1005` → RECALLED; `AGV-1006` → expired
  (302 days ago); `AGV-9999` → not found; empty input → prompt.

**The registry is simulated** and the page says so: a real product would need a
trusted manufacturer / authorised-registry database.

---

## 7. Module 6 — Government Scheme Matcher (static rules)

`data/schemes.json` holds **8 real, publicly available schemes** with name,
description, benefit, eligibility, land-size window, region, crop coverage,
documents and the official link:

| scheme | category | land size (acres) | official link |
|---|---|---|---|
| PM-KISAN | income-support | 0.01 – 5 | pmkisan.gov.in |
| PMFBY | insurance | 0.01 – 2000 | pmfby.gov.in |
| Kisan Credit Card | credit | 0.01 – 2000 | myscheme.gov.in/schemes/kcc |
| Soil Health Card | soil-health | 0.01 – 2000 | soilhealth.dac.gov.in |
| PMKSY – Per Drop More Crop | irrigation | 0.25 – 12.5 | pmksy.gov.in |
| PKVY (organic, PGS-India) | organic | 0.1 – 30 | pgsindia-ncof.gov.in |
| MIDH (horticulture) | horticulture | 0.1 – 200 | midh.gov.in |
| Agriculture Infrastructure Fund | infrastructure | 0.1 – 2000 | agriinfra.dac.gov.in |

All links were reachability-checked before being written into the file (e-NAM was
excluded because its TLS certificate failed from this machine).

The 4-step wizard maps 1:1 onto the rules: **land size → region → crop → support
type (category)**, with Back / Next / Start-over buttons and a progress bar.
Matching is pure JSON logic (`modules/subsidy_matcher.py`) and the result cards
show *why* each scheme matched, plus a “did not match” list with reasons.
Verified with several profiles, e.g. 2.5 acres / Uttar Pradesh / Tomato / Any → 8
matches; 0.2 acre / irrigation → 7 matches + 1 near-miss (“Requires between 0.25
and 12.5 acres”). Gemini is not involved, so no scheme or link can be invented.

---

## 8. Module 7 — Equipment Rental (SQLite MVP)

* **Roles:** `farmer` (browse + book) and `owner` (CRUD on their own machines).
* **Authentication:** username + **PBKDF2-SHA256 salted hash** (120 000 iterations,
  stdlib `hashlib`/`hmac`, constant-time compare) stored in `data/rentals.db`;
  session state keeps the logged-in user; two demo accounts are seeded
  (`farmer_demo/farmer123`, `owner_demo/owner123`).
* **Machine CRUD:** create (name, type, hourly rate, daily rate, location,
  description), read (with location/type/owner filters), update and delete —
  update/delete are refused for anyone who is not the owner.
* **Bookings:** inclusive date range, `days = (end − start) + 1`,
  `cost = days × daily_rate`; **overlap prevention** with the SQL condition
  `existing.start <= requested.end AND requested.start <= existing.end`
  restricted to non-cancelled bookings; past start dates are rejected.
* Verified end-to-end: booking a machine for 3 days → ₹6,600; an identical request
  and an edge-overlapping request are both rejected with the clashing dates named;
  after cancelling, the same dates can be booked again; deleting the machine
  removes its bookings.
* Out of scope by design: payments and reviews.

---

## 9. Dashboard, navigation and session state

* Sidebar navigation over the eight remaining pages, with a styled brand block and
  a live **System status** expander (active checkpoint, class count, device, Gemini
  status/model/SDK, fine-tuned weights, fertilizer table, scheme list).
* Dashboard: crop health / disease risk / weather cards with the current session's
  results, quick-action buttons, the latest diagnosis, the session context used by
  the assistant, the module list, and a **model performance** card with the
  pretrained vs fine-tuned accuracy/loss and the comparison chart.
* `st.session_state` keeps: current user, diagnosis history (last 20), uploaded
  image bytes/name, last diagnosis bundle, symptom text, weather result and city,
  selected machine and the assistant transcript.

---

## 10. ML / AI vs deterministic — summary for the evaluator

**ML / AI**

| Module | Technique | Evidence |
|---|---|---|
| 1 Crop Doctor | pretrained MobileNetV2 (PlantVillage, 38 classes) **fine-tuned** on the extra Kaggle dataset | 93.33 % → 96.00 % accuracy on 150 val images; `evaluation_summary.json`, confusion matrices |
| 1 Symptom classifier | scikit-learn Random Forest on TF-IDF + 5 symptom features | 92.9 % held-out, 89.1 % ± 8.3 % 5-fold CV |
| 1 Grad-CAM | PyTorch forward hook + `torch.autograd.grad` | overlays in `data/evaluation/gradcam_samples/` |
| 1 & 8 Gemini | LLM used **only** to phrase explanations / answer questions, with guard rails | prompts stored and shown in the UI |
| 3 Weather | API data + documented risk rules + Gemini wording | rule table verified with 5 weather profiles |

**Deterministic / database (explicitly not ML)**

| Module | Mechanism |
|---|---|
| 4 Fertilizer | static per-acre lookup + arithmetic |
| 5 Product Verifier | SQLite registry lookup (+ OpenCV QR decode) |
| 6 Government Schemes | static JSON rule matching, 4-step wizard |
| 7 Equipment Rental | SQLite CRUD, PBKDF2 auth, overlap-checked bookings |

> **AgriVision's vision model is not trained from scratch.** It starts from a
> pretrained MobileNetV2 plant-disease model (already fine-tuned by its author on
> the 38-class augmented PlantVillage dataset) and is further fine-tuned on an
> additional agriculture dataset (`emmarex/plantdisease`), with the backbone frozen
> and only the classifier head trained.

---

## 11. Testing and verification performed

Testing was kept deliberately minimal, as the brief requests — every step was
verified by *running* it:

1. **Pretrained model** — `python training/baseline_inference.py --gradcam`
   → 6/6 known sample labels correct, Grad-CAM overlays written.
2. **Dataset** — `python training/download_dataset.py` → 450 train / 150 val
   images across 15 classes, manifest written.
3. **Fine-tuning** — `python training/fine_tune.py --epochs 5 --batch-size 32 --lr 0.001`
   → best val accuracy 96.00 % (epoch 2), checkpoint + history saved.
4. **Evaluation** — `python training/evaluate.py` → before/after accuracy, loss,
   classification reports, two confusion matrices (`figsize=(20,20)`), comparison
   chart, all in `data/evaluation/`.
5. **Symptom model** — build dataset + train script → 92.9 % held-out / 89.1 % CV.
6. **Module-level driver tests** — each module was executed from a script
   (predictions, parsing, rule engine, lookups, matching, bookings) before wiring it
   to the UI.
7. **UI (headless)** — `python tools/verify_pages.py` runs every page through
   `streamlit.testing.v1.AppTest`: **8/8 pages PASS, 0 failures**; the Crop Doctor,
   Weather, Product, Scheme, Rental and Assistant pages were also driven through
   real widget clicks/inputs to confirm that results appear.
8. **Regression fixes found by that testing** — Streamlit forbids writing to a
   *widget* key after the widget exists, so the QR-decode and “Clear inputs”
   actions use versioned widget keys with separate session values;
   `use_container_width` was migrated to the current `width="stretch"` API.
9. **UI polish (this revision)** — a single injected stylesheet (`APP_CSS`) drives
   the look: hero page headers, styled section titles, accent-bordered status
   cards, colour-coded confidence bars, a framed AI answer block, softer buttons,
   rounded metric tiles and a tidier sidebar. Decorative comment banners were
   removed from every Python file, so comments stay short and useful.
---

## 12. Fallback behaviour (what happens when a service is unavailable)

| Missing / failing | Implemented fallback |
|---|---|
| `GEMINI_API_KEY` or Gemini error | Deterministic offline text, clearly labelled “no AI”, assembled from the classifier outputs |
| Open-Meteo unavailable | Manual temperature/humidity/rainfall form runs the same rule engine |
| Unknown city | 404-style message with a suggestion to try a nearby larger city |
| Fine-tuned checkpoint absent | Falls back to the pretrained checkpoint and shows which is active |
| Invalid image / empty input | Farmer-friendly message; the app never shows a traceback |
| Barcode scanning | Manual code entry (QR codes are decoded with OpenCV) |
| Voice input blocked | Typing/pasting in the symptom box |

---

## 13. Limitations (stated honestly)

* The product registry is a simulated demo database, not a real product
  verification service.
* Weather rules are threshold-based screening aids, not a forecast or an
  epidemiological model.
* The symptom dataset is small and hand-authored; its confidence is conservative,
  so brief descriptions often fall below the 0.70 threshold and trigger the
  “uncertain” path (which is the intended safety behaviour).
* Only 15 of the 38 PlantVillage classes have training/evaluation images in the
  additional Kaggle dataset; the model still outputs all 38 classes.
* Severity (“Mild/Moderate/Severe”) is a presentation heuristic.
* Fine-tuning was performed on CPU with a small balanced subset, so the
  improvement is modest (+2.67 pp) — the point is to demonstrate the
  transfer-learning workflow, not to beat the state of the art.
* No payments, reviews or real user accounts beyond the demo marketplace.

---

## 14. Future work

* Retrain on the complete 38-class PlantVillage set and measure on its official
  test split; add more on-field (non-lab) images for domain shift.
* Fine-tune the symptom classifier on real farmer transcripts; optionally add
  Whisper/offline speech-to-text so the transcript lands in the app directly.
* Replace demo registries with real APIs (product registry, mandi prices,
  state-specific schemes) and add authentication with roles beyond the demo.
* Persist diagnosis history per user (SQLite/Postgres) instead of session state.
* Add a small automated test suite and CI if the project grows.

---

## 15. Conclusion

AgriVision demonstrates the complete pipeline the brief asked for: a **pretrained
MobileNetV2 plant-disease model is fine-tuned** (not trained from scratch) on an
additional dataset, evaluated before/after with confusion matrices and reports,
explained with **Grad-CAM**, fused with a **Random Forest symptom classifier**
under an explicit `min(confidence) ≥ 0.70` rule, and narrated by **Gemini** with
guard rails. Around that core AI module sit five supporting modules —
weather-risk rules, a deterministic fertilizer calculator,
a SQLite product registry, a static government-scheme matcher and an
overlap-safe equipment rental marketplace — all inside a single **Streamlit** app
that degrades gracefully whenever a model, key, binary or network is unavailable.
