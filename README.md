# 🌾 AgriVision — Intelligent Agriculture Super-App

AgriVision is an integrated, Python-first **Streamlit** application designed for modern agricultural decision support. It replaces the previous decoupled React frontend + FastAPI backend architecture with a single, maintainable, deployment-ready Python codebase while fully preserving all underlying AI models, algorithms, SQLite registries, and deterministic business rules.

---

## ✨ Features & Agricultural Modules

| Module | Core Technology | Agronomic Functionality |
|---|---|---|
| 🩺 **Crop Doctor** | PyTorch MobileNetV2 + Random Forest + Grad-CAM | Dual-signal plant leaf disease diagnosis across 38 PlantVillage classes, symptom NLP classification, Grad-CAM visual heatmaps, and advisory recommendations guarded by a strict 70% confidence threshold. |
| 🌦️ **Weather Intelligence** | Open-Meteo REST API + Rule Engine | Real-time microclimate conditions with 15-minute response caching per location. Deterministic rules evaluating fungal spore germination risk, heat stress warnings, and spray drift alerts. Includes a manual simulation mode. |
| 🧮 **Fertilizer Planner** | Deterministic Lookup Tables | Per-acre nutrient dosage calculations (Urea, DAP, MOP, etc.), bag requirements (standard 45 kg / 50 kg bags), indicative INR costs, and [Britannica 4R fertilizer stewardship](https://www.britannica.com/topic/fertilizer) guidance. |
| 🔐 **Product Verification** | SQLite Database + OpenCV QR Decoding | Anti-counterfeiting verification for seeds, fertilizers, and crop protection inputs. Verifies serial codes and scanned QR codes against the local SQLite registry (`data/products.db`). |
| 🏛️ **Government Scheme Matcher** | Deterministic Rule Engine | 4-step farm profiling wizard matching landholding size, state/region, crop, and support category against 8 statutory central agricultural welfare schemes with real application links. |

---

## 🗂️ Application Structure

```text
AGRICULTURE_VISION/
├── app.py                              # Main application entry point & Home Overview
├── requirements.txt                    # Unified Python dependencies
├── runtime.txt                         # Python version (python-3.11)
├── README.md                           # Documentation & deployment guide
├── .env.example                        # Safe environment variable template
├── .gitignore                          # Excludes models, caches, and secrets
├── .streamlit/
│   └── config.toml                     # AgriVision botanical theme and server settings
├── pages/
│   ├── 1_Crop_Doctor.py                # Dual-signal diagnosis & Grad-CAM heatmaps
│   ├── 2_Weather_Intelligence.py       # Open-Meteo microclimate & fungal risk
│   ├── 3_Fertilizer_Planner.py         # Deterministic nutrient & bag calculator
│   ├── 4_Product_Verification.py       # SQLite authenticity & QR scanning
│   └── 5_Government_Schemes.py         # 4-step subsidy & support scheme matcher
├── components/
│   ├── botanical_elements.py           # Editorial CSS, header cards, botanical badges
│   ├── cards.py                        # KPI cards, confidence bars, scheme cards
│   ├── navigation.py                   # Sidebar system readiness indicators
│   └── visualizations.py               # Plotly prediction bars & weather gauges
├── services/
│   ├── crop_diagnosis.py               # Cached PyTorch inference & Grad-CAM pipeline
│   ├── weather_service.py              # Open-Meteo API wrapper with 15-min cache
│   ├── fertilizer_service.py           # Deterministic nutrient arithmetic & bag counts
│   ├── product_verification.py         # SQLite queries & OpenCV QR decoding
│   └── scheme_matcher.py               # Statutory scheme matching engine
├── models/
│   ├── agrivision_cnn.pth              # Fine-tuned MobileNetV2 (9.3 MB)
│   ├── mobilenetv2_plant.pth           # Pretrained MobileNetV2 baseline (9.3 MB)
│   ├── agrivision_symptom_model.pkl    # Random Forest symptom classifier (5.1 MB)
│   └── class_names.json                # 38 PlantVillage disease classes
├── utils/
│   ├── config.py                       # Brand design tokens, paths, thresholds
│   ├── caching.py                      # st.cache_resource and st.cache_data wrappers
│   ├── validators.py                   # Form validation (land area, city, codes)
│   ├── image_processing.py             # EXIF normalization, resizing, leaf check
│   ├── database.py                     # SQLite connection manager & schemas
│   ├── gemini.py                       # Optional Gemini AI explanations & fallbacks
│   ├── gradcam.py                      # PyTorch gradient activation hooks
│   └── helpers.py                      # Shared labels, categories, formatters
├── data/
│   ├── fertilizer_data.json            # Deterministic crop nutrient lookup data
│   ├── schemes.json                    # 8 statutory central agricultural schemes
│   ├── symptoms.csv                    # Symptom classification training corpus
│   ├── products.db                     # Local SQLite product registry
│   └── sample_images/                  # Verified leaf images for instant testing
└── assets/
    └── images/                         # Agricultural photography & hero banners
```

---

## 🚀 Local Run Instructions

### 1. Prerequisites
- Python 3.10, 3.11, or 3.12 (Python 3.11 recommended).
- Git.

### 2. Setup Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

**On Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Model Weights Setup
If model files are not already present in `models/`, obtain them using the built-in downloader:
```bash
# Downloads pretrained MobileNetV2 checkpoint and generates class_names.json
python training/download_model.py

# Trains the Random Forest symptom classifier from data/symptoms.csv
python training/train_symptom_model.py
```

### 4. Configuration (Secrets)
Create your local environment file:
```bash
cp .env.example .env
```
*(Optional)* Add your Google Gemini API key to `.env` if you wish to enable dynamic AI explanation synthesis. When omitted, AgriVision seamlessly operates in **offline-fallback mode** using deterministic agronomic summaries without crashing.

### 5. Launch the Application
```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## ☁️ Deployment Guide

### Recommended Platform: **Streamlit Community Cloud**
Streamlit Community Cloud is the recommended deployment host:
- Native support for multipage Streamlit applications.
- Zero server maintenance, automatic rebuilds on GitHub push.
- The entire model bundle (`agrivision_cnn.pth` at ~9.3 MB + symptom model at ~5.1 MB) is under 20 MB, fitting well within repository and runtime limits.
- CPU inference is lightweight and responsive.

### Deployment Steps:
1. Push this repository to GitHub.
2. Sign in to [share.streamlit.io](https://share.streamlit.io/).
3. Click **"New app"** and select your repository, branch, and entry point:
   - **Repository:** `your-username/AGRICULTURE_VISION`
   - **Branch:** `main`
   - **Main file path:** `app.py`
4. Under **Advanced Settings**:
   - Python Version: Select **3.11** (matching `runtime.txt`).
   - Secrets: Add any optional keys (e.g. `GEMINI_API_KEY = "your-api-key"`).
5. Click **"Deploy!"**.

### Ephemeral Storage Note (SQLite)
Streamlit Cloud containers utilize ephemeral storage. If changes made to `data/products.db` must persist indefinitely across container restarts, mount a persistent volume (e.g., using Streamlit Secrets with a cloud database) or keep the registry pre-seeded using `utils/database.py:init_products_db()`, which automatically recreates and seeds the authentic demo products on boot.

---

## 🧪 Verification & Health Checks
You can run automated end-to-end verification of all five tools and inference models with:
```bash
python tools/test_services.py
```
