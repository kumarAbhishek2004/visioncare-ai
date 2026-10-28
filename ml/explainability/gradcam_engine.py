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

import gc
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

    def _prepare_cam_input(self, input_tensor: torch.Tensor) -> torch.Tensor:
        """Preserves 100% native resolution for exact mathematical attribution accuracy."""
        return input_tensor

    def _cleanup_cam_memory(self):
        """Immediately frees intermediate activations, autograd buffers, and memory caches."""
        self.gradients = None
        self.activations = None
        self.model.zero_grad(set_to_none=True)
        gc.collect()

    def generate_gradcam(
        self,
        input_tensor: torch.Tensor,
        class_idx: int,
        target_size: Tuple[int, int] = (1024, 1024)
    ) -> np.ndarray:
        """
        Computes standard Grad-CAM attribution map via global average pooled gradients:
        alpha_k = (1/Z) * sum(grad_k)
        L_GradCAM = ReLU(sum(alpha_k * A_k))
        """
        self.model.zero_grad(set_to_none=True)
        cam_input = self._prepare_cam_input(input_tensor)
        output = self.model(cam_input)
        target_score = output[0, class_idx]
        target_score.backward(retain_graph=False)

        if self.gradients is None or self.activations is None:
            self._cleanup_cam_memory()
            return np.zeros(target_size, dtype=np.float32)

        grads = self.gradients[0].detach()   # [C, H, W]
        acts = self.activations[0].detach()  # [C, H, W]

        # Standard Grad-CAM weights: global average of gradients across spatial dimensions
        weights = grads.mean(dim=(1, 2), keepdim=True)
        cam = (weights * acts).sum(dim=0)
        cam = F.relu(cam)

        self._cleanup_cam_memory()

        cam_np = cam.cpu().numpy()
        cam_min, cam_max = cam_np.min(), cam_np.max()
        if cam_max > cam_min:
            cam_np = (cam_np - cam_min) / (cam_max - cam_min)
        else:
            cam_np = np.zeros_like(cam_np)

        heatmap_resized = cv2.resize(cam_np, target_size, interpolation=cv2.INTER_CUBIC)
        return np.clip(heatmap_resized, 0.0, 1.0)

    def generate_gradcam_plus_plus(
        self,
        input_tensor: torch.Tensor,
        class_idx: int,
        target_size: Tuple[int, int] = (1024, 1024)
    ) -> np.ndarray:
        """
        Computes Grad-CAM++ continuous activation map with higher-order gradient weighting.
        """
        self.model.zero_grad(set_to_none=True)
        cam_input = self._prepare_cam_input(input_tensor)
        output = self.model(cam_input)
        target_score = output[0, class_idx]
        target_score.backward(retain_graph=False)

        if self.gradients is None or self.activations is None:
            self._cleanup_cam_memory()
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

        self._cleanup_cam_memory()

        cam_np = cam.cpu().numpy()
        cam_min, cam_max = cam_np.min(), cam_np.max()
        if cam_max > cam_min:
            cam_np = (cam_np - cam_min) / (cam_max - cam_min)
        else:
            cam_np = np.zeros_like(cam_np)

        heatmap_resized = cv2.resize(cam_np, target_size, interpolation=cv2.INTER_CUBIC)
        return np.clip(heatmap_resized, 0.0, 1.0)

    def generate_integrated_gradients(
        self,
        input_tensor: torch.Tensor,
        class_idx: int,
        steps: int = 8,
        target_size: Tuple[int, int] = (1024, 1024)
    ) -> np.ndarray:
        """
        Computes Integrated Gradients (Sundararajan et al., ICML 2017) feature attribution.
        Integrates path gradients from black baseline to input image.
        """
        cam_input = self._prepare_cam_input(input_tensor)
        baseline = torch.zeros_like(cam_input)
        diff = cam_input - baseline
        accumulated_grads = torch.zeros_like(cam_input)

        for step in range(1, steps + 1):
            alpha = float(step) / float(steps)
            interpolated = baseline + alpha * diff
            interpolated.requires_grad_(True)
            self.model.zero_grad(set_to_none=True)
            out = self.model(interpolated)
            target = out[0, class_idx]
            target.backward(retain_graph=False)
            if interpolated.grad is not None:
                accumulated_grads += interpolated.grad.detach()

        self._cleanup_cam_memory()

        # Multiply by input difference: (x - x') * avg_grad
        ig = (diff * (accumulated_grads / steps)).squeeze(0).abs().mean(dim=0).cpu().numpy()
        ig_min, ig_max = ig.min(), ig.max()
        if ig_max > ig_min:
            ig = (ig - ig_min) / (ig_max - ig_min)
        else:
            ig = np.zeros_like(ig)

        # Smooth slightly and resize to target resolution
        ig_smooth = cv2.GaussianBlur(ig, (7, 7), 2.0)
        heatmap_resized = cv2.resize(ig_smooth, target_size, interpolation=cv2.INTER_CUBIC)
        return np.clip(heatmap_resized, 0.0, 1.0)

    def generate_saliency(
        self,
        input_tensor: torch.Tensor,
        class_idx: int,
        target_size: Tuple[int, int] = (1024, 1024)
    ) -> np.ndarray:
        """
        Computes Vanilla Gradient Saliency map (Simonyan et al.):
        Takes absolute maximum gradient with respect to input pixels.
        """
        cam_input = self._prepare_cam_input(input_tensor)
        inp = cam_input.clone().detach().requires_grad_(True)
        self.model.zero_grad(set_to_none=True)
        out = self.model(inp)
        target = out[0, class_idx]
        target.backward(retain_graph=False)

        if inp.grad is None:
            self._cleanup_cam_memory()
            return np.zeros(target_size, dtype=np.float32)

        saliency, _ = torch.max(inp.grad.detach().abs(), dim=1)
        saliency_np = saliency.squeeze(0).cpu().numpy()
        self._cleanup_cam_memory()

        s_min, s_max = saliency_np.min(), saliency_np.max()
        if s_max > s_min:
            saliency_np = (saliency_np - s_min) / (s_max - s_min)
        else:
            saliency_np = np.zeros_like(saliency_np)

        saliency_smooth = cv2.GaussianBlur(saliency_np, (5, 5), 1.5)
        heatmap_resized = cv2.resize(saliency_smooth, target_size, interpolation=cv2.INTER_CUBIC)
        return np.clip(heatmap_resized, 0.0, 1.0)

    def generate_heatmap(
        self,
        input_tensor: torch.Tensor,
        class_idx: int,
        target_size: Tuple[int, int] = (1024, 1024),
        method: str = "gradcam++"
    ) -> np.ndarray:
        """
        Unified multi-technique explainability selector:
        Supports 'gradcam++', 'gradcam', 'integrated_gradients', and 'saliency'.
        """
        m = method.lower().strip()
        if m in ("gradcam", "grad_cam"):
            return self.generate_gradcam(input_tensor, class_idx, target_size)
        elif m in ("integrated_gradients", "ig"):
            return self.generate_integrated_gradients(input_tensor, class_idx, target_size=target_size)
        elif m in ("saliency", "vanilla_gradient"):
            return self.generate_saliency(input_tensor, class_idx, target_size)
        else:
            # Default to Grad-CAM++
            return self.generate_gradcam_plus_plus(input_tensor, class_idx, target_size)

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
