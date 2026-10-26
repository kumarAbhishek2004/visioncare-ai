"""
========================================================================================
VisionCare AI: Module 2 — Diagnostic Image Optimization & Window/Level Presets
========================================================================================
Purpose: Deterministic, non-generative contrast enhancement.
         Improves visibility of alveolar opacities, pleural margins, and cardiac borders
         WITHOUT hallucinating synthetic textures (FDA/CE-MDR compliant).
========================================================================================
"""

from typing import Dict, Any, Tuple, Union
import numpy as np
import cv2
from PIL import Image


class ImageOptimizer:
    """
    Medical-grade image enhancement using CLAHE, Bilateral filtering,
    and radiological Window/Level (WW/WL) linear transfer functions.
    """

    # Clinical Window Width (WW) and Window Level/Center (WL) presets
    PRESETS = {
        "LUNG": {"window_center": 130, "window_width": 180},
        "MEDIASTINUM": {"window_center": 155, "window_width": 220},
        "BONE": {"window_center": 185, "window_width": 140},
        "DEFAULT": {"window_center": 128, "window_width": 255}
    }

    def __init__(self, clip_limit: float = 2.0, tile_grid_size: Tuple[int, int] = (8, 8)):
        self.clip_limit = clip_limit
        self.tile_grid_size = tile_grid_size
        self._clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)

    def _ensure_uint8_grayscale(self, image: Union[np.ndarray, Image.Image]) -> np.ndarray:
        if isinstance(image, Image.Image):
            image = np.array(image)
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        if image.dtype != np.uint8:
            image = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        return image

    def apply_clahe(self, gray: np.ndarray) -> np.ndarray:
        """Applies Contrast-Limited Adaptive Histogram Equalization."""
        return self._clahe.apply(gray)

    def apply_bilateral_filter(
        self, gray: np.ndarray, d: int = 5, sigma_color: float = 50.0, sigma_space: float = 5.0
    ) -> np.ndarray:
        """Edge-preserving smoothing to suppress high-frequency acquisition sensor noise."""
        return cv2.bilateralFilter(gray, d, sigma_color, sigma_space)

    def apply_window_level(
        self, gray: np.ndarray, window_center: int, window_width: int
    ) -> np.ndarray:
        """
        Applies radiologist Window Center / Window Width (WL/WW) linear transform:
        Maps [WL - WW/2, WL + WW/2] to [0, 255].
        """
        lower = max(0, window_center - window_width // 2)
        upper = min(255, window_center + window_width // 2)

        if upper <= lower:
            return gray

        # Linear scaling within window
        windowed = np.clip(gray, lower, upper)
        windowed = ((windowed - lower) / (upper - lower) * 255.0).astype(np.uint8)
        return windowed

    def optimize(
        self,
        image: Union[np.ndarray, Image.Image],
        preset: str = "DEFAULT",
        enable_bilateral: bool = True
    ) -> Dict[str, Any]:
        """
        Runs complete non-generative optimization pipeline:
        1. Bilateral edge-preserving noise filter (optional)
        2. Window/Level preset transformation
        3. Adaptive CLAHE contrast balancing
        """
        gray = self._ensure_uint8_grayscale(image)

        # 1. Bilateral filter
        denoised = self.apply_bilateral_filter(gray) if enable_bilateral else gray

        # 2. Window/Level adjustment
        cfg = self.PRESETS.get(preset.upper(), self.PRESETS["DEFAULT"])
        windowed = self.apply_window_level(denoised, cfg["window_center"], cfg["window_width"])

        # 3. CLAHE
        enhanced = self.apply_clahe(windowed)

        return {
            "original_gray": gray,
            "enhanced_image": enhanced,
            "applied_preset": preset.upper(),
            "window_parameters": cfg,
            "clahe_clip_limit": self.clip_limit
        }
