"""
modules/symptom_model.py
========================
MODULE 1 (part 2) - the **symptom classifier** of the Crop Doctor.

What it does
------------
* Turns free text ("lower leaves are turning yellow and the plant is small")
  into a small set of binary symptom features plus TF-IDF text features.
* Classifies the text with a scikit-learn **Random Forest**.
* ``predict_symptoms(text)`` -> ``{"label": ..., "confidence": 0.00}``

Symptom features used (as required by the brief): leaf colour change,
spot pattern, wilting, leaf curling and stunted growth.  They are extracted
from the text with transparent keyword rules (`extract_symptom_flags`) so the
same feature space is available both for training and for inference.

The trained model is stored in ``models/agrivision_symptom_model.pkl`` and is
produced by ``training/train_symptom_model.py`` from ``data/symptoms.csv``.
"""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline

from utils.helpers import (
    SYMPTOM_MODEL_PATH,
    SYMPTOMS_CSV_PATH,
    confidence_band,
    load_json,
    save_json,
)

TEXT_COLUMN: str = "symptom_text"
LABEL_COLUMN: str = "label"
FLAG_COLUMNS: List[str] = [
    "leaf_colour_change",
    "spot_pattern",
    "wilting",
    "leaf_curling",
    "stunted_growth",
]
CSV_COLUMNS: List[str] = [TEXT_COLUMN, *FLAG_COLUMNS, LABEL_COLUMN]

# Transparent keyword rules for the five binary symptom features

FLAG_KEYWORDS: Dict[str, Tuple[str, ...]] = {
    "leaf_colour_change": (
        "yellow", "yellowing", "pale", "chlorosis", "chlorotic", "brown",
        "black", "purple", "dark", "orange", "white", "grey", "gray",
        "silver", "bronze", "discolour", "discolor", "pale green",
    ),
    "spot_pattern": (
        "spot", "spots", "speckle", "blotch", "lesion", "patch", "dot",
        "ring", "concentric", "rust", "powder", "mildew", "mould", "mold",
        "rot", "smut", "pustule", "webbing",
    ),
    "wilting": (
        "wilt", "wilting", "droop", "sagging", "limp", "collapsed",
        "drying", "dry out", "dried out", "dry up", "drying out",
        "dead patch", "dying",
    ),
    "leaf_curling": (
        "curl", "curling", "cupped", "twisted", "rolled", "crinkled",
        "puckered", "mosaic", "distorted", "wrinkled",
    ),
    "stunted_growth": (
        "stunted", "slow growth", "slow growing", "growing slowly", "slowly",
        "small leaves", "no growth", "poor growth", "dwarf", "short plant",
        "fewer leaves", "not growing", "small plant", "thinner", "weak growth",
        "weak plant", "the plant is weak", "growth has stopped", "stalls",
    ),
}

# Label metadata (family is used by the Crop Doctor fusion logic)

SYMPTOM_META: Dict[str, Dict[str, str]] = {
    "Nitrogen Deficiency": {
        "family": "nutrient",
        "severity": "Moderate",
        "advice": "Nutrient related - use the Fertilizer Calculator to size a nitrogen dose.",
    },
    "Phosphorus Deficiency": {
        "family": "nutrient",
        "severity": "Moderate",
        "advice": "Nutrient related - phosphatic fertiliser plus soil pH check is usually advised.",
    },
    "Potassium Deficiency": {
        "family": "nutrient",
        "severity": "Moderate",
        "advice": "Nutrient related - potash (MOP) top dressing is the usual correction.",
    },
    "Fungal Leaf Spot / Blight": {
        "family": "fungal",
        "severity": "Severe",
        "advice": "Typical of a fungal infection - remove affected leaves and consult an expert for a fungicide schedule.",
    },
    "Bacterial Infection": {
        "family": "bacterial",
        "severity": "Severe",
        "advice": "Bacterial diseases spread with rain splash - avoid overhead irrigation and consult an expert.",
    },
    "Viral Infection": {
        "family": "viral",
        "severity": "Severe",
        "advice": "Viral diseases cannot be cured - control the insect vector and remove infected plants.",
    },
    "Pest Attack (mites / insects)": {
        "family": "pest",
        "severity": "Moderate",
        "advice": "Look under the leaves for mites/insects and act early with an approved control.",
    },
    "Water Stress (over/under watering)": {
        "family": "water",
        "severity": "Mild",
        "advice": "Irrigation related - check soil moisture before the next watering.",
    },
    "Heat & Sunlight Stress": {
        "family": "environment",
        "severity": "Mild",
        "advice": "Weather related - shade or extra irrigation during the hot hours usually helps.",
    },
    "Healthy Crop": {
        "family": "healthy",
        "severity": "None (healthy)",
        "advice": "No clear symptom pattern - continue normal monitoring.",
    },
}

SYMPTOM_LABELS: List[str] = list(SYMPTOM_META.keys())

def label_meta(label: str) -> Dict[str, str]:
    """Metadata for a symptom label (safe defaults when unknown)."""
    return SYMPTOM_META.get(
        str(label),
        {"family": "unknown", "severity": "Moderate", "advice": "Consult an agricultural expert."},
    )

# Text -> symptom features

def extract_symptom_flags(text: str) -> Dict[str, int]:
    """
    Derive the five binary symptom features from free text.

    Simple, explainable keyword rules - the same function is used when building
    the training data (validation only) and for live inference, so the feature
    space can never drift apart.
    """
    lowered = str(text or "").lower()
    return {
        column: int(any(keyword in lowered for keyword in FLAG_KEYWORDS[column]))
        for column in FLAG_COLUMNS
    }

def extract_cues(text: str) -> List[str]:
    """Return the matched symptom words - shown in the UI as 'detected cues'."""
    lowered = str(text or "").lower()
    cues: List[str] = []
    for column in FLAG_COLUMNS:
        for keyword in FLAG_KEYWORDS[column]:
            if keyword in lowered and keyword not in cues:
                cues.append(keyword)
    return cues

def describe_flags(flags: Dict[str, int]) -> List[str]:
    """Human readable list of the symptom features that are present."""
    pretty = {
        "leaf_colour_change": "leaf colour change",
        "spot_pattern": "spot / lesion pattern",
        "wilting": "wilting",
        "leaf_curling": "leaf curling",
        "stunted_growth": "stunted growth",
    }
    return [pretty[column] for column in FLAG_COLUMNS if flags.get(column)]

# Training

def build_pipeline(n_estimators: int = 300, random_state: int = 42) -> Pipeline:
    """TF-IDF (word 1-2 grams) + the five binary symptom features -> RandomForest."""
    features = ColumnTransformer(
        transformers=[
            (
                "text",
                TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True),
                TEXT_COLUMN,
            ),
            ("flags", "passthrough", FLAG_COLUMNS),
        ],
        remainder="drop",
    )
    return Pipeline(
        steps=[
            ("features", features),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=n_estimators,
                    random_state=random_state,
                    class_weight="balanced",
                    n_jobs=-1,
                ),
            ),
        ]
    )

def load_symptom_dataset(csv_path: "Path | str" = SYMPTOMS_CSV_PATH) -> pd.DataFrame:
    """Read ``data/symptoms.csv`` and validate its columns."""
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Symptom dataset not found: {path}. Run: python training/build_symptom_dataset.py"
        )
    frame = pd.read_csv(path)
    missing = [column for column in CSV_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"{path.name} is missing columns: {missing}")
    return frame[CSV_COLUMNS].dropna(subset=[TEXT_COLUMN, LABEL_COLUMN])

def train_symptom_model(
    csv_path: "Path | str" = SYMPTOMS_CSV_PATH,
    model_path: "Path | str" = SYMPTOM_MODEL_PATH,
    n_estimators: int = 300,
    test_size: float = 0.2,
    random_state: int = 42,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Train the Random Forest symptom classifier and save it to ``model_path``.

    Returns a metrics dictionary (accuracy, per-class report, row counts) which
    the training script stores for the project report.
    """
    import joblib
    from sklearn.metrics import accuracy_score, classification_report
    from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split

    from utils.helpers import timestamp

    frame = load_symptom_dataset(csv_path)

    # Transparency check: how well do the keyword rules reproduce the symptom
    # flags that were hand labelled in data/symptoms.csv?
    mismatches = 0
    for _, row in frame.iterrows():
        derived = extract_symptom_flags(row[TEXT_COLUMN])
        for column in FLAG_COLUMNS:
            if int(row[column]) != derived[column]:
                mismatches += 1

    train_frame, test_frame = train_test_split(
        frame,
        test_size=test_size,
        random_state=random_state,
        stratify=frame[LABEL_COLUMN],
    )

    pipeline = build_pipeline(n_estimators=n_estimators, random_state=random_state)
    pipeline.fit(train_frame, train_frame[LABEL_COLUMN])

    predictions = pipeline.predict(test_frame)
    accuracy = float(accuracy_score(test_frame[LABEL_COLUMN], predictions))
    report = classification_report(test_frame[LABEL_COLUMN], predictions, zero_division=0)

    # A single small split is noisy, so we also report 5-fold stratified
    # cross-validation on the whole dataset (more reliable for the report).
    cross_val_accuracy = float("nan")
    cross_val_std = float("nan")
    folds = int(min(5, frame[LABEL_COLUMN].value_counts().min()))
    if folds >= 2:
        try:
            scores = cross_val_score(
                build_pipeline(n_estimators=n_estimators, random_state=random_state),
                frame,
                frame[LABEL_COLUMN],
                cv=StratifiedKFold(n_splits=folds, shuffle=True, random_state=random_state),
                scoring="accuracy",
            )
            cross_val_accuracy = float(scores.mean())
            cross_val_std = float(scores.std())
        except ValueError:
            pass

    payload = {
        "pipeline": pipeline,
        "labels": SYMPTOM_LABELS,
        "text_column": TEXT_COLUMN,
        "flag_columns": FLAG_COLUMNS,
        "trained_at": timestamp(),
        "accuracy": accuracy,
        "n_rows": int(len(frame)),
        "n_train": int(len(train_frame)),
        "n_test": int(len(test_frame)),
        "n_estimators": int(n_estimators),
        "flag_rule_mismatches": int(mismatches),
        "report": report,
        "cross_val_accuracy": cross_val_accuracy,
        "cross_val_std": cross_val_std,
        "cross_val_folds": folds,
    }
    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(payload, model_path)
    load_symptom_model.cache_clear()

    if verbose:
        print(f"[symptom] rows={len(frame)} train={len(train_frame)} test={len(test_frame)}")
        print(f"[symptom] keyword-rule vs CSV flag mismatches: {mismatches}")
        print(f"[symptom] held-out accuracy: {accuracy:.4f}")
        if folds >= 2:
            print(
                f"[symptom] {folds}-fold cross-validation accuracy: "
                f"{cross_val_accuracy:.4f} +/- {cross_val_std:.4f}"
            )
        print(report)
        print(f"[ok] saved symptom model -> {model_path}")

    return {
        "accuracy": accuracy,
        "report": report,
        "n_rows": int(len(frame)),
        "n_train": int(len(train_frame)),
        "n_test": int(len(test_frame)),
        "flag_rule_mismatches": int(mismatches),
        "labels": SYMPTOM_LABELS,
        "cross_val_accuracy": cross_val_accuracy,
        "cross_val_std": cross_val_std,
        "cross_val_folds": folds,
    }

# Inference

@functools.lru_cache(maxsize=2)
def load_symptom_model(model_path: str = str(SYMPTOM_MODEL_PATH)) -> Dict[str, Any]:
    """Load (and cache) the pickled symptom model payload."""
    import joblib

    path = Path(model_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Symptom model not found: {path}. "
            "Run: python training/build_symptom_dataset.py && python training/train_symptom_model.py"
        )
    payload = joblib.load(path)
    if not isinstance(payload, dict) or "pipeline" not in payload:
        raise ValueError(f"{path.name} does not look like an AgriVision symptom model.")
    return payload

def symptom_model_status() -> Dict[str, Any]:
    """Status dictionary for the UI / dashboard."""
    payload: Dict[str, Any]
    try:
        payload = load_symptom_model()
        available = True
        error = None
    except (FileNotFoundError, ValueError) as exc:
        payload = {}
        available = False
        error = str(exc)
    return {
        "available": available,
        "path": str(SYMPTOM_MODEL_PATH),
        "labels": payload.get("labels", SYMPTOM_LABELS),
        "accuracy": payload.get("accuracy"),
        "trained_at": payload.get("trained_at"),
        "n_rows": payload.get("n_rows"),
        "error": error,
    }

def _symptom_error(message: str) -> Dict[str, Any]:
    return {
        "label": None,
        "confidence": 0.0,
        "pretty_label": None,
        "family": None,
        "severity": None,
        "advice": None,
        "flags": {},
        "cues": [],
        "detected_features": [],
        "model": str(SYMPTOM_MODEL_PATH.name),
        "is_uncertain": True,
        "confidence_band": "Unknown",
        "error": message,
    }

def predict_symptoms(text: str, model_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Public API required by the project brief.

    Parameters
    ----------
    text:
        Farmer's free-text description of the symptoms (typed or dictated).
    model_path:
        Optional override for the pickled model location.

    Returns
    -------
    ``{"label": "...", "confidence": 0.00, ...}`` plus the extracted symptom
    features, the disease family and a short advice string.
    """
    cleaned = str(text or "").strip()
    if len(cleaned) < 3:
        return _symptom_error(
            "Please describe what you can see on the plant (for example: "
            "'yellow leaves with brown spots and wilting')."
        )

    try:
        payload = load_symptom_model(model_path or str(SYMPTOM_MODEL_PATH))
        pipeline = payload["pipeline"]
        flags = extract_symptom_flags(cleaned)
        row = pd.DataFrame([{TEXT_COLUMN: cleaned, **flags}])

        label = str(pipeline.predict(row)[0])
        probabilities = pipeline.predict_proba(row)[0]
        classes = list(pipeline.named_steps["classifier"].classes_)
        confidence = float(probabilities[classes.index(label)]) if label in classes else 0.0
        # Fall back to the best probability when the predicted label is unknown.
        if confidence == 0.0:
            best = int(probabilities.argmax())
            label = str(classes[best])
            confidence = float(probabilities[best])

        meta = label_meta(label)
        return {
            "label": label,
            "confidence": confidence,
            "pretty_label": label,
            "family": meta["family"],
            "severity": meta["severity"],
            "advice": meta["advice"],
            "flags": flags,
            "cues": extract_cues(cleaned),
            "detected_features": describe_flags(flags),
            "model": SYMPTOM_MODEL_PATH.name,
            "is_uncertain": confidence < 0.50,
            "confidence_band": confidence_band(confidence),
            "error": None,
        }
    except (FileNotFoundError, ValueError) as exc:
        return _symptom_error(str(exc))
    except Exception as exc:  # pragma: no cover - defensive: never crash the app
        return _symptom_error(f"Symptom analysis failed: {type(exc).__name__}: {exc}")
