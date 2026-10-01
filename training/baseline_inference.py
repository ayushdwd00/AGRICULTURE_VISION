"""
training/baseline_inference.py
==============================
Sanity check for the **pretrained** MobileNetV2 plant-disease model - run this
BEFORE any fine-tuning.

It loads
    * the MobileNetV2 architecture used by the published checkpoint
    * ``models/mobilenetv2_plant.pth``
    * ``models/class_names.json`` (38 PlantVillage classes)
    * the sample leaf photos in ``data/sample_images/``
runs inference on each of them and prints the predicted class, the confidence
and the top-3 candidates.  Every sample photo has a known label, so the script
also reports how many of them the pretrained model gets right - that is the
"baseline" the fine-tuning step is compared against.

Usage
-----
    python training/baseline_inference.py
    python training/baseline_inference.py --image path/to/leaf.jpg
    python training/baseline_inference.py --gradcam          # + Grad-CAM overlays
    python training/baseline_inference.py --weights mobilenetv2_plant.pth
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from modules.crop_doctor import (  # noqa: E402
    get_model,
    gradcam_for_image,
    model_status,
    predict_from_image,
)
from utils.helpers import (  # noqa: E402
    EVALUATION_DIR,
    SAMPLE_IMAGES_DIR,
    ensure_directories,
    format_percent,
    load_image_from_bytes,
    pretty_label,
    save_json,
)

#: Known class of every bundled sample photo (used to score the baseline).
SAMPLE_EXPECTATIONS: Dict[str, str] = {
    "sample_tomato_early_blight.jpg": "Tomato___Early_blight",
    "sample_tomato_healthy.jpg": "Tomato___healthy",
    "sample_potato_late_blight.jpg": "Potato___Late_blight",
    "sample_pepper_bacterial_spot.jpg": "Pepper,_bell___Bacterial_spot",
    "sample_tomato_mosaic_virus.jpg": "Tomato___Tomato_mosaic_virus",
    "sample_tomato_yellow_leaf_curl.jpg": "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
}

def _read_image(path: Path):
    with open(path, "rb") as handle:
        return load_image_from_bytes(handle.read())

def _collect_images(single: Optional[str]) -> List[Path]:
    if single:
        path = Path(single)
        if not path.exists():
            raise SystemExit(f"Image not found: {path}")
        return [path]
    if not SAMPLE_IMAGES_DIR.exists():
        raise SystemExit(
            f"No sample images found in {SAMPLE_IMAGES_DIR}. "
            "Add leaf photos there or pass --image <path>."
        )
    images = sorted(
        path for path in SAMPLE_IMAGES_DIR.iterdir()
        if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    )
    if not images:
        raise SystemExit(f"{SAMPLE_IMAGES_DIR} contains no images.")
    return images

def main() -> int:
    parser = argparse.ArgumentParser(description="Baseline inference for the AgriVision model.")
    parser.add_argument("--image", default=None, help="single image to test")
    parser.add_argument(
        "--weights", default="mobilenetv2_plant.pth", help="checkpoint file name inside models/"
    )
    parser.add_argument("--top-k", type=int, default=3, help="how many candidates to print")
    parser.add_argument("--gradcam", action="store_true", help="also save Grad-CAM overlays")
    args = parser.parse_args()

    ensure_directories()
    status = model_status()
    print("[model-status] " + ", ".join(
        f"{key}={value}" for key, value in status.items() if key != "weights"
    ))
    weights_requested = (
        args.weights if args.weights in status["weights"] else None
    )
    if weights_requested is None:
        print(f"[note] '{args.weights}' is not in models/ - using the best available checkpoint.")

    try:
        model, class_names, weights_path = get_model(weights_name=weights_requested)
    except FileNotFoundError as exc:
        raise SystemExit(str(exc))

    print(
        f"[model] using {weights_path.name} | classes={len(class_names)} "
        f"| device={next(model.parameters()).device.type}"
    )

    results: List[dict] = []
    correct = 0
    scored = 0

    for image_path in _collect_images(args.image):
        try:
            image = _read_image(image_path)
        except ValueError as exc:
            print(f"[skip] {image_path.name}: {exc}")
            continue

        prediction = predict_from_image(
            image,
            model=model,
            class_names=class_names,
            weights_path=weights_path,
            top_k=args.top_k,
        )
        if prediction.get("error"):
            print(f"[error] {image_path.name}: {prediction['error']}")
            continue

        expected = SAMPLE_EXPECTATIONS.get(image_path.name)
        match = None if expected is None else (expected == prediction["label"])
        if expected is not None:
            scored += 1
            correct += int(bool(match))

        print(f"\n[image] {image_path.name}")
        print(f"        predicted   : {pretty_label(prediction['label'])}")
        print(f"                      ({prediction['label']})")
        print(f"        confidence  : {format_percent(prediction['confidence'])}")
        print(f"        severity    : {prediction['severity']}")
        for rank, candidate in enumerate(prediction["top_predictions"][1:], start=2):
            print(
                f"        candidate {rank}: {pretty_label(candidate['label'])} "
                f"({format_percent(candidate['confidence'])})"
            )
        if expected is not None:
            print(
                f"        known label : {pretty_label(expected)} -> "
                f"{'MATCH' if match else 'MISMATCH'}"
            )

        record = {
            "image": image_path.name,
            "predicted": prediction["label"],
            "confidence": prediction["confidence"],
            "expected": expected,
            "match": match,
            "top_predictions": prediction["top_predictions"],
            "weights": weights_path.name,
        }

        if args.gradcam:
            explanation = gradcam_for_image(
                image, target_label=prediction["label"]
            )
            if explanation.get("error"):
                print(f"        gradcam     : {explanation['error']}")
            else:
                out_dir = EVALUATION_DIR / "gradcam_samples"
                out_dir.mkdir(parents=True, exist_ok=True)
                overlay_path = out_dir / f"{image_path.stem}_gradcam.png"
                explanation["overlay_image"].save(overlay_path)
                print(f"        gradcam     : saved {overlay_path.name}")
                record["gradcam"] = str(overlay_path)

        results.append(record)

    summary = {
        "weights": weights_path.name,
        "images_tested": len(results),
        "images_with_known_label": scored,
        "correct": correct,
        "sample_accuracy": (correct / scored) if scored else None,
        "results": results,
    }
    save_json(summary, EVALUATION_DIR / "baseline_inference.json")

    print("\n" + "=" * 62)
    if scored:
        print(
            f"[summary] pretrained model matched {correct}/{scored} known sample labels "
            f"({format_percent(correct / scored)})"
        )
    else:
        print(f"[summary] inference completed for {len(results)} image(s)")
    print(f"[ok] results -> {EVALUATION_DIR / 'baseline_inference.json'}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
