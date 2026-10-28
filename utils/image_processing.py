"""
utils/image_processing.py
=========================
Image validation, EXIF normalization, resizing and leaf heuristics.
"""

from __future__ import annotations

import io
from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

from utils.helpers import is_probably_leaf_image

MAX_IMAGE_PIXELS = 40_000_000


def load_image_safely(data: bytes | io.BytesIO | Image.Image) -> Tuple[Optional[Image.Image], Optional[str]]:
    """
    Load an image safely from bytes or file buffer.
    Applies EXIF orientation normalization and ensures RGB mode.
    """
    if isinstance(data, Image.Image):
        try:
            if data.width * data.height > MAX_IMAGE_PIXELS:
                return None, "This image is too large to process. Please upload a smaller photo."
            img = ImageOps.exif_transpose(data)
            return img.convert("RGB"), None
        except Exception as exc:
            return None, f"Failed to process image: {exc}"

    try:
        if isinstance(data, (bytes, bytearray)):
            stream = io.BytesIO(data)
        else:
            stream = data
        image = Image.open(stream)
        if image.width * image.height > MAX_IMAGE_PIXELS:
            return None, "This image is too large to process. Please upload a smaller photo."
        image.load()
        try:
            image = ImageOps.exif_transpose(image)
        except Exception:
            pass
        return image.convert("RGB"), None
    except UnidentifiedImageError:
        return None, "The uploaded file could not be decoded as an image. Please use a valid JPEG, PNG, or WebP photo."
    except Exception as exc:
        return None, f"Failed to process image: {exc}"


def resize_thumbnail(image: Image.Image, max_dim: int = 800) -> Image.Image:
    """Create a high-quality thumbnail preserving aspect ratio for display."""
    if max(image.size) <= max_dim:
        return image
    ratio = max_dim / max(image.size)
    new_size = (int(image.width * ratio), int(image.height * ratio))
    return image.resize(new_size, Image.Resampling.LANCZOS)


def assess_image_quality(image: Image.Image) -> Dict[str, object]:
    """Report simple, non-diagnostic photo limitations without rejecting the image."""
    issues: List[str] = []
    if min(image.size) < 96:
        issues.append("The image is small, so fine details may be hard to assess.")

    sample = resize_thumbnail(image.convert("RGB"), max_dim=256)
    grayscale = cv2.cvtColor(np.asarray(sample), cv2.COLOR_RGB2GRAY)
    mean_brightness = float(np.mean(grayscale))
    if mean_brightness < 35:
        issues.append("The photo is quite dark; brighter, even lighting may help.")
    elif mean_brightness > 235:
        issues.append("The photo is very bright; softer lighting may show more detail.")

    detail_score = float(cv2.Laplacian(grayscale, cv2.CV_64F).var())
    if detail_score < 8:
        issues.append("The photo has little fine detail; move closer and tap to focus.")

    return {
        "width": image.width,
        "height": image.height,
        "issues": issues,
        "is_suitable": not issues,
    }


def image_to_base64_png(image: Image.Image) -> str:
    """Encode PIL image to base64 string for embedding."""
    import base64
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def check_leaf_suitability(image: Image.Image) -> Tuple[bool, Optional[str]]:
    """Check if image contains adequate foliage characteristics for diagnosis."""
    if is_probably_leaf_image(image):
        return True, None
    return False, "This image may have low leaf/foliage visibility. For the highest diagnostic accuracy, use a clear, close-up photo of the affected plant leaf."
