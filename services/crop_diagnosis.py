"""
services/crop_diagnosis.py
==========================
Service managing crop leaf disease vision inference, symptom NLP classification,
Grad-CAM heatmaps, and explanation synthesis with Streamlit resource caching.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image
import streamlit as st

from modules import crop_doctor
from modules.symptom_model import predict_symptoms, symptom_model_status
from utils.caching import cached_resource
from utils.config import SAMPLE_IMAGES_DIR
from utils.gemini import fallback_diagnosis, generate_description, recommendation_for_image
from utils.image_processing import check_leaf_suitability, load_image_safely


@cached_resource
def get_cached_vision_model() -> Tuple[Any, List[str], Path]:
    """Cache the PyTorch MobileNetV2 model in memory across Streamlit reruns."""
    return crop_doctor.get_model(prefer_fine_tuned=True)


@cached_resource
def get_cached_symptom_status() -> Dict[str, Any]:
    """Check symptom classification model file status."""
    return symptom_model_status()


def get_available_sample_images() -> List[Dict[str, Any]]:
    """Return available sample leaf images for quick demonstration."""
    samples = []
    if SAMPLE_IMAGES_DIR.exists():
        for p in sorted(SAMPLE_IMAGES_DIR.glob("*.*")):
            if p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                label = p.stem.replace("sample_", "").replace("_", " ").title()
                samples.append({"name": label, "path": p, "filename": p.name})
    return samples


def run_crop_diagnosis(
    image: Optional[Image.Image] = None,
    symptom_text: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute full Crop Doctor diagnostic workflow:
    - Vision model inference on leaf image (if provided)
    - Symptom classification on farmer description (if provided)
    - Signal combination via min(confidence) and 0.70 threshold
    - AI or deterministic explanation synthesis
    - Actionable recommendations
    """
    image_result: Optional[Dict[str, Any]] = None
    leaf_warning: Optional[str] = None

    if image is not None:
        is_suitable, warning = check_leaf_suitability(image)
        if not is_suitable:
            leaf_warning = warning

        model, class_names, weights_path = get_cached_vision_model()
        image_result = crop_doctor.predict_from_image(
            image=image,
            model=model,
            class_names=class_names,
            weights_path=weights_path,
            top_k=3,
        )

    symptom_result: Optional[Dict[str, Any]] = None
    cleaned_symptoms = (symptom_text or "").strip()
    if cleaned_symptoms:
        symptom_result = predict_symptoms(cleaned_symptoms)

    combined = crop_doctor.combine_signals(image_result, symptom_result)

    # Explanation generation
    if combined.get("is_confident"):
        explanation = generate_description(image_result, symptom_result, cleaned_symptoms, combined)
    else:
        explanation = {
            "text": fallback_diagnosis(image_result, symptom_result, combined, cleaned_symptoms),
            "source": "offline-fallback",
            "used_ai": False,
            "model": None,
            "error": None,
            "prompt": None,
        }

    recommendations: List[str] = []
    if image_result and not image_result.get("error") and image_result.get("label"):
        rec = recommendation_for_image(image_result)
        if rec:
            recommendations.append(rec)
    if symptom_result and not symptom_result.get("error") and symptom_result.get("advice"):
        adv = symptom_result["advice"]
        if adv and adv not in recommendations:
            recommendations.append(adv)

    return {
        "image_result": image_result,
        "symptom_result": symptom_result,
        "combined": combined,
        "explanation": explanation,
        "recommendations": recommendations,
        "leaf_warning": leaf_warning,
    }


def generate_gradcam_explanation(
    image: Image.Image,
    target_label: Optional[str] = None,
    alpha: float = 0.45,
) -> Dict[str, Any]:
    """Generate Grad-CAM activation heatmap overlay for visual explainability."""
    try:
        from utils.gradcam import gradcam_overlay
        model, class_names, weights_path = get_cached_vision_model()
        tensor = crop_doctor.preprocess_image(image, device=crop_doctor.get_device())
        result = gradcam_overlay(
            model=model,
            input_tensor=tensor,
            class_names=class_names,
            target_label=target_label,
            alpha=alpha,
        )
        result["model_used"] = weights_path.name
        result["error"] = None
        return result
    except Exception as exc:
        return {"error": f"Grad-CAM generation failed: {type(exc).__name__}: {exc}"}
