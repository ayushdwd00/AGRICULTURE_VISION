"""
training/download_model.py
==========================
Downloads the **pretrained** plant-disease classifier used by AgriVision.

Repository (Hugging Face)
-------------------------
    Daksh159/plant-disease-mobilenetv2      ->  mobilenetv2_plant.pth

Facts about that checkpoint (from its model card):

* Architecture : ``torchvision.models.mobilenet_v2`` with the ImageNet
  backbone frozen and ``classifier[1]`` replaced by a 38-way head.
* Dataset      : "New Plant Diseases Dataset (Augmented)" - PlantVillage
  (~87,000 images, 38 balanced classes).
* Input        : 224 x 224 RGB, ImageNet normalisation.
* Reported val accuracy: ~95%.

AgriVision does **not** train a vision model from scratch - it starts from
this checkpoint and later fine-tunes it (see ``training/fine_tune.py``).

The Hugging Face repository ships only the ``.pth`` file, so
``models/class_names.json`` is written from the canonical alphabetically
sorted PlantVillage class list (the order ``ImageFolder`` produced during
training, therefore the order of the model's logits).

Usage
-----
    python training/download_model.py              # download + write class names
    python training/download_model.py --force      # re-download
    python training/download_model.py --inspect    # print checkpoint structure
    python training/download_model.py --offline    # use the local HF cache only
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Any, Dict

# Allow "python training/download_model.py" from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.helpers import (  # noqa: E402  (import after sys.path fix)
    CANONICAL_PLANTVILLAGE_CLASSES,
    CLASS_NAMES_PATH,
    MODELS_DIR,
    PRETRAINED_MODEL_PATH,
    ensure_directories,
    save_json,
)

HF_REPO_ID = "Daksh159/plant-disease-mobilenetv2"
HF_FILENAME = "mobilenetv2_plant.pth"

def download_weights(
    force: bool = False, local_files_only: bool = False
) -> Path:
    """Download ``mobilenetv2_plant.pth`` into ``models/`` and return its path."""
    ensure_directories()
    if PRETRAINED_MODEL_PATH.exists() and not force:
        size_mb = PRETRAINED_MODEL_PATH.stat().st_size / 1_048_576
        print(f"[skip] {PRETRAINED_MODEL_PATH.name} already present ({size_mb:.1f} MB)")
        return PRETRAINED_MODEL_PATH

    try:
        from huggingface_hub import hf_hub_download
    except ImportError as exc:  # pragma: no cover - environment guard
        raise SystemExit(
            "huggingface_hub is not installed. Run:  pip install huggingface_hub"
        ) from exc

    print(f"[hf] downloading {HF_REPO_ID}/{HF_FILENAME} ...")
    cached_path = hf_hub_download(
        repo_id=HF_REPO_ID,
        filename=HF_FILENAME,
        local_files_only=local_files_only,
    )
    shutil.copy2(cached_path, PRETRAINED_MODEL_PATH)
    size_mb = PRETRAINED_MODEL_PATH.stat().st_size / 1_048_576
    print(f"[ok] saved -> {PRETRAINED_MODEL_PATH}  ({size_mb:.1f} MB)")
    return PRETRAINED_MODEL_PATH

def ensure_class_names(force: bool = False) -> Path:
    """Write ``models/class_names.json`` (38 canonical PlantVillage labels)."""
    ensure_directories()
    if CLASS_NAMES_PATH.exists() and not force:
        print(f"[skip] {CLASS_NAMES_PATH.name} already present")
        return CLASS_NAMES_PATH
    save_json(list(CANONICAL_PLANTVILLAGE_CLASSES), CLASS_NAMES_PATH)
    print(
        f"[ok] wrote {CLASS_NAMES_PATH} "
        f"({len(CANONICAL_PLANTVILLAGE_CLASSES)} class names)"
    )
    return CLASS_NAMES_PATH

def inspect_checkpoint(path: Path = PRETRAINED_MODEL_PATH) -> Dict[str, Any]:
    """Print a short structural summary of a ``.pth`` checkpoint."""
    import torch

    if not path.exists():
        raise SystemExit(f"Checkpoint not found: {path}")
    checkpoint = torch.load(path, map_location="cpu", weights_only=False)
    if isinstance(checkpoint, dict) and not any(
        key.startswith(("features", "classifier", "model")) for key in checkpoint
    ):
        state_dict = (
            checkpoint.get("state_dict")
            or checkpoint.get("model_state_dict")
            or checkpoint
        )
        print(f"[info] wrapper keys: {list(checkpoint.keys())[:8]}")
    else:
        state_dict = checkpoint
    print(f"[info] container type : {type(state_dict).__name__}")
    print(f"[info] tensor count   : {len(state_dict)}")
    classifier_keys = [key for key in state_dict if "classifier" in key]
    print(f"[info] classifier keys: {classifier_keys}")
    for key in classifier_keys:
        tensor = state_dict[key]
        if hasattr(tensor, "shape"):
            print(f"         {key:35s} shape={tuple(tensor.shape)}")
    return state_dict

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download the pretrained AgriVision plant-disease model."
    )
    parser.add_argument("--force", action="store_true", help="re-download even if present")
    parser.add_argument(
        "--offline", action="store_true", help="use the local Hugging Face cache only"
    )
    parser.add_argument(
        "--inspect", action="store_true", help="print the checkpoint structure"
    )
    args = parser.parse_args()

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    download_weights(force=args.force, local_files_only=args.offline)
    ensure_class_names(force=args.force)
    if args.inspect:
        inspect_checkpoint()
    print("[done] Module 1 asset download complete.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
