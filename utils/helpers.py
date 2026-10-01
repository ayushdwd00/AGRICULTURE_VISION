"""
utils/helpers.py
================
Single source of truth for paths, shared constants and small pure helpers used
across AgriVision.

Contents
--------
1. Project paths (models / data / evaluation directories)
2. JSON helpers
3. PlantVillage 38-class label utilities (crop name, condition, category,
   severity, healthy-vs-diseased)
4. Dataset folder-name normalisation (used by ``training/`` scripts)
5. Image loading + validation helpers that never raise inside Streamlit
6. Tiny formatting helpers for the UI

Nothing in this file depends on Streamlit, torch or an API key, so it is safe
to import from training scripts and from the Streamlit app alike.
"""

from __future__ import annotations

import io
import json
import os
import random
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from PIL import Image, UnidentifiedImageError

# 1. Paths

PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]
MODELS_DIR: Path = PROJECT_ROOT / "models"
DATA_DIR: Path = PROJECT_ROOT / "data"
TRAINING_DIR: Path = PROJECT_ROOT / "training"
EVALUATION_DIR: Path = DATA_DIR / "evaluation"
DATASET_DIR: Path = DATA_DIR / "dataset"
SAMPLE_IMAGES_DIR: Path = DATA_DIR / "sample_images"

# Model artefacts
CLASS_NAMES_PATH: Path = MODELS_DIR / "class_names.json"
PRETRAINED_MODEL_PATH: Path = MODELS_DIR / "mobilenetv2_plant.pth"
FINE_TUNED_MODEL_PATH: Path = MODELS_DIR / "agrivision_cnn.pth"
SYMPTOM_MODEL_PATH: Path = MODELS_DIR / "agrivision_symptom_model.pkl"

# Static data files
SYMPTOMS_CSV_PATH: Path = DATA_DIR / "symptoms.csv"
FERTILIZER_DATA_PATH: Path = DATA_DIR / "fertilizer_data.json"
SCHEMES_PATH: Path = DATA_DIR / "schemes.json"
PRODUCTS_DB_PATH: Path = DATA_DIR / "products.db"
RENTAL_DB_PATH: Path = DATA_DIR / "rentals.db"

# Shared constants
IMAGE_SIZE: int = 224
IMAGENET_MEAN: Tuple[float, float, float] = (0.485, 0.456, 0.406)
IMAGENET_STD: Tuple[float, float, float] = (0.229, 0.224, 0.225)
CONFIDENCE_THRESHOLD: float = 0.70  # Crop Doctor "trust the prediction" cut-off
UNCERTAIN_MESSAGE: str = (
    "Prediction uncertain. Please provide a clearer image / symptom description, "
    "or consult an agricultural expert."
)

def ensure_directories() -> None:
    """Create every directory AgriVision writes to (safe to call repeatedly)."""
    for directory in (
        MODELS_DIR,
        DATA_DIR,
        EVALUATION_DIR,
        DATASET_DIR,
        SAMPLE_IMAGES_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)

# 2. JSON helpers

def load_json(path: "Path | str", default: Any = None) -> Any:
    """Load JSON from ``path``; return ``default`` when missing or malformed."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default

def save_json(obj: Any, path: "Path | str", indent: int = 2) -> Path:
    """Write ``obj`` as pretty JSON and return the path that was written."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(obj, handle, indent=indent, ensure_ascii=False)
    return path

# 3. PlantVillage (38 classes) label utilities

#: Canonical class order of the "New Plant Diseases Dataset" (augmented
#: PlantVillage). The pretrained MobileNetV2 classifier was trained with
#: ``torchvision.datasets.ImageFolder``, which sorts folder names
#: alphabetically - this list is exactly that sorted order, so index i is
#: class i in the model output.
CANONICAL_PLANTVILLAGE_CLASSES: List[str] = [
    "Apple___Apple_scab",
    "Apple___Black_rot",
    "Apple___Cedar_apple_rust",
    "Apple___healthy",
    "Blueberry___healthy",
    "Cherry_(including_sour)___Powdery_mildew",
    "Cherry_(including_sour)___healthy",
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
    "Corn_(maize)___Common_rust_",
    "Corn_(maize)___Northern_Leaf_Blight",
    "Corn_(maize)___healthy",
    "Grape___Black_rot",
    "Grape___Esca_(Black_Measles)",
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)",
    "Grape___healthy",
    "Orange___Haunglongbing_(Citrus_greening)",
    "Peach___Bacterial_spot",
    "Peach___healthy",
    "Pepper,_bell___Bacterial_spot",
    "Pepper,_bell___healthy",
    "Potato___Early_blight",
    "Potato___Late_blight",
    "Potato___healthy",
    "Raspberry___healthy",
    "Soybean___healthy",
    "Squash___Powdery_mildew",
    "Strawberry___Leaf_scorch",
    "Strawberry___healthy",
    "Tomato___Bacterial_spot",
    "Tomato___Early_blight",
    "Tomato___Late_blight",
    "Tomato___Leaf_Mold",
    "Tomato___Septoria_leaf_spot",
    "Tomato___Spider_mites Two-spotted_spider_mite",
    "Tomato___Target_Spot",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato___Tomato_mosaic_virus",
    "Tomato___healthy",
]

#: Explicit folder aliases seen in the additional Kaggle dataset
#: (``emmarex/plantdisease`` -> ``PlantVillage/<folder>``). Generic
#: normalisation below already matches most of them; this table keeps the
#: mapping obvious and documented.
DATASET_FOLDER_ALIASES: Dict[str, str] = {
    "pepper__bell___bacterial_spot": "Pepper,_bell___Bacterial_spot",
    "pepper__bell___healthy": "Pepper,_bell___healthy",
    "tomato_bacterial_spot": "Tomato___Bacterial_spot",
    "tomato_early_blight": "Tomato___Early_blight",
    "tomato_late_blight": "Tomato___Late_blight",
    "tomato_leaf_mold": "Tomato___Leaf_Mold",
    "tomato_septoria_leaf_spot": "Tomato___Septoria_leaf_spot",
    "tomato_spider_mites_two_spotted_spider_mite": (
        "Tomato___Spider_mites Two-spotted_spider_mite"
    ),
    "tomato__target_spot": "Tomato___Target_Spot",
    "tomato__tomato_yellowleaf__curl_virus": (
        "Tomato___Tomato_Yellow_Leaf_Curl_Virus"
    ),
    "tomato__tomato_mosaic_virus": "Tomato___Tomato_mosaic_virus",
    "tomato_healthy": "Tomato___healthy",
    "potato___early_blight": "Potato___Early_blight",
    "potato___late_blight": "Potato___Late_blight",
    "potato___healthy": "Potato___healthy",
}

_CROP_DISPLAY: Dict[str, str] = {
    "Apple": "Apple",
    "Blueberry": "Blueberry",
    "Cherry_(including_sour)": "Cherry",
    "Corn_(maize)": "Maize (Corn)",
    "Grape": "Grape",
    "Orange": "Orange",
    "Peach": "Peach",
    "Pepper,_bell": "Bell Pepper",
    "Potato": "Potato",
    "Raspberry": "Raspberry",
    "Soybean": "Soybean",
    "Squash": "Squash",
    "Strawberry": "Strawberry",
    "Tomato": "Tomato",
}

_CONDITION_DISPLAY: Dict[str, str] = {
    "Apple_scab": "Apple scab",
    "Black_rot": "Black rot",
    "Cedar_apple_rust": "Cedar apple rust",
    "Powdery_mildew": "Powdery mildew",
    "Cercospora_leaf_spot Gray_leaf_spot": "Cercospora / gray leaf spot",
    "Common_rust_": "Common rust",
    "Northern_Leaf_Blight": "Northern leaf blight",
    "Esca_(Black_Measles)": "Esca (black measles)",
    "Leaf_blight_(Isariopsis_Leaf_Spot)": "Leaf blight (Isariopsis leaf spot)",
    "Haunglongbing_(Citrus_greening)": "Huanglongbing (citrus greening)",
    "Bacterial_spot": "Bacterial spot",
    "Early_blight": "Early blight",
    "Late_blight": "Late blight",
    "Leaf_Mold": "Leaf mould",
    "Septoria_leaf_spot": "Septoria leaf spot",
    "Spider_mites Two-spotted_spider_mite": "Two-spotted spider mite damage",
    "Target_Spot": "Target spot",
    "Tomato_Yellow_Leaf_Curl_Virus": "Tomato yellow leaf curl virus",
    "Tomato_mosaic_virus": "Tomato mosaic virus",
    "Leaf_scorch": "Leaf scorch",
    "healthy": "Healthy",
}

def normalize_label_key(name: str) -> str:
    """Normalise a class/folder name: lower-case, alphanumerics only."""
    return re.sub(r"[^a-z0-9]+", "", str(name).lower())

def canonical_from_dataset_folder(folder_name: str) -> Optional[str]:
    """
    Map a dataset folder name onto one of the 38 canonical PlantVillage labels.

    Returns ``None`` when the folder does not match a known class so callers
    can skip it safely.
    """
    raw = str(folder_name).strip()
    if raw in CANONICAL_PLANTVILLAGE_CLASSES:
        return raw
    alias = DATASET_FOLDER_ALIASES.get(raw.lower())
    if alias:
        return alias
    key = normalize_label_key(raw)
    for canonical in CANONICAL_PLANTVILLAGE_CLASSES:
        if normalize_label_key(canonical) == key:
            return canonical
    return None

def split_label(label: str) -> Tuple[str, str]:
    """Split ``"Tomato___Early_blight"`` into ``("Tomato", "Early blight")``."""
    crop_part, _, condition_part = str(label).partition("___")
    if not condition_part:
        return str(label), ""
    crop = _CROP_DISPLAY.get(crop_part, crop_part.replace("_", " ").strip())
    condition = _CONDITION_DISPLAY.get(
        condition_part, condition_part.replace("_", " ").strip().capitalize()
    )
    return crop, condition

def pretty_label(label: str) -> str:
    """Human readable label, e.g. ``"Tomato - Early blight"``."""
    crop, condition = split_label(label)
    if not condition:
        return crop
    return f"{crop} - {condition}"

def is_healthy_label(label: str) -> bool:
    """True when the class describes a healthy leaf."""
    _, condition = split_label(label)
    return condition.lower().startswith("healthy")

DISEASE_CATEGORIES: Tuple[str, ...] = (
    "healthy",
    "fungal",
    "bacterial",
    "viral",
    "pest",
    "unknown",
)

_PEST_KEYWORDS = ("spider", "mite", "thrip", "aphid", "borer", "worm")
_VIRAL_KEYWORDS = ("virus", "mosaic", "curl")
_BACTERIAL_KEYWORDS = ("bacterial", "haunglongbing", "greening", "canker")
_FUNGAL_KEYWORDS = (
    "blight", "rust", "mildew", "scab", "rot", "spot", "mold", "mould",
    "scorch", "esca", "measles", "septoria", "cercospora", "anthracnose",
    "wilt", "smut", "isariopsis",
)

def disease_category(label: str) -> str:
    """Coarse disease family used for severity and weather-risk hints."""
    if is_healthy_label(label):
        return "healthy"
    text = normalize_label_key(split_label(label)[1])
    if any(word in text for word in _PEST_KEYWORDS):
        return "pest"
    if any(word in text for word in _VIRAL_KEYWORDS):
        return "viral"
    if any(word in text for word in _BACTERIAL_KEYWORDS):
        return "bacterial"
    if any(word in text for word in _FUNGAL_KEYWORDS):
        return "fungal"
    return "unknown"

_SEVERITY_STEPS: Tuple[str, str, str] = ("Mild", "Moderate", "Severe")
_CATEGORY_BASE_STEP: Dict[str, int] = {
    "viral": 2,
    "bacterial": 1,
    "fungal": 1,
    "pest": 1,
    "unknown": 1,
}

def estimate_severity(label: str, confidence: float) -> str:
    """
    Deterministic (non-ML) severity hint shown next to a diagnosis.

    * healthy leaves            -> ``"None (healthy)"``
    * otherwise a base level per disease family, shifted one step up or down
      by the model confidence.

    This is a presentation heuristic, not an agronomic measurement.
    """
    category = disease_category(label)
    if category == "healthy":
        return "None (healthy)"
    step = _CATEGORY_BASE_STEP.get(category, 1)
    if confidence >= 0.90:
        step += 1
    elif confidence < 0.75:
        step -= 1
    step = max(0, min(len(_SEVERITY_STEPS) - 1, step))
    return _SEVERITY_STEPS[step]

def load_class_names(path: "Path | str" = CLASS_NAMES_PATH) -> List[str]:
    """
    Load the 38 class names used by the vision model.

    Falls back to the built-in canonical list when the file is missing so the
    application can still describe a model that was trained outside AgriVision.
    """
    names = load_json(path)
    if isinstance(names, dict):  # tolerate {"0": "Apple___healthy", ...}
        names = [names[key] for key in sorted(names, key=lambda k: int(k))]
    if isinstance(names, list) and len(names) >= 2:
        return [str(name) for name in names]
    return list(CANONICAL_PLANTVILLAGE_CLASSES)

# 4. Dataset helpers (shared by training/download_dataset.py and evaluate.py)

IMAGE_EXTENSIONS: Tuple[str, ...] = (
    ".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff", ".JPG", ".JPEG", ".PNG",
)

def list_image_files(directory: "Path | str", limit: Optional[int] = None) -> List[Path]:
    """Return image files inside ``directory`` sorted for reproducibility."""
    directory = Path(directory)
    if not directory.is_dir():
        return []
    files = sorted(
        (child for child in directory.iterdir()
         if child.is_file() and child.suffix in IMAGE_EXTENSIONS),
        key=lambda p: p.name.lower(),
    )
    return files[:limit] if limit else files

def find_class_directories(root: "Path | str") -> Dict[str, Path]:
    """
    Walk ``root`` and return ``{canonical_label: directory}`` for every folder
    that maps onto one of the 38 PlantVillage classes.

    Only leaf directories containing images are considered, so nested layouts
    such as ``PlantVillage/PlantVillage/Tomato_healthy`` work out of the box.
    """
    found: Dict[str, Path] = {}
    for current, _subdirs, files in os.walk(str(root)):
        has_images = any(Path(name).suffix in IMAGE_EXTENSIONS for name in files)
        if not has_images:
            continue
        canonical = canonical_from_dataset_folder(Path(current).name)
        if canonical and canonical not in found:
            found[canonical] = Path(current)
    return found

def count_images_by_class(root: "Path | str") -> Dict[str, int]:
    """``{canonical_label: number_of_images}`` for a dataset directory."""
    return {
        label: len(list_image_files(directory))
        for label, directory in find_class_directories(root).items()
    }

# 5. Image helpers

def load_image_from_bytes(data: bytes) -> Image.Image:
    """
    Convert raw upload bytes into a validated ``RGB`` PIL image.

    Raises ``ValueError`` with a farmer friendly message for invalid input so
    the Streamlit layer can show a warning instead of crashing.
    """
    if not data:
        raise ValueError("The uploaded file is empty. Please choose a crop image.")
    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except UnidentifiedImageError as exc:  # not an image at all
        raise ValueError(
            "That file could not be read as an image. Please upload a JPG or PNG photo of a leaf."
        ) from exc
    except Exception as exc:  # truncated / corrupt file
        raise ValueError(f"The image could not be opened ({exc}). Please try another photo.") from exc
    return image.convert("RGB")

def is_probably_leaf_image(
    image: Image.Image, min_size: int = 64, min_saturation: float = 0.05
) -> bool:
    """
    Very light sanity check used to warn about obviously unsuitable uploads
    (blank scans, screenshots of text, thumbnails that are too small).

    Heuristic only - the UI shows a *warning*, never a hard block.
    """
    if min(image.size) < min_size:
        return False
    small = image.convert("RGB").resize((64, 64))
    pixels = list(small.getdata())
    if not pixels:
        return False
    max_sat = 0.0
    for red, green, blue in pixels:
        high, low = max(red, green, blue), min(red, green, blue)
        max_sat = max(max_sat, (high - low) / 255.0)
    return max_sat >= min_saturation

# 6. Small formatting / misc helpers

def format_percent(value: float, digits: int = 1) -> str:
    """``0.9345 -> "93.5%"`` (defensive against ``None``/NaN)."""
    try:
        return f"{float(value) * 100:.{digits}f}%"
    except (TypeError, ValueError):
        return "n/a"

def confidence_band(value: float) -> str:
    """Human readable confidence band used for colour coding in the UI."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "Unknown"
    if value >= 0.85:
        return "High"
    if value >= CONFIDENCE_THRESHOLD:
        return "Medium"
    return "Low"

def seed_everything(seed: int = 42) -> None:
    """Make training runs reproducible enough for a college project."""
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import numpy as np
        import torch

        np.random.seed(seed)
        torch.manual_seed(seed)
    except ImportError:  # torch not needed for every script
        pass

def timestamp() -> str:
    """Local timestamp string used for records and logs."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def safe_slug(value: str) -> str:
    """Filesystem friendly slug (used for saved report/plot names)."""
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", str(value)).strip("_").lower() or "item"
