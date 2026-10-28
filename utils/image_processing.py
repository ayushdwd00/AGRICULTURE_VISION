"""
utils/image_processing.py
=========================
Image validation, EXIF normalization, resizing and leaf heuristics.
"""

from __future__ import annotations

import io
from typing import Optional, Tuple
from PIL import Image, ImageOps, UnidentifiedImageError

from utils.helpers import is_probably_leaf_image


def load_image_safely(data: bytes | io.BytesIO | Image.Image) -> Tuple[Optional[Image.Image], Optional[str]]:
    """
    Load an image safely from bytes or file buffer.
    Applies EXIF orientation normalization and ensures RGB mode.
    """
    if isinstance(data, Image.Image):
        try:
            img = ImageOps.exif_transpose(data)
            return img.convert("RGB"), None
        except Exception:
            return data.convert("RGB"), None

    try:
        if isinstance(data, (bytes, bytearray)):
            stream = io.BytesIO(data)
        else:
            stream = data
        image = Image.open(stream)
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
