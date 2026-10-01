"""
training/train_symptom_model.py
===============================
Trains the Crop Doctor's symptom classifier (scikit-learn Random Forest) from
``data/symptoms.csv`` and writes ``models/agrivision_symptom_model.pkl``.

The heavy lifting lives in :func:`modules.symptom_model.train_symptom_model` so
the Streamlit app and this script share one implementation.

Usage
-----
    python training/train_symptom_model.py
    python training/train_symptom_model.py --n-estimators 500 --test-size 0.25
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from modules.symptom_model import train_symptom_model  # noqa: E402
from utils.helpers import (  # noqa: E402
    EVALUATION_DIR,
    SYMPTOM_MODEL_PATH,
    SYMPTOMS_CSV_PATH,
    ensure_directories,
    save_json,
)

def main() -> int:
    parser = argparse.ArgumentParser(description="Train the AgriVision symptom classifier.")
    parser.add_argument("--csv", default=str(SYMPTOMS_CSV_PATH), help="training CSV")
    parser.add_argument("--out", default=str(SYMPTOM_MODEL_PATH), help="output .pkl path")
    parser.add_argument("--n-estimators", type=int, default=300, help="RandomForest trees")
    parser.add_argument("--test-size", type=float, default=0.2, help="held-out fraction")
    parser.add_argument("--seed", type=int, default=42, help="random state")
    args = parser.parse_args()

    ensure_directories()
    metrics = train_symptom_model(
        csv_path=args.csv,
        model_path=args.out,
        n_estimators=args.n_estimators,
        test_size=args.test_size,
        random_state=args.seed,
    )

    metrics_path = EVALUATION_DIR / "symptom_model_metrics.json"
    save_json(
        {
            "model": Path(args.out).name,
            "csv": Path(args.csv).name,
            "accuracy": metrics["accuracy"],
            "n_rows": metrics["n_rows"],
            "n_train": metrics["n_train"],
            "n_test": metrics["n_test"],
            "labels": metrics["labels"],
            "keyword_rule_vs_csv_flag_mismatches": metrics["flag_rule_mismatches"],
        },
        metrics_path,
    )
    (EVALUATION_DIR / "symptom_model_report.txt").write_text(
        metrics["report"], encoding="utf-8"
    )
    print(f"[ok] metrics -> {metrics_path}")
    print(f"[ok] classification report -> {EVALUATION_DIR / 'symptom_model_report.txt'}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
