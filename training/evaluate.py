"""
training/evaluate.py
====================
Evaluates the **pretrained** and the **fine-tuned** AgriVision model on the same
validation split and writes a full before/after report:

* accuracy and loss for both checkpoints
* per-class classification report (precision / recall / F1)
* confusion matrix heat map (``figsize=(20, 20)``, as required by the brief)
* accuracy / loss comparison bar chart

Everything is written to ``data/evaluation/``::

    evaluation_summary.json
    evaluation_before_after.txt
    classification_report_before.txt
    classification_report_after.txt
    confusion_matrix_before.png
    confusion_matrix_after.png
    metrics_comparison.png

Class-index note
----------------
The validation subset only contains 15 of the 38 PlantVillage classes, so by
default the confusion matrix is drawn for the classes that actually have
samples (with the same 20x20 inch figure).  Pass ``--full-matrix`` to force the
complete 38x38 layout.

Usage
-----
    python training/evaluate.py
    python training/evaluate.py --dataset data/dataset --full-matrix
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib  # noqa: E402

matplotlib.use("Agg")  # headless: no GUI needed when running from the terminal

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import seaborn as sns  # noqa: E402
import torch  # noqa: E402
import torch.nn as nn  # noqa: E402
from sklearn.metrics import (  # noqa: E402
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from torch.utils.data import DataLoader  # noqa: E402

from modules.crop_doctor import (  # noqa: E402
    NUM_CLASSES,
    build_image_folder_dataset,
    build_model,
    get_device,
    load_checkpoint_into_model,
    preprocess_transform,
)
from utils.helpers import (  # noqa: E402
    DATASET_DIR,
    EVALUATION_DIR,
    FINE_TUNED_MODEL_PATH,
    PRETRAINED_MODEL_PATH,
    ensure_directories,
    load_class_names,
    pretty_label,
    save_json,
    seed_everything,
    timestamp,
)

# Core evaluation

def build_val_loader(
    dataset_dir: Path, class_names: List[str], batch_size: int = 32
) -> Tuple[DataLoader, List[str], Dict[str, int]]:
    """Validation loader with global class indices + its folder mapping."""
    val_dir = Path(dataset_dir) / "val"
    if not val_dir.exists():
        raise SystemExit(
            f"{val_dir} does not exist. Run: python training/download_dataset.py"
        )
    dataset = build_image_folder_dataset(val_dir, class_names, transform=preprocess_transform())
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
    return loader, list(dataset.classes), dict(getattr(dataset, "class_mapping", {}))

@torch.no_grad()
def collect_predictions(
    weights_path: Path, loader: DataLoader, class_names: List[str]
) -> Dict[str, Any]:
    """Run one checkpoint over the validation split and collect everything we plot."""
    device = get_device()
    model = build_model(NUM_CLASSES)
    load_checkpoint_into_model(model, Path(weights_path))
    model.to(device)
    model.eval()

    criterion = nn.CrossEntropyLoss(reduction="sum")
    targets_all: List[int] = []
    predictions_all: List[int] = []
    confidences_all: List[float] = []
    total_loss = 0.0
    total = 0

    for images, targets in loader:
        images = images.to(device)
        targets = targets.to(device)
        logits = model(images)
        total_loss += float(criterion(logits, targets).item())
        probabilities = torch.softmax(logits, dim=1)
        confidence, predicted = probabilities.max(dim=1)
        targets_all.extend(targets.cpu().tolist())
        predictions_all.extend(predicted.cpu().tolist())
        confidences_all.extend(confidence.cpu().tolist())
        total += targets.size(0)

    y_true = np.array(targets_all)
    y_pred = np.array(predictions_all)
    return {
        "weights": Path(weights_path).name,
        "accuracy": float(accuracy_score(y_true, y_pred)) if total else 0.0,
        "loss": (total_loss / total) if total else float("nan"),
        "images": total,
        "mean_confidence": float(np.mean(confidences_all)) if confidences_all else 0.0,
        "y_true": y_true,
        "y_pred": y_pred,
    }

def present_class_indices(y_true: np.ndarray, y_pred: np.ndarray) -> List[int]:
    """Global class indices that actually occur in the validation split."""
    return sorted(set(y_true.tolist()) | set(y_pred.tolist()))

def plot_confusion_matrix(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    class_names: Sequence[str],
    out_path: Path,
    title: str,
    full_matrix: bool = False,
) -> List[int]:
    """Seaborn heat map with ``figsize=(20, 20)`` (38-class layout when full)."""
    indices = list(range(len(class_names))) if full_matrix else present_class_indices(y_true, y_pred)
    labels = [pretty_label(class_names[index]) for index in indices]
    matrix = confusion_matrix(y_true, y_pred, labels=indices)

    figure, axes = plt.subplots(figsize=(20, 20))
    sns.heatmap(
        matrix,
        annot=len(indices) <= 20,
        fmt="d",
        cmap="YlGnBu",
        xticklabels=labels,
        yticklabels=labels,
        square=True,
        linewidths=0.4,
        cbar_kws={"shrink": 0.7},
        ax=axes,
    )
    axes.set_title(f"{title}\n(validation images: {len(y_true)})", fontsize=16, pad=16)
    axes.set_xlabel("Predicted class", fontsize=13)
    axes.set_ylabel("True class", fontsize=13)
    plt.setp(axes.get_xticklabels(), rotation=90, fontsize=8)
    plt.setp(axes.get_yticklabels(), rotation=0, fontsize=8)
    figure.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(out_path, dpi=110)
    plt.close(figure)
    return indices

def write_classification_report(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    class_names: Sequence[str],
    indices: Sequence[int],
    out_path: Path,
) -> str:
    """Per-class precision/recall/F1 for the classes present in the split."""
    labels = [class_names[index] for index in indices]
    report = classification_report(
        y_true,
        y_pred,
        labels=list(indices),
        target_names=[pretty_label(label) for label in labels],
        zero_division=0,
        digits=3,
    )
    out_path.write_text(report, encoding="utf-8")
    return report

def plot_metric_comparison(summary: Dict[str, Any], out_path: Path) -> None:
    """Side-by-side accuracy / loss bars for the before vs after comparison."""
    stages = ["before (pretrained)", "after (fine-tuned)"]
    before = summary["before"]
    after = summary.get("after")
    if after is None:
        return

    accuracy = [before["accuracy"] * 100, after["accuracy"] * 100]
    losses = [before["loss"], after["loss"]]

    figure, axes = plt.subplots(1, 2, figsize=(13, 5))
    colors = ["#7f8c8d", "#27ae60"]

    bars = axes[0].bar(stages, accuracy, color=colors, width=0.55)
    axes[0].set_title("Validation accuracy (higher is better)", fontsize=13)
    axes[0].set_ylabel("Accuracy (%)")
    axes[0].set_ylim(0, 105)
    for bar, value in zip(bars, accuracy):
        axes[0].text(bar.get_x() + bar.get_width() / 2, value + 1.5, f"{value:.2f}%",
                     ha="center", fontsize=11)

    bars = axes[1].bar(stages, losses, color=colors, width=0.55)
    axes[1].set_title("Validation loss (lower is better)", fontsize=13)
    axes[1].set_ylabel("Cross-entropy loss")
    top = max(losses) * 1.25 if max(losses) > 0 else 1.0
    axes[1].set_ylim(0, top)
    for bar, value in zip(bars, losses):
        axes[1].text(bar.get_x() + bar.get_width() / 2, value + top * 0.02, f"{value:.4f}",
                     ha="center", fontsize=11)

    figure.suptitle(
        f"AgriVision - effect of fine-tuning on {summary['val_images']} validation images",
        fontsize=14,
    )
    figure.tight_layout(rect=(0, 0, 1, 0.95))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(out_path, dpi=130)
    plt.close(figure)

def format_comparison_table(summary: Dict[str, Any]) -> str:
    """Plain-text before/after table used in the console output and the report."""
    before = summary["before"]
    after = summary.get("after")
    lines = [
        "=" * 78,
        " AgriVision - Phase 1 model evaluation (before vs after fine-tuning)",
        "=" * 78,
        f" validation images          : {summary['val_images']}",
        f" classes in validation split : {summary['val_classes']}",
        f" device                      : {summary['device']}",
        "",
        f" {'metric':<26}{'before (pretrained)':>22}{'after (fine-tuned)':>22}{'change':>14}",
        " " + "-" * 76,
    ]
    if after is None:
        lines.append(f" {'accuracy':<26}{before['accuracy'] * 100:>21.2f}%{'n/a':>22}{'n/a':>14}")
        lines.append(f" {'loss':<26}{before['loss']:>22.4f}{'n/a':>22}{'n/a':>14}")
    else:
        accuracy_delta = (after["accuracy"] - before["accuracy"]) * 100
        loss_delta = after["loss"] - before["loss"]
        lines.append(
            f" {'accuracy':<26}{before['accuracy'] * 100:>21.2f}%"
            f"{after['accuracy'] * 100:>21.2f}%{accuracy_delta:>+13.2f}%"
        )
        lines.append(
            f" {'loss':<26}{before['loss']:>22.4f}{after['loss']:>22.4f}{loss_delta:>+14.4f}"
        )
        lines.append(
            f" {'mean confidence':<26}{before['mean_confidence'] * 100:>21.2f}%"
            f"{after['mean_confidence'] * 100:>21.2f}%"
            f"{(after['mean_confidence'] - before['mean_confidence']) * 100:>+13.2f}%"
        )
    lines.append("=" * 78)
    return "\n".join(lines)

def evaluate_checkpoint(
    weights_path: Path,
    loader: DataLoader,
    class_names: List[str],
    tag: str,
    full_matrix: bool,
) -> Dict[str, Any]:
    """Full evaluation of one checkpoint: metrics, report and plots."""
    print(f"\n[evaluate] {tag}: {Path(weights_path).name}")
    result = collect_predictions(Path(weights_path), loader, class_names)
    print(
        f"           accuracy={result['accuracy'] * 100:.2f}%  "
        f"loss={result['loss']:.4f}  images={result['images']}  "
        f"mean_confidence={result['mean_confidence'] * 100:.2f}%"
    )

    indices = plot_confusion_matrix(
        result["y_true"],
        result["y_pred"],
        class_names,
        EVALUATION_DIR / f"confusion_matrix_{tag}.png",
        title=f"AgriVision confusion matrix - {tag} ({Path(weights_path).name})",
        full_matrix=full_matrix,
    )
    report = write_classification_report(
        result["y_true"],
        result["y_pred"],
        class_names,
        indices,
        EVALUATION_DIR / f"classification_report_{tag}.txt",
    )
    result["report"] = report
    result["classes_evaluated"] = [class_names[index] for index in indices]
    result["confusion_matrix_size"] = len(indices)
    result.pop("y_true")
    result.pop("y_pred")
    return result

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate the pretrained and fine-tuned AgriVision checkpoints."
    )
    parser.add_argument("--dataset", default=str(DATASET_DIR), help="dataset root (train/ val/)")
    parser.add_argument("--pretrained", default=str(PRETRAINED_MODEL_PATH))
    parser.add_argument("--fine-tuned", default=str(FINE_TUNED_MODEL_PATH))
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument(
        "--full-matrix", action="store_true",
        help="draw the full 38x38 confusion matrix instead of the classes present in the split",
    )
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    seed_everything(args.seed)
    ensure_directories()
    sns.set_theme(style="whitegrid")
    class_names = load_class_names()
    loader, folder_classes, _mapping = build_val_loader(
        Path(args.dataset), class_names, args.batch_size
    )

    print("=" * 78)
    print(" AgriVision evaluation - pretrained vs fine-tuned")
    print("=" * 78)
    print(f" validation split : {Path(args.dataset) / 'val'}")
    print(f" local classes    : {len(folder_classes)} -> mapped into {len(class_names)} global classes")
    print(f" images           : {len(loader.dataset)}")
    print(f" device           : {get_device()}")

    if not Path(args.pretrained).exists():
        raise SystemExit(
            f"Pretrained checkpoint not found: {args.pretrained}\n"
            "Run: python training/download_model.py"
        )

    before = evaluate_checkpoint(
        Path(args.pretrained), loader, class_names, tag="before", full_matrix=args.full_matrix
    )

    after = None
    if Path(args.fine_tuned).exists():
        after = evaluate_checkpoint(
            Path(args.fine_tuned), loader, class_names, tag="after", full_matrix=args.full_matrix
        )
    else:
        print(
            f"\n[warn] fine-tuned checkpoint not found ({args.fine_tuned}).\n"
            "       Run: python training/fine_tune.py --epochs 5 --batch-size 32 --lr 0.001\n"
            "       Only the 'before' evaluation is written for now."
        )

    summary = {
        "created_at": timestamp(),
        "dataset_dir": str(args.dataset),
        "val_images": len(loader.dataset),
        "val_classes": len(folder_classes),
        "device": str(get_device()),
        "full_matrix": bool(args.full_matrix),
        "before": before,
        "after": after,
        "fine_tuned_available": after is not None,
    }
    if after is not None:
        summary["accuracy_delta"] = after["accuracy"] - before["accuracy"]
        summary["loss_delta"] = after["loss"] - before["loss"]
        plot_metric_comparison(summary, EVALUATION_DIR / "metrics_comparison.png")

    save_json(summary, EVALUATION_DIR / "evaluation_summary.json")

    table = format_comparison_table(summary)
    print("\n" + table)
    (EVALUATION_DIR / "evaluation_before_after.txt").write_text(table + "\n", encoding="utf-8")

    print(f"\n[ok] summary              -> {EVALUATION_DIR / 'evaluation_summary.json'}")
    print(f"[ok] comparison table     -> {EVALUATION_DIR / 'evaluation_before_after.txt'}")
    print(f"[ok] confusion matrices   -> confusion_matrix_before.png / confusion_matrix_after.png")
    print(f"[ok] classification report-> classification_report_before.txt / _after.txt")
    if after is not None:
        print(f"[ok] metrics comparison   -> {EVALUATION_DIR / 'metrics_comparison.png'}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
