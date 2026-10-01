"""
training/download_dataset.py
============================
Downloads the **additional agriculture dataset** used to fine-tune the
plant-disease model and copies a manageable, balanced subset into::

    data/dataset/train/<canonical_class>/*.jpg
    data/dataset/val/<canonical_class>/*.jpg

Source: ``emmarex/plantdisease`` (PlantVillage, 15 crop/disease folders) fetched
with ``kagglehub``.

Why a subset?
    AgriVision fine-tunes on modest hardware (CPU / free Colab), and the goal is
    *fine-tuning* a pretrained model - not training from scratch - so a few
    hundred balanced images are enough while keeping every run short.

Folder names in the Kaggle dataset differ slightly from the canonical
PlantVillage names (``Tomato_Early_blight`` vs ``Tomato___Early_blight``), so
they are normalised through ``utils.helpers.canonical_from_dataset_folder``.

Usage
-----
    python training/download_dataset.py                     # 30 train / 10 val per class
    python training/download_dataset.py --train-per-class 40 --val-per-class 10
    python training/download_dataset.py --list-only         # show what is available
    python training/download_dataset.py --force             # re-copy existing files
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Dict, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.helpers import (  # noqa: E402
    DATASET_DIR,
    EVALUATION_DIR,
    ensure_directories,
    find_class_directories,
    list_image_files,
    save_json,
    seed_everything,
    timestamp,
)

KAGGLE_DATASET = "emmarex/plantdisease"

def download_source_dataset() -> Path:
    """Return the local path of the Kaggle dataset (downloading it if needed)."""
    try:
        import kagglehub
    except ImportError as exc:  # pragma: no cover - environment guard
        raise SystemExit("kagglehub is not installed. Run:  pip install kagglehub") from exc

    print(f"[kaggle] fetching {KAGGLE_DATASET} (the local kagglehub cache is reused when present)")
    try:
        path = Path(kagglehub.dataset_download(KAGGLE_DATASET))
    except Exception as exc:  # network / credentials / rate limit
        raise SystemExit(
            "Could not download the dataset via kagglehub.\n"
            f"  reason     : {type(exc).__name__}: {exc}\n"
            "  what to do : check your internet connection, or place Kaggle API\n"
            "               credentials at %USERPROFILE%\\.kaggle\\kaggle.json and retry."
        ) from exc
    print(f"[kaggle] local copy at {path}")
    return path

def discover_classes(root: Path) -> Dict[str, Path]:
    """``{canonical_label: folder}`` for every class folder found under ``root``."""
    directories = find_class_directories(root)
    if not directories:
        raise SystemExit(
            f"No plant-disease class folders were found inside {root}. "
            "The dataset layout may have changed - please check the archive."
        )
    return directories

def copy_subset(
    class_dirs: Dict[str, Path],
    train_per_class: int,
    val_per_class: int,
    force: bool = False,
    seed: int = 42,
) -> Tuple[Dict[str, int], Dict[str, Dict[str, int]]]:
    """
    Copy ``train_per_class`` + ``val_per_class`` images per class into
    ``data/dataset``.  Returns ``(totals, per_class_counts)``.
    """
    seed_everything(seed)
    totals = {"train": 0, "val": 0}
    counts: Dict[str, Dict[str, int]] = {}

    for label in sorted(class_dirs):
        files = list_image_files(class_dirs[label])
        needed = train_per_class + val_per_class
        if len(files) < needed:
            print(
                f"[warn] {label}: only {len(files)} images available - "
                "using a proportional subset instead"
            )

        # Deterministic interleaving instead of a random shuffle, so repeated
        # runs copy exactly the same files (keeps the evaluation reproducible).
        step = max(1, len(files) // max(1, needed))
        selected = files[::step][:needed]
        val_files = selected[:val_per_class]
        train_files = selected[val_per_class:]

        counts[label] = {"available": len(files), "train": 0, "val": 0}
        for split, split_files in (("train", train_files), ("val", val_files)):
            target_dir = DATASET_DIR / split / label
            target_dir.mkdir(parents=True, exist_ok=True)
            for source in split_files:
                destination = target_dir / source.name
                if destination.exists() and not force:
                    counts[label][split] += 1
                    continue
                try:
                    shutil.copy2(source, destination)
                    counts[label][split] += 1
                except OSError as exc:
                    print(f"[warn] could not copy {source.name}: {exc}")
            totals[split] += counts[label][split]

    return totals, counts

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download PlantVillage (kagglehub) and build a fine-tuning subset."
    )
    parser.add_argument("--train-per-class", type=int, default=30)
    parser.add_argument("--val-per-class", type=int, default=10)
    parser.add_argument("--out", default=str(DATASET_DIR), help="output directory")
    parser.add_argument("--force", action="store_true", help="re-copy existing files")
    parser.add_argument("--list-only", action="store_true", help="only report available classes")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    ensure_directories()
    source_root = download_source_dataset()
    class_dirs = discover_classes(source_root)

    print(f"\n[info] {len(class_dirs)} canonical classes available in the downloaded dataset:")
    for label in sorted(class_dirs):
        print(f"       {label:<50s} {len(list_image_files(class_dirs[label])):>6d} images")

    if args.list_only:
        return 0

    totals, counts = copy_subset(
        class_dirs,
        train_per_class=args.train_per_class,
        val_per_class=args.val_per_class,
        force=args.force,
        seed=args.seed,
    )

    print(f"\n[ok] copied train={totals['train']} val={totals['val']} images into {DATASET_DIR}")
    for label in sorted(counts):
        row = counts[label]
        print(
            f"       {label:<50s} train={row['train']:>3d} val={row['val']:>3d} "
            f"(source had {row['available']})"
        )

    manifest = {
        "source": KAGGLE_DATASET,
        "source_path": str(source_root),
        "created_at": timestamp(),
        "train_per_class": args.train_per_class,
        "val_per_class": args.val_per_class,
        "classes": len(class_dirs),
        "totals": totals,
        "per_class": counts,
        "dataset_dir": str(DATASET_DIR),
    }
    save_json(manifest, EVALUATION_DIR / "dataset_manifest.json")
    print(f"[ok] manifest -> {EVALUATION_DIR / 'dataset_manifest.json'}")
    print("\nNext step:  python training/fine_tune.py --epochs 5 --batch-size 32 --lr 0.001")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
