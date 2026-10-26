"""
========================================================================================
VisionCare AI: Module 5A — Grad-CAM++ & Lesion Bounding Box Engine
========================================================================================
Purpose: Generates high-resolution Grad-CAM++ visual attribution heatmaps and
         extracts localized bounding boxes with metric physical dimensions (cm).
Technical Safeguard: Attaches hooks directly to the activation tensor, bypassing
                     PyTorch in-place ReLU autograd conflicts.
========================================================================================
"""

from typing import Dict, Any, Tuple, Union, Optional, List
import numpy as np
import cv2
from PIL import Image

import torch
import torch.nn as nn
import torch.nn.functional as F

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD  = [0.229, 0.224, 0.225]


class GradCAMPlusPlusEngine:
    """
    Grad-CAM++ Explainability Engine for DenseNet-121.
    Computes higher-order weighted feature attribution maps for individual pathologies.
    """

    def __init__(self, model: nn.Module, target_layer: Optional[nn.Module] = None):
        self.model = model
        self.model.eval()

        # Default to final normalization layer of DenseNet features
        if target_layer is None:
            if hasattr(model, "features") and hasattr(model.features, "norm5"):
                self.target_layer = model.features.norm5
            elif hasattr(model, "features"):
                self.target_layer = list(model.features.children())[-1]
            else:
                self.target_layer = list(model.children())[0]
        else:
            self.target_layer = target_layer

        self.gradients = None
        self.activations = None

        # Reset hooks
        self.target_layer._forward_hooks.clear()
        self.target_layer._backward_hooks.clear()
        self.target_layer._is_full_backward_hook = None

        # Register forward hook (which dynamically hooks the activation tensor)
        self.target_layer.register_forward_hook(self._forward_hook)

    def _forward_hook(self, module, input, output):
        self.activations = output
        # Hook directly onto the activation tensor only if gradients are required
        if output.requires_grad:
            output.register_hook(self._save_gradient)

    def _save_gradient(self, grad):
        self.gradients = grad

    def generate_heatmap(
        self,
        input_tensor: torch.Tensor,
        class_idx: int,
        target_size: Tuple[int, int] = (1024, 1024)
    ) -> np.ndarray:
        """
        Computes Grad-CAM++ continuous activation map resized to target_size.
        Returns: Normalized float32 heatmap (0.0 to 1.0).
        """
        self.model.zero_grad()

        output = self.model(input_tensor)
        target_score = output[0, class_idx]
        target_score.backward(retain_graph=True)

        if self.gradients is None or self.activations is None:
            return np.zeros(target_size, dtype=np.float32)

        grads = self.gradients[0].detach()   # [C, H, W]
        acts = self.activations[0].detach()  # [C, H, W]

        # Grad-CAM++ second & third order weighting formulation
        grads_power_2 = grads.pow(2)
        grads_power_3 = grads_power_2 * grads
        sum_acts = acts.sum(dim=(1, 2), keepdim=True)

        eps = 1e-7
        aij = grads_power_2 / (2 * grads_power_2 + sum_acts * grads_power_3 + eps)
        aij = torch.where(grads != 0, aij, torch.zeros_like(aij))

        weights = (aij * F.relu(grads)).sum(dim=(1, 2), keepdim=True)
        cam = (weights * acts).sum(dim=0)
        cam = F.relu(cam)

        cam_np = cam.cpu().numpy()
        cam_min, cam_max = cam_np.min(), cam_np.max()

        if cam_max > cam_min:
            cam_np = (cam_np - cam_min) / (cam_max - cam_min)
        else:
            cam_np = np.zeros_like(cam_np)

        # Upsample to full diagnostic resolution (e.g. 1024x1024)
        heatmap_resized = cv2.resize(cam_np, target_size, interpolation=cv2.INTER_CUBIC)
        return np.clip(heatmap_resized, 0.0, 1.0)

    def extract_bounding_boxes(
        self,
        heatmap: np.ndarray,
        threshold_percentile: float = 75.0,
        pixel_spacing: Optional[Tuple[float, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Applies adaptive thresholding to convert continuous heatmap into discrete ROIs.
        Extracts bounding box coordinates [x, y, w, h] and computes physical size in cm.
        """
        h, w = heatmap.shape
        thresh_val = np.percentile(heatmap, threshold_percentile)
        binary_mask = (heatmap >= thresh_val).astype(np.uint8) * 255

        # Morphological cleanup
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        cleaned = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel)

        # Find connected contours
        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        boxes = []

        min_box_area = (h * w) * 0.005  # Filter tiny noise specks (< 0.5% image area)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area >= min_box_area:
                bx, by, bw, bh = cv2.boundingRect(cnt)
                mean_intensity = float(np.mean(heatmap[by:by+bh, bx:bx+bw]))

                box_info = {
                    "bbox_pixels": [int(bx), int(by), int(bw), int(bh)],
                    "center": [int(bx + bw // 2), int(by + bh // 2)],
                    "area_pixels": int(area),
                    "mean_activation": round(mean_intensity, 3)
                }

                # Calculate physical dimension in centimeters if pixel spacing is available
                if pixel_spacing:
                    sp_x, sp_y = pixel_spacing
                    width_cm  = round((bw * sp_x) / 10.0, 2)
                    height_cm = round((bh * sp_y) / 10.0, 2)
                    box_info["dimensions_cm"] = {"width_cm": width_cm, "height_cm": height_cm}

                boxes.append(box_info)

        # Sort by activation strength descending
        boxes.sort(key=lambda b: b["mean_activation"], reverse=True)
        return boxes

    def create_overlay(
        self,
        image_gray: np.ndarray,
        heatmap: np.ndarray,
        alpha: float = 0.55,
        colormap: int = cv2.COLORMAP_JET
    ) -> np.ndarray:
        """
        Blends continuous heatmap with original radiograph.
        Returns: RGB color overlay (1024x1024 uint8).
        """
        h, w = image_gray.shape[:2]
        if heatmap.shape != (h, w):
            heatmap = cv2.resize(heatmap, (w, h), interpolation=cv2.INTER_LINEAR)

        # Convert heatmap float (0..1) to uint8 (0..255)
        heatmap_uint8 = (heatmap * 255.0).astype(np.uint8)
        color_heatmap = cv2.applyColorMap(heatmap_uint8, colormap)

        # Ensure base image is 3-channel RGB
        if len(image_gray.shape) == 2:
            base_rgb = cv2.cvtColor(image_gray, cv2.COLOR_GRAY2RGB)
        else:
            base_rgb = image_gray.copy()

        # Alpha blend
        overlay = cv2.addWeighted(color_heatmap, alpha, base_rgb, 1.0 - alpha, 0)
        return overlay
