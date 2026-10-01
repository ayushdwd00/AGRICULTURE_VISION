"""
utils/gradcam.py
================
Grad-CAM (Gradient-weighted Class Activation Mapping) for the AgriVision
MobileNetV2 plant-disease classifier.

Pipeline implemented here::

    Image
      |
      v
    Model (MobileNetV2)              <- forward pass, activations captured
      |
      v
    Target class (argmax or given)
      |
      v
    Activation maps                  <- gradients of the class score w.r.t.
      |                                 the last convolutional feature map
      v
    Grad-CAM heatmap
      |
      v
    Overlay on the original image    <- returned as PIL images for Streamlit

The implementation uses plain PyTorch hooks + ``torch.autograd.grad`` (no
external Grad-CAM package) so it works with any ``torchvision`` CNN whose
feature extractor is exposed as ``model.features``.
"""

from __future__ import annotations

from typing import Dict, Optional, Sequence, Tuple

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

from utils.helpers import IMAGENET_MEAN, IMAGENET_STD

__all__ = ["GradCAM", "gradcam_overlay", "denormalize_tensor"]

def denormalize_tensor(tensor: torch.Tensor) -> np.ndarray:
    """Undo ImageNet normalisation: ``(C,H,W)`` tensor -> RGB ``uint8`` array."""
    mean = torch.tensor(IMAGENET_MEAN).view(3, 1, 1)
    std = torch.tensor(IMAGENET_STD).view(3, 1, 1)
    image = (tensor.detach().cpu() * std + mean).clamp(0, 1)
    return (image.permute(1, 2, 0).numpy() * 255.0).astype(np.uint8)

class GradCAM:
    """
    Minimal, dependency-free Grad-CAM.

    Parameters
    ----------
    model:
        A ``torch.nn.Module`` used for inference (ideally ``.eval()``).
    target_layer:
        Convolutional layer to explain. Defaults to ``model.features[-1]``
        (the last feature block of MobileNetV2).
    """

    def __init__(
        self, model: torch.nn.Module, target_layer: Optional[torch.nn.Module] = None
    ):
        self.model = model
        self.target_layer = target_layer or self._default_target_layer()
        self.activations: Optional[torch.Tensor] = None
        self._handle = None

    def _default_target_layer(self) -> torch.nn.Module:
        features = getattr(self.model, "features", None)
        if features is None:
            raise ValueError(
                "Grad-CAM needs a model exposing 'features' (MobileNetV2/ResNet style)."
            )
        return features[-1]

    def _capture(self, _module, _inputs, output):  # forward hook
        self.activations = output

    def generate(
        self, input_tensor: torch.Tensor, target_index: Optional[int] = None
    ) -> Tuple[np.ndarray, int, float]:
        """
        Compute a Grad-CAM heat map.

        Parameters
        ----------
        input_tensor: ``(1, 3, H, W)`` normalised image batch.
        target_index: class to explain (``None`` -> predicted class).

        Returns
        -------
        ``(cam, predicted_index, confidence)`` where ``cam`` is a float32 array
        in ``[0, 1]`` with the spatial size of the input image.
        """
        self.model.eval()
        self.model.zero_grad(set_to_none=True)

        tensor = input_tensor.detach().clone().requires_grad_(True)
        self._handle = self.target_layer.register_forward_hook(self._capture)
        try:
            logits = self.model(tensor)
            probabilities = F.softmax(logits, dim=1)[0]
            predicted_index = int(probabilities.argmax().item())
            confidence = float(probabilities[predicted_index].item())
            index = predicted_index if target_index is None else int(target_index)

            activations = self.activations
            if activations is None:
                raise RuntimeError("Grad-CAM could not capture activations for this model.")
            gradients = torch.autograd.grad(
                outputs=logits[0, index], inputs=activations, retain_graph=False
            )[0]
        finally:
            if self._handle is not None:
                self._handle.remove()
                self._handle = None

        # Global-average-pool the gradients -> per-channel importance weights
        weights = gradients.mean(dim=(2, 3), keepdim=True)
        cam = F.relu((weights * activations).sum(dim=1))[0]
        cam = cam.detach().cpu().numpy()
        cam -= cam.min()
        peak = float(cam.max())
        cam = cam / peak if peak > 1e-8 else np.zeros_like(cam)

        height, width = tensor.shape[-2:]
        cam = cv2.resize(cam, (width, height), interpolation=cv2.INTER_LINEAR)
        return cam.astype(np.float32), predicted_index, confidence

    def overlay(
        self,
        input_tensor: torch.Tensor,
        target_index: Optional[int] = None,
        alpha: float = 0.45,
    ) -> Dict[str, object]:
        """
        Build a Grad-CAM overlay for a single image tensor.

        Returns ``cam`` (float map), ``heatmap``/``overlay``/``original``
        (RGB uint8 arrays), ``predicted_index`` and ``confidence``.
        """
        cam, predicted_index, confidence = self.generate(input_tensor, target_index)
        original = denormalize_tensor(input_tensor[0])
        heatmap_bgr = cv2.applyColorMap((cam * 255).astype(np.uint8), cv2.COLORMAP_JET)
        heatmap = cv2.cvtColor(heatmap_bgr, cv2.COLOR_BGR2RGB)
        overlay = cv2.addWeighted(original.astype(np.float32), 1.0 - alpha, heatmap.astype(np.float32), alpha, 0)
        return {
            "cam": cam,
            "heatmap": heatmap,
            "overlay": overlay.astype(np.uint8),
            "original": original,
            "predicted_index": predicted_index,
            "confidence": confidence,
            "alpha": alpha,
        }

def gradcam_overlay(
    model: torch.nn.Module,
    input_tensor: torch.Tensor,
    class_names: Optional[Sequence[str]] = None,
    target_label: Optional[str] = None,
    alpha: float = 0.45,
    target_layer: Optional[torch.nn.Module] = None,
) -> Dict[str, object]:
    """
    High level helper used by the Crop Doctor page.

    ``class_names`` / ``target_label`` are optional metadata used only to label
    the returned PIL images (``overlay_image``, ``heatmap_image``,
    ``original_image``).
    """
    index: Optional[int] = None
    names = list(class_names) if class_names else None
    if target_label and names and target_label in names:
        index = names.index(target_label)

    engine = GradCAM(model, target_layer=target_layer)
    result = engine.overlay(input_tensor, target_index=index, alpha=alpha)

    predicted = int(result["predicted_index"])  # type: ignore[arg-type]
    if names and predicted < len(names):
        label = names[predicted]
    else:
        label = f"class_{predicted}"

    result["label"] = label
    result["explained_label"] = target_label or label
    result["overlay_image"] = Image.fromarray(result["overlay"])  # type: ignore[arg-type]
    result["heatmap_image"] = Image.fromarray(result["heatmap"])  # type: ignore[arg-type]
    result["original_image"] = Image.fromarray(result["original"])  # type: ignore[arg-type]
    return result
