"""
modules/crop_doctor.py
======================
MODULE 1 (core AI module) - the image half of the AgriVision Crop Doctor.

Responsibilities
----------------
* Build the MobileNetV2 architecture used by the pretrained checkpoint
  (``Daksh159/plant-disease-mobilenetv2``) and by our fine-tuned model.
* Load ``models/agrivision_cnn.pth`` when available, otherwise fall back to the
  pretrained ``models/mobilenetv2_plant.pth`` (never crash).
* ``predict_image(image_bytes)`` -> ``{"label": ..., "confidence": ...}``
* Provide the crops/conditions/severity metadata used by the UI.
* Grad-CAM hook-up for the "Visual Explanation" panel.
* Combine the image prediction with the symptom classifier prediction using
  ``min(image_confidence, symptom_confidence)`` and a ``0.70`` threshold.

The module is Streamlit-free so the same code is reused by the scripts in
``training/``.
"""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms

from utils.helpers import (
    CLASS_NAMES_PATH,
    CONFIDENCE_THRESHOLD,
    FINE_TUNED_MODEL_PATH,
    IMAGE_SIZE,
    IMAGENET_MEAN,
    IMAGENET_STD,
    PRETRAINED_MODEL_PATH,
    UNCERTAIN_MESSAGE,
    confidence_band,
    disease_category,
    estimate_severity,
    is_healthy_label,
    load_class_names,
    load_image_from_bytes,
    pretty_label,
    split_label,
)

NUM_CLASSES: int = 38

# Human readable names for the two weight files AgriVision can use.
WEIGHTS_LABELS: Dict[str, str] = {
    "agrivision_cnn.pth": "Fine-tuned AgriVision model (agrivision_cnn.pth)",
    "mobilenetv2_plant.pth": "Pretrained MobileNetV2 (mobilenetv2_plant.pth)",
}

# Model construction / loading

def get_device() -> torch.device:
    """CUDA when available, otherwise CPU (this project is CPU friendly)."""
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")

def build_model(num_classes: int = NUM_CLASSES, imagenet_backbone: bool = False) -> nn.Module:
    """
    MobileNetV2 with the *same head layout* as the pretrained checkpoint.

    The published checkpoint stores ``classifier.1.1.weight/bias`` of shape
    ``(38, 1280)``, i.e. the head is::

        classifier = Sequential(Dropout(0.2), Sequential(Dropout(0.2), Linear(1280, 38)))

    Rebuilding it exactly like that lets us load the state dict strictly.
    """
    weights = models.MobileNet_V2_Weights.IMAGENET1K_V1 if imagenet_backbone else None
    model = models.mobilenet_v2(weights=weights)
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Sequential(nn.Dropout(0.2), nn.Linear(in_features, num_classes))
    return model

def extract_state_dict(checkpoint: Any) -> Dict[str, torch.Tensor]:
    """Accept a raw state dict or a wrapped checkpoint (``state_dict``/``model``)."""
    state_dict = checkpoint
    if isinstance(checkpoint, dict):
        for key in ("state_dict", "model_state_dict", "model", "net"):
            inner = checkpoint.get(key)
            if isinstance(inner, dict):
                state_dict = inner
                break
    if not isinstance(state_dict, dict):
        raise ValueError("Unsupported checkpoint format: expected a PyTorch state dict.")
    # Strip DataParallel / wrapper prefixes such as "module." or "model."
    cleaned: Dict[str, torch.Tensor] = {}
    for key, value in state_dict.items():
        new_key = key
        for prefix in ("module.", "model."):
            if new_key.startswith(prefix) and not new_key.startswith("model.features"):
                new_key = new_key[len(prefix):]
        cleaned[new_key] = value
    return cleaned

def load_checkpoint_into_model(model: nn.Module, weights_path: Path) -> nn.Module:
    """Load ``weights_path`` into ``model`` in a tolerant way."""
    checkpoint = torch.load(weights_path, map_location="cpu", weights_only=False)
    state_dict = extract_state_dict(checkpoint)
    missing, unexpected = model.load_state_dict(state_dict, strict=False)
    if missing:
        raise ValueError(
            f"{weights_path.name} does not match the AgriVision architecture "
            f"(missing {len(missing)} tensors, e.g. {missing[:3]})."
        )
    if unexpected:
        # Harmless extras (e.g. num_batches_tracked) are ignored, but report
        # genuine mismatches so problems are visible instead of silent.
        print(f"[crop_doctor] note: ignored {len(unexpected)} unexpected keys in {weights_path.name}")
    return model

def available_weights() -> Dict[str, Path]:
    """``{file_name: path}`` for every usable checkpoint in ``models/``."""
    found: Dict[str, Path] = {}
    for path in (FINE_TUNED_MODEL_PATH, PRETRAINED_MODEL_PATH):
        if path.exists():
            found[path.name] = path
    return found

def model_status() -> Dict[str, Any]:
    """Small status dictionary used by the Dashboard and by error messages."""
    weights = available_weights()
    fine_tuned = FINE_TUNED_MODEL_PATH.exists()
    return {
        "fine_tuned_available": fine_tuned,
        "pretrained_available": PRETRAINED_MODEL_PATH.exists(),
        "weights": {name: str(path) for name, path in weights.items()},
        "active": FINE_TUNED_MODEL_PATH.name if fine_tuned else (
            PRETRAINED_MODEL_PATH.name if PRETRAINED_MODEL_PATH.exists() else None
        ),
        "class_names_path": str(CLASS_NAMES_PATH),
        "num_classes": len(load_class_names()),
        "device": str(get_device()),
    }

# Pre-processing transforms

def preprocess_transform() -> transforms.Compose:
    """Inference transform - matches the transform used for the published model."""
    return transforms.Compose(
        [
            transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]
    )

def augment_transform() -> transforms.Compose:
    """Light augmentation for the fine-tuning *training* split."""
    return transforms.Compose(
        [
            transforms.RandomResizedCrop(IMAGE_SIZE, scale=(0.7, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(15),
            transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.15),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]
    )

def preprocess_image(
    image: "Image.Image | Any", device: Optional[torch.device] = None
) -> torch.Tensor:
    """PIL image -> ``(1, 3, 224, 224)`` normalised tensor on the chosen device."""
    device = device or get_device()
    if not isinstance(image, Image.Image):
        image = Image.fromarray(image).convert("RGB")
    return preprocess_transform()(image.convert("RGB")).unsqueeze(0).to(device)

# Cached model access

@functools.lru_cache(maxsize=4)
def load_model(weights_path: str, device_name: str = "cpu") -> nn.Module:
    """
    Load (and cache) a checkpoint. Parameters get ``requires_grad = False`` -
    AgriVision only performs inference here; gradients are still available for
    Grad-CAM because the *input* tensor carries the graph.
    """
    model = build_model(NUM_CLASSES)
    load_checkpoint_into_model(model, Path(weights_path))
    device = torch.device(device_name)
    model.to(device)
    model.eval()
    for parameter in model.parameters():
        parameter.requires_grad = False
    return model

def get_model(
    prefer_fine_tuned: bool = True, weights_name: Optional[str] = None
) -> Tuple[nn.Module, List[str], Path]:
    """
    Return ``(model, class_names, weights_path)``.

    Preference order: ``models/agrivision_cnn.pth`` (fine-tuned) and then
    ``models/mobilenetv2_plant.pth`` (pretrained baseline). Raises
    ``FileNotFoundError`` only when *no* checkpoint exists - the Streamlit layer
    turns that into a friendly message.
    """
    weights = available_weights()
    if not weights:
        raise FileNotFoundError(
            "No model file found in 'models/'. Run: python training/download_model.py"
        )

    if weights_name is None:
        if prefer_fine_tuned and FINE_TUNED_MODEL_PATH.name in weights:
            weights_name = FINE_TUNED_MODEL_PATH.name
        elif PRETRAINED_MODEL_PATH.name in weights:
            weights_name = PRETRAINED_MODEL_PATH.name
        else:
            weights_name = next(iter(weights))

    weights_path = weights[weights_name]
    device = get_device()
    model = load_model(str(weights_path.resolve()), str(device))
    return model, load_class_names(), weights_path

def current_model_label(weights_path: Optional[Path]) -> str:
    """Human readable description of the active checkpoint."""
    if weights_path is None:
        return "No model loaded"
    return WEIGHTS_LABELS.get(
        weights_path.name, f"Custom checkpoint ({weights_path.name})"
    )

def build_image_folder_dataset(
    directory: "Path | str",
    class_names: List[str],
    transform: Optional[Any] = None,
) -> Any:
    """
    Build a ``torchvision.datasets.ImageFolder`` whose labels are remapped into
    the **global 38-class index space**.

    The fine-tuning subset only contains 15 of the 38 classes; a plain
    ImageFolder would relabel them 0..14, which would silently train the head
    against the wrong outputs.  The ``target_transform`` below maps every local
    folder index onto its position in ``models/class_names.json``, so the model
    keeps its original 38-way output structure and the fine-tuned and pretrained
    checkpoints stay interchangeable.

    Used by ``training/fine_tune.py`` and ``training/evaluate.py``.
    """
    from torchvision.datasets import ImageFolder

    from utils.helpers import canonical_from_dataset_folder

    dataset = ImageFolder(str(directory), transform=transform)
    mapping: Dict[str, int] = {}
    unmapped: List[str] = []
    for local_index, folder_name in enumerate(dataset.classes):
        canonical = canonical_from_dataset_folder(folder_name)
        if canonical and canonical in class_names:
            mapping[folder_name] = class_names.index(canonical)
        else:
            unmapped.append(folder_name)

    if unmapped:
        raise ValueError(
            f"{directory}: these folders do not map to a known AgriVision class: {unmapped}"
        )
    if not mapping:
        raise ValueError(f"{directory}: no class folders were found.")

    dataset.target_transform = lambda local_index, _mapping=mapping, _classes=dataset.classes: (
        _mapping[_classes[local_index]]
    )
    dataset.class_mapping = mapping  # type: ignore[attr-defined]
    return dataset

# Inference

def _empty_result(error: str) -> Dict[str, Any]:
    """Uniform error payload so the UI never has to special-case ``None``."""
    return {
        "label": None,
        "confidence": 0.0,
        "pretty_label": None,
        "crop": None,
        "condition": None,
        "is_healthy": None,
        "category": None,
        "severity": None,
        "confidence_band": "Unknown",
        "top_predictions": [],
        "model_used": None,
        "model_label": None,
        "device": str(get_device()),
        "is_uncertain": True,
        "error": error,
    }

def _pack_result(
    probabilities: torch.Tensor,
    class_names: List[str],
    weights_path: Optional[Path],
    top_k: int,
) -> Dict[str, Any]:
    """Turn a probability vector into the dictionary returned by ``predict_image``."""
    top_confidences, top_indices = torch.topk(
        probabilities, k=min(top_k, probabilities.numel())
    )
    top_predictions = [
        {
            "label": class_names[index] if index < len(class_names) else f"class_{index}",
            "confidence": float(score),
            "pretty_label": pretty_label(class_names[index])
            if index < len(class_names)
            else f"class_{index}",
        }
        for index, score in zip(top_indices.tolist(), top_confidences.tolist())
    ]

    best = top_predictions[0]
    label = best["label"]
    confidence = float(best["confidence"])
    crop, condition = split_label(label)
    return {
        "label": label,
        "confidence": confidence,
        "pretty_label": best["pretty_label"],
        "crop": crop,
        "condition": condition,
        "is_healthy": is_healthy_label(label),
        "category": disease_category(label),
        "severity": estimate_severity(label, confidence),
        "confidence_band": confidence_band(confidence),
        "top_predictions": top_predictions,
        "model_used": weights_path.name if weights_path else None,
        "model_label": current_model_label(weights_path),
        "device": str(get_device()),
        "is_uncertain": confidence < CONFIDENCE_THRESHOLD,
        "error": None,
    }

def predict_from_image(
    image: Image.Image,
    model: Optional[nn.Module] = None,
    class_names: Optional[List[str]] = None,
    weights_path: Optional[Path] = None,
    weights_name: Optional[str] = None,
    top_k: int = 3,
) -> Dict[str, Any]:
    """
    Run the vision model on a PIL image.

    Never raises: configuration / inference problems are reported through the
    ``"error"`` key of the returned dictionary.
    """
    try:
        if model is None or class_names is None or weights_path is None:
            model, class_names, weights_path = get_model(weights_name=weights_name)
        device = get_device()
        tensor = preprocess_image(image, device=device)
        with torch.no_grad():
            logits = model(tensor)
            probabilities = torch.softmax(logits, dim=1)[0].cpu()
        return _pack_result(probabilities, list(class_names), weights_path, top_k)
    except FileNotFoundError as exc:
        return _empty_result(str(exc))
    except ValueError as exc:
        return _empty_result(f"Model / image problem: {exc}")
    except Exception as exc:  # pragma: no cover - defensive: never crash the app
        return _empty_result(f"Inference failed: {type(exc).__name__}: {exc}")

def predict_image(
    image_bytes: bytes, top_k: int = 3, weights_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Public API required by the project brief.

    Parameters
    ----------
    image_bytes:
        Raw bytes of the uploaded crop photo.
    top_k:
        How many candidate classes to return.
    weights_name:
        Force a specific checkpoint (defaults to the fine-tuned model).

    Returns
    -------
    ``{"label": "...", "confidence": 0.0, ...}`` plus extra UI metadata.
    """
    try:
        image = load_image_from_bytes(image_bytes)
    except ValueError as exc:
        return _empty_result(str(exc))
    return predict_from_image(image, weights_name=weights_name, top_k=top_k)

def predict_probabilities(
    image: Image.Image, weights_name: Optional[str] = None
) -> Tuple[torch.Tensor, nn.Module, List[str], Path]:
    """``(probabilities, model, class_names, weights_path)`` - used by Grad-CAM."""
    model, class_names, weights_path = get_model(weights_name=weights_name)
    tensor = preprocess_image(image, device=get_device())
    with torch.no_grad():
        logits = model(tensor)
        probabilities = torch.softmax(logits, dim=1)[0].cpu()
    return probabilities, model, class_names, weights_path

def gradcam_for_image(
    image: "Image.Image | Any",
    target_label: Optional[str] = None,
    weights_name: Optional[str] = None,
    alpha: float = 0.45,
) -> Dict[str, Any]:
    """
    Grad-CAM explanation for a crop image.

    Returns the :func:`utils.gradcam.gradcam_overlay` dictionary (with
    ``overlay_image``, ``heatmap_image`` and ``original_image`` PIL images) or
    ``{"error": "..."}`` when the explanation cannot be produced.
    """
    try:
        from utils.gradcam import gradcam_overlay

        model, class_names, weights_path = get_model(weights_name=weights_name)
        tensor = preprocess_image(image, device=get_device())
        result = gradcam_overlay(
            model,
            tensor,
            class_names=class_names,
            target_label=target_label,
            alpha=alpha,
        )
        result["model_used"] = weights_path.name
        result["error"] = None
        return result
    except Exception as exc:  # pragma: no cover - defensive
        return {"error": f"Grad-CAM failed: {type(exc).__name__}: {exc}"}

# Crop Doctor confidence logic (image + symptom fusion)

#: ``min(image_confidence, symptom_confidence)`` must reach this value before
#: the AI explanation is generated (project brief, section 10).
THRESHOLD: float = CONFIDENCE_THRESHOLD

_SEVERITY_RANK: Dict[str, int] = {
    "None (healthy)": 0,
    "Mild": 1,
    "Moderate": 2,
    "Severe": 3,
}
_RANK_TO_SEVERITY: Dict[int, str] = {value: key for key, value in _SEVERITY_RANK.items()}

#: Which symptom families are *compatible* with each image-model category.
#: Used to detect "the two models disagree" situations, which the Gemini
#: explanation then reports as two possibilities instead of false certainty.
IMAGE_TO_SYMPTOM_COMPATIBILITY: Dict[str, set] = {
    "healthy": {"healthy", "nutrient", "water", "environment", "unknown"},
    "fungal": {"fungal", "water", "nutrient", "unknown"},
    "bacterial": {"bacterial", "fungal", "nutrient", "unknown"},
    "viral": {"viral", "pest", "nutrient", "unknown"},
    "pest": {"pest", "viral", "nutrient", "unknown"},
    "unknown": {
        "healthy", "nutrient", "fungal", "bacterial", "viral", "pest",
        "water", "environment", "unknown",
    },
}

def signals_agree(
    image_result: Optional[Dict[str, Any]], symptom_result: Optional[Dict[str, Any]]
) -> bool:
    """True when the image model and the symptom classifier are compatible."""
    if not image_result or not symptom_result:
        return True
    if image_result.get("error") or symptom_result.get("error"):
        return True
    family = str(symptom_result.get("family") or "unknown").lower()
    category = str(image_result.get("category") or "unknown").lower()
    if family == "unknown":
        return True
    allowed = IMAGE_TO_SYMPTOM_COMPATIBILITY.get(
        category, IMAGE_TO_SYMPTOM_COMPATIBILITY["unknown"]
    )
    return family in allowed

def _disagreement_note(
    image_result: Dict[str, Any], symptom_result: Dict[str, Any]
) -> str:
    """Explain a disagreement in one farmer friendly sentence."""
    image_text = image_result.get("pretty_label") or "an unclear image result"
    symptom_text = symptom_result.get("pretty_label") or "your description"
    return (
        f"The photo model suggests {image_text}, while the symptom analysis suggests "
        f"{symptom_text}. Both possibilities are reported because the image and the "
        "described symptoms point in different directions."
    )

def combine_signals(
    image_result: Optional[Dict[str, Any]] = None,
    symptom_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Fuse the two model outputs using ``min(confidences)`` and the 0.70 threshold.

    Exactly as required by the brief:

    * ``combined_confidence >= 0.70`` -> an AI explanation is generated.
    * ``combined_confidence <  0.70`` -> the "prediction uncertain" message is
      shown and the user is asked for a clearer image / description or to
      consult an agricultural expert.
    """
    confidences: List[float] = []
    if image_result and not image_result.get("error") and image_result.get("label"):
        confidences.append(float(image_result.get("confidence") or 0.0))
    if symptom_result and not symptom_result.get("error") and symptom_result.get("label"):
        confidences.append(float(symptom_result.get("confidence") or 0.0))

    combined = min(confidences) if confidences else 0.0
    is_confident = bool(confidences) and combined >= THRESHOLD

    agreed = signals_agree(image_result, symptom_result)
    note = None
    if not agreed and image_result and symptom_result:
        note = _disagreement_note(image_result, symptom_result)

    # Overall severity = the worst of the available severity hints.
    severity_rank = 0
    for result in (image_result, symptom_result):
        if result and result.get("severity"):
            severity_rank = max(severity_rank, _SEVERITY_RANK.get(str(result["severity"]), 0))

    return {
        "combined_confidence": combined,
        "is_confident": is_confident,
        "threshold": THRESHOLD,
        "confidence_band": confidence_band(combined),
        "message": None if is_confident else UNCERTAIN_MESSAGE,
        "agreement": agreed,
        "disagreement_note": note,
        "severity": _RANK_TO_SEVERITY.get(severity_rank, "Moderate"),
        "signals_used": len(confidences),
        "image_confidence": image_result.get("confidence") if image_result else None,
        "symptom_confidence": symptom_result.get("confidence") if symptom_result else None,
    }
