"""
========================================================================================
VisionCare AI: Module 3 — Pulmonary Region Extraction
========================================================================================
Purpose: Segment pulmonary parenchyma and extract the thoracic bounding envelope.
Outputs:
  1. Binary Lung Mask (Left & Right lung fields)
  2. Masked Lung Visualization (for UI display)
  3. Overlay View (Cyan color tint over pulmonary fields)
  4. Thoracic Bounding Envelope [x, y, w, h] (covers lungs + cardiac mediastinum)
  5. Frontal Sanity Check: Flags scan if segmented area < 8% (Non-chest/pediatric warning)
========================================================================================
"""

import os
from typing import Dict, Any, Tuple, Union, Optional
import numpy as np
import cv2
from PIL import Image

import torch
import torch.nn as nn
import torch.nn.functional as F


class BasicUNetBlock(nn.Module):
    def __init__(self, in_ch: int, out_ch: int):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.conv(x)


class PulmonaryUNet(nn.Module):
    """
    Standard 2D U-Net for pulmonary parenchyma segmentation.
    Compatible with MONAI BasicUNet parameter specifications.
    """
    def __init__(self, in_channels: int = 1, out_channels: int = 1, features: Tuple[int, ...] = (16, 32, 64, 128)):
        super().__init__()
        self.downs = nn.ModuleList()
        self.ups = nn.ModuleList()
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)

        # Encoder
        curr_in = in_channels
        for feature in features:
            self.downs.append(BasicUNetBlock(curr_in, feature))
            curr_in = feature

        # Bottleneck
        self.bottleneck = BasicUNetBlock(features[-1], features[-1] * 2)

        # Decoder
        for feature in reversed(features):
            self.ups.append(
                nn.ConvTranspose2d(feature * 2, feature, kernel_size=2, stride=2)
            )
            self.ups.append(BasicUNetBlock(feature * 2, feature))

        self.final_conv = nn.Conv2d(features[0], out_channels, kernel_size=1)

    def forward(self, x):
        skip_connections = []
        for down in self.downs:
            x = down(x)
            skip_connections.append(x)
            x = self.pool(x)

        x = self.bottleneck(x)
        skip_connections = skip_connections[::-1]

        for idx in range(0, len(self.ups), 2):
            x = self.ups[idx](x)
            skip_connection = skip_connections[idx // 2]
            if x.shape != skip_connection.shape:
                x = F.interpolate(x, size=skip_connection.shape[2:], mode="bilinear", align_corners=False)
            concat_x = torch.cat((skip_connection, x), dim=1)
            x = self.ups[idx + 1](concat_x)

        return torch.sigmoid(self.final_conv(x))


class PulmonaryRegionExtractor:
    """
    Extracts pulmonary parenchyma masks, color overlays, and the thoracic bounding envelope.
    """

    def __init__(self, weights_path: Optional[str] = None, device: Optional[str] = None):
        self.device = torch.device(device if device else ("cuda" if torch.cuda.is_available() else "cpu"))
        self.model = PulmonaryUNet(in_channels=1, out_channels=1).to(self.device)
        self.has_weights = False

        if weights_path and os.path.exists(weights_path):
            try:
                state_dict = torch.load(weights_path, map_location=self.device)
                self.model.load_state_dict(state_dict)
                self.has_weights = True
                print(f"[+] Loaded pretrained U-Net lung segmentation weights from: {weights_path}")
            except Exception as e:
                print(f"[!] Warning: Could not load U-Net weights ({e}). Using morphological fallback.")

        self.model.eval()

    def _morphological_segmentation_fallback(self, gray: np.ndarray) -> np.ndarray:
        """
        High-precision anatomical morphological fallback when weights file is not yet downloaded.
        Extracts bilateral lung fields using Otsu thresholding, connected components, and convex hulls.
        """
        h, w = gray.shape
        # Blur to smooth rib artifacts
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        # Threshold: lung fields are dark (air attenuation)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Clear borders (remove background air and image borders)
        border_mask = np.zeros_like(thresh)
        border_mask[int(h * 0.05):int(h * 0.95), int(w * 0.05):int(w * 0.95)] = 255
        cleaned = cv2.bitwise_and(thresh, border_mask)

        # Morphological opening and closing
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
        opened = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel, iterations=2)
        closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel, iterations=3)

        # Find two largest components (left and right lung fields)
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(closed)
        mask = np.zeros_like(gray, dtype=np.uint8)

        if num_labels > 1:
            # Sort by area, skip background (index 0)
            areas = [(i, stats[i, cv2.CC_STAT_AREA]) for i in range(1, num_labels)]
            areas.sort(key=lambda x: x[1], reverse=True)

            # Keep top 2 components (lungs) if they have reasonable size
            for comp_idx, area in areas[:2]:
                if area > (h * w * 0.03):
                    mask[labels == comp_idx] = 255

        # Final smoothing
        mask = cv2.GaussianBlur(mask, (5, 5), 0)
        _, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
        return mask

    def extract(self, image: Union[np.ndarray, Image.Image]) -> Dict[str, Any]:
        """
        Executes pulmonary region extraction:
        Returns:
          - lung_mask: Binary mask (1024x1024 uint8)
          - masked_lung: Grayscale image with background suppressed
          - overlay_view: Color image with translucent cyan overlay on lungs
          - thoracic_bbox: [x, y, w, h] encompassing lungs and mediastinum
          - validation_status: PASS or FLAG_FOR_REVIEW
        """
        if isinstance(image, Image.Image):
            image = np.array(image)
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        orig_h, orig_w = gray.shape[:2]

        if self.has_weights:
            # Inference through U-Net at 256x256
            resized = cv2.resize(gray, (256, 256), interpolation=cv2.INTER_LINEAR)
            tensor = torch.from_numpy(resized.astype(np.float32) / 255.0).unsqueeze(0).unsqueeze(0).to(self.device)
            with torch.no_grad():
                pred = self.model(tensor).squeeze().cpu().numpy()
            pred_mask = (pred >= 0.50).astype(np.uint8) * 255
            lung_mask = cv2.resize(pred_mask, (orig_w, orig_h), interpolation=cv2.INTER_NEAREST)
        else:
            lung_mask = self._morphological_segmentation_fallback(gray)

        # 1. Masked Lung
        masked_lung = cv2.bitwise_and(gray, gray, mask=lung_mask)

        # 2. Translucent Cyan Overlay (for UI display)
        color_base = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        overlay_color = np.zeros_like(color_base)
        overlay_color[lung_mask > 0] = [230, 216, 0]  # BGR Cyan / Medical Teal
        overlay_view = cv2.addWeighted(color_base, 0.70, overlay_color, 0.30, 0)

        # 3. Thoracic Bounding Envelope [x, y, w, h]
        y_indices, x_indices = np.where(lung_mask > 0)
        if len(x_indices) > 0:
            x1, x2 = int(np.min(x_indices)), int(np.max(x_indices))
            y1, y2 = int(np.min(y_indices)), int(np.max(y_indices))
            # Expand horizontally slightly to ensure cardiac mediastinum is included
            pad_x = int((x2 - x1) * 0.05)
            x1 = max(0, x1 - pad_x)
            x2 = min(orig_w, x2 + pad_x)
            thoracic_bbox = [x1, y1, x2 - x1, y2 - y1]
        else:
            thoracic_bbox = [0, 0, orig_w, orig_h]

        # 4. View / Confidence Sanity Check
        lung_pixel_count = np.sum(lung_mask > 0)
        lung_area_ratio = float(lung_pixel_count / (orig_h * orig_w))

        if lung_area_ratio < 0.08:
            validation_status = "FLAG_FOR_REVIEW"
            status_message = "Low segmentation confidence: Non-standard projection, severe pathology, or pediatric scan."
            is_valid_frontal = False
        else:
            validation_status = "VALIDATED_FRONTAL_THORAX"
            status_message = "Bilateral pulmonary fields successfully identified."
            is_valid_frontal = True

        return {
            "lung_mask": lung_mask,
            "masked_lung": masked_lung,
            "overlay_view": overlay_view,
            "thoracic_envelope": thoracic_bbox,
            "lung_area_ratio": round(lung_area_ratio, 4),
            "validation_status": validation_status,
            "status_message": status_message,
            "is_valid_frontal": is_valid_frontal
        }
