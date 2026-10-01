# 🌾 AgriVision — Smart Agriculture Super-App

AgriVision combines **computer vision, a symptom classifier, weather APIs and
SQLite databases** into a farmer-focused web application. The React + TypeScript
frontend communicates with a FastAPI backend, which reuses the existing
agricultural modules and model files. Google Gemini may explain model outputs;
it does not invent predictions, schemes or calculations.

> **Key statement about the AI:** the vision model is **not trained from
> scratch**. It starts from a pretrained MobileNetV2 plant-disease model
> (`Daksh159/plant-disease-mobilenetv2`, trained on the 38-class augmented
> PlantVillage dataset) and is **fine-tuned** on an additional agriculture
> dataset (`emmarex/plantdisease`).

---

## ✨ Modules

| # | Module | Type | What it does |
|---|--------|------|--------------|
| 1 | 🩺 **Crop Doctor** | **AI (ML + LLM)** | MobileNetV2 leaf-disease CNN (fine-tuned), Random Forest symptom classifier, Grad-CAM explanation, Gemini diagnosis. Core module. |
| 3 | 🌦️ **Weather & Crop Risk** | API + rules + LLM | Open-Meteo geocoding + current weather, deterministic disease/heat risk rules, Gemini words the warning. |
| 4 | 🧮 **Fertilizer Calculator** | **Deterministic** | Per-acre lookup table for crop × deficiency → fertilizer, quantity, cost. *Not ML, never an LLM guess.* |
| 5 | 🔐 **Product Verifier** | **Database** | SQLite product registry lookup (+ OpenCV QR decoding). Simulated demo registry. |
| 6 | 🏛️ **Government Schemes** | **Static rules** | 4-step wizard matching land size / region / crop / support type against 8 real schemes with official links. |
| 7 | 🚜 **Equipment Rental** | **Database** | SQLite marketplace: two roles, machine CRUD, bookings with overlap prevention. |
| — | 🤖 **AI Assistant** | LLM | Gemini chat that can use your AgriVision results as context. |
| — | 🏠 **Dashboard** | UI | Crop health, disease risk, weather, quick actions, model-performance card. |

---

## 🗂️ Project structure

```text
agri-vision/
├── app.py                        # Preserved Streamlit application for migration fallback
├── requirements.txt
├── .env.example                  # GEMINI_API_KEY template
├── .gitignore
├── README.md                     # this file
├── PROJECT_REPORT.md             # college report notes (module by module)
├── backend/
│   ├── main.py                   # FastAPI routes; reuses modules/ and utils/
│   ├── security.py               # Rental API bearer-token signing
│   ├── requirements.txt          # API runtime dependencies (no Streamlit)
│   └── test_api.py               # API and booking-conflict tests
├── frontend/
│   ├── src/                      # React, TypeScript, Tailwind and 3D field scene
│   ├── package.json
│   └── vite.config.ts
│
├── models/                       # model artefacts (git-ignored)
│   ├── mobilenetv2_plant.pth     # pretrained, downloaded from Hugging Face
│   ├── agrivision_cnn.pth        # fine-tuned by training/fine_tune.py
│   ├── agrivision_symptom_model.pkl
│   └── class_names.json          # the 38 PlantVillage class names
│
├── data/
│   ├── symptoms.csv              # labelled symptom dataset (built by training/)
│   ├── fertilizer_data.json      # deterministic fertilizer table (Module 4)
│   ├── schemes.json              # 8 real government schemes (Module 6)
│   ├── products.db               # SQLite registry (Module 5, seeded with demo rows)
│   ├── rentals.db                # SQLite rental marketplace (Module 7)
│   ├── sample_images/            # sample leaf photos for baseline inference
│   ├── dataset/{train,val}/      # fine-tuning subset (git-ignored)
│   └── evaluation/               # metrics, plots, reports, manifests
│
├── modules/                      # feature logic (Streamlit-free)
│   ├── crop_doctor.py            # vision model, predict_image(), confidence fusion
│   ├── symptom_model.py          # Random Forest symptom classifier
│   ├── weather.py                # Open-Meteo + risk rule engine
│   ├── fertilizer.py             # deterministic calculator
│   ├── product_verifier.py       # registry lookup + QR decode
│   ├── subsidy_matcher.py        # static scheme matching
│   └── equipment_rental.py       # auth, machine CRUD, bookings
│
├── utils/
│   ├── gemini.py                 # Gemini wrapper + offline fallbacks
│   ├── gradcam.py                # Grad-CAM (PyTorch hooks, no extra package)
│   ├── database.py               # SQLite helpers, password hashing, schemas
│   └── helpers.py                # paths, image IO, class-name utilities
│
├── training/
│   ├── download_model.py         # Hugging Face checkpoint + class_names.json
│   ├── baseline_inference.py     # verify the pretrained model (before fine-tuning)
│   ├── download_dataset.py       # kagglehub download + balanced subset
│   ├── fine_tune.py              # transfer learning -> agrivision_cnn.pth
│   ├── evaluate.py               # before/after metrics, confusion matrices
│   ├── build_symptom_dataset.py  # creates data/symptoms.csv
│   └── train_symptom_model.py    # trains the Random Forest symptom model
│
└── tools/
    ├── verify_pages.py           # headless smoke check for every page
    └── verify_modules.py         # one-call integration check of all 8 modules
```

---

## ⚙️ Setup

The API runtime does not require Streamlit. A GPU is *not* required for
inference. The old Streamlit application and root `requirements.txt` are
preserved for migration fallback; the final web application uses
`backend/requirements.txt` and `frontend/`.

```powershell
# 1) Install backend runtime dependencies (does not install Streamlit)
pip install -r backend/requirements.txt

# 2) Configure backend-only secrets; never commit the real .env
Copy-Item .env.example .env
# Edit .env with GEMINI_API_KEY as needed.
# Set AGRIVISION_AUTH_SECRET to a private random value for stable rental tokens.

# 3) Start the API in one terminal
python -m uvicorn backend.main:app --reload

# 4) Start the React app in another terminal
Set-Location frontend
npm install
npm run dev

# Production frontend bundle
npm run build
```

The frontend expects the API at `http://localhost:8000` by default. To change
that, set `VITE_API_URL` in a local `frontend/.env` file. API keys belong only
in the root backend `.env`; they must never be added to frontend variables.

The preserved Streamlit app can still be run separately during migration:

```powershell
pip install -r requirements.txt
streamlit run app.py
```

The backend health endpoint is `GET /api/health`; interactive API documentation
is available at `/docs` while the development server is running.

The API also exposes crop diagnosis, symptoms and Grad-CAM; weather; fertilizer
options and calculations; product and QR verification; scheme listing and
matching; and authenticated equipment listings and bookings. Weather can analyze
farmer-entered values with
`GET /api/weather?city=Farm&temperature=30&humidity=70`. Such values are
identified as manual observations and pass through the existing risk rules.

Run the API integration tests with:

```powershell
python -m pytest backend/test_api.py -q
```

### Model & data pipeline (run once, in this order)

```powershell
python training/download_model.py          # pretrained MobileNetV2 -> models/
python training/baseline_inference.py --gradcam   # confirm the pretrained model works
python training/download_dataset.py        # kagglehub subset -> data/dataset/{train,val}
python training/fine_tune.py --epochs 5 --batch-size 32 --lr 0.001
python training/evaluate.py                # before/after metrics + plots
python training/build_symptom_dataset.py   # data/symptoms.csv
python training/train_symptom_model.py     # Random Forest -> models/*.pkl
```

Everything after `download_model.py` is optional for *running* the app: without
the fine-tuned checkpoint the Crop Doctor automatically falls back to the
pretrained one, and missing optional services never break the UI.

---

## 📊 Measured results (this machine, CPU only)

**Vision model — before vs after fine-tuning** (150 validation images, 15 classes
mapped into the original 38-class output space):

| metric | pretrained (`mobilenetv2_plant.pth`) | fine-tuned (`agrivision_cnn.pth`) | change |
|---|---|---|---|
| accuracy | 93.33 % | **96.00 %** | **+2.67 %** |
| cross-entropy loss | 0.2290 | **0.2181** | **−0.0110** |
| mean confidence | 92.13 % | 93.19 % | +1.06 % |

Fine-tuning used only **48,678 of 2,272,550 parameters** (frozen MobileNetV2
backbone, 38-way head trained for 5 epochs, ~28 s/epoch on CPU).

**Symptom classifier** (120 → 210 labelled rows, 10 classes): held-out accuracy
**92.9 %**, 5-fold cross-validation **89.1 % ± 8.3 %**.

All artefacts (confusion matrices `figsize=(20,20)`, classification reports,
`metrics_comparison.png`, `evaluation_summary.json`, `baseline_inference.json`,
`fine_tune_history.json`) are written to `data/evaluation/`.

---

## ✅ Verification

```powershell
python tools/verify_pages.py --out data/evaluation/ui_smoke_report.txt   # every page, headless
python tools/verify_modules.py                                           # every module's API
```

`verify_pages.py` runs `app.py` headlessly once per page
(`streamlit.testing.v1.AppTest`) and reports whether every page rendered without
an exception — current report: **8/8 pages PASS, 0 failures**.
`verify_modules.py` calls the public entry point of every module and prints one
line per module (prediction, risk rules, cost, registry, matches, booking) —
current output is stored in `data/evaluation/final_integration_check.txt`.

Manual checklist used while building each module is described in
`PROJECT_REPORT.md`.

---

## 🎨 Web interface

The React frontend provides responsive navigation for the overview, Crop Doctor,
weather intelligence, fertilizer planning, product verification, scheme matcher,
equipment rental and About pages. The overview includes a lazily loaded,
interactive React Three Fiber crop field. Feature pages render data returned by
the backend and do not ship example predictions or secret API keys.

---

## 🧠 Machine learning vs deterministic logic (important for evaluation)

**ML / AI modules**

* **Crop Doctor** — pretrained MobileNetV2 (Hugging Face) fine-tuned on the extra
  Kaggle PlantVillage subset; Random Forest symptom classifier (scikit-learn);
  Grad-CAM (PyTorch hooks); Gemini for the natural-language explanation.
* **Weather & Crop Risk** — API data + deterministic risk rules + Gemini wording.

**Deterministic / database modules**

* **Fertilizer Calculator** — static per-acre lookup, plain arithmetic.
* **Product Verifier** — SQLite registry lookup.
* **Government Schemes** — static rule matching against `data/schemes.json`.
* **Equipment Rental** — SQLite CRUD + overlap-checked bookings with PBKDF2
  password hashing.

Gemini is never allowed to invent a diagnosis, a scheme name, an application
link, a fertilizer dose or a product verification result — the prompts contain
explicit guard rails (`utils/gemini.py`, `SAFETY_RULES`).

---

## 🛟 Graceful fallbacks (design decisions you can demo)

| Situation | Behaviour |
|---|---|
| `GEMINI_API_KEY` missing or the API fails | The UI labels an **offline fallback** text built deterministically from the model outputs; nothing crashes. |
| Open-Meteo unavailable | The Weather page can use **manual values** mode: the same rule engine + warning run on typed temperature/humidity. |
| Unknown / misspelled city | 404-style message: “City 'x' was not found…”. |
| Fine-tuned checkpoint missing | Crop Doctor automatically uses the pretrained checkpoint and the UI shows which one is active. |
| Invalid image upload | Farmer-friendly message; no traceback. |
| Barcode (EAN/UPC) scan | Not part of the installed stack → manual code entry is the documented fallback (QR codes *are* decoded with OpenCV). |
| Browser voice input | Implemented with the Web Speech API inside a Streamlit HTML component; because a raw HTML component cannot push a value back into Streamlit, the transcript is **copied** and pasted into the symptom box (typing always works). |

---

## ⚠️ Honest limitations

* The product registry is a **simulated demo database**, not a real
  manufacturer/authorised registry.
* Weather risk rules are simple, documented thresholds — agronomic screening
  aids, not a forecast model.
* The symptom dataset is small and hand-authored (210 rows); its confidence is
  deliberately conservative, so short or vague descriptions often land below the
  70 % threshold and correctly trigger the “consult an expert / add detail” path.
* Evaluation uses a 15-class subset of the 38 PlantVillage classes because the
  additional Kaggle dataset covers 15 classes; the confusion matrix is drawn with
  `figsize=(20,20)` for the classes present (`--full-matrix` forces all 38).
* Severity (“Mild/Moderate/Severe”) is a presentation heuristic derived from the
  predicted class family and confidence — not a field measurement.
* This is an educational project: always confirm a diagnosis with a local
  agricultural expert before spraying.

---

## 🔗 Data, models and links

* Pretrained model: [`Daksh159/plant-disease-mobilenetv2`](https://huggingface.co/Daksh159/plant-disease-mobilenetv2)
  (Apache-2.0) — 38-class PlantVillage MobileNetV2.
* Fine-tuning data: [`emmarex/plantdisease`](https://www.kaggle.com/datasets/emmarex/plantdisease)
  (PlantVillage subset) downloaded with `kagglehub`.
* Government schemes: PM-KISAN, PMFBY, KCC, Soil Health Card, PMKSY (Per Drop
  More Crop), PKVY (PGS-India), MIDH, Agriculture Infrastructure Fund — links to
  their official portals are stored in `data/schemes.json` and were reachability
  checked when the file was written.
* Weather: Open-Meteo geocoding + current weather APIs.
* AI text: Google Gemini (`gemini-2.0-flash` by default, configurable).
