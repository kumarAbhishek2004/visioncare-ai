"""
========================================================================================
VisionCare AI: Module 1 — Image Quality Assessment (IQA)
========================================================================================
Purpose: Deterministic OpenCV-based image quality evaluation. Assesses blur, exposure,
         contrast, and spatial resolution before clinical inference.
Design Rule: Pure classical computer vision — zero deep learning overhead (< 20 ms).
========================================================================================
"""

from typing import Dict, Any, Tuple, Union
import numpy as np
import cv2
from PIL import Image


class ImageQualityAnalyzer:
    """
    Evaluates Chest Radiograph diagnostic quality using classical image processing metrics.
    """

    def __init__(
        self,
        blur_threshold_low: float = 80.0,
        blur_threshold_high: float = 250.0,
        min_resolution: int = 512,
        recommended_resolution: int = 1024
    ):
        self.blur_threshold_low = blur_threshold_low
        self.blur_threshold_high = blur_threshold_high
        self.min_resolution = min_resolution
        self.recommended_resolution = recommended_resolution

    def _ensure_grayscale(self, image: Union[np.ndarray, Image.Image, str]) -> np.ndarray:
        """Converts input image (path, PIL Image, or numpy array) to single-channel uint8."""
        if isinstance(image, str):
            img_arr = cv2.imread(image, cv2.IMREAD_GRAYSCALE)
            if img_arr is None:
                raise FileNotFoundError(f"Could not load image from path: {image}")
            return img_arr

        if isinstance(image, Image.Image):
            image = np.array(image)

        if len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        return image.astype(np.uint8)

    def compute_blur(self, gray: np.ndarray) -> Tuple[float, str]:
        """
        Calculates sharpness via Variance of the Laplacian:
        Var(Laplacian) = sum((L(x,y) - mean)^2) / N
        High variance = sharp edges; Low variance = motion blur / soft tissue smearing.
        """
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = float(laplacian.var())

        if variance >= self.blur_threshold_high:
            rating = "EXCELLENT"
        elif variance >= self.blur_threshold_low:
            rating = "ACCEPTABLE"
        else:
            rating = "BLURRY"

        return round(variance, 2), rating

    def compute_exposure(self, gray: np.ndarray) -> Tuple[float, float, str]:
        """
        Calculates under-penetration (underexposed black clipping) and
        over-penetration (overexposed burnout).
        """
        total_pixels = gray.size
        under_exposed_pct = float(np.sum(gray < 15) / total_pixels) * 100.0
        over_exposed_pct  = float(np.sum(gray > 240) / total_pixels) * 100.0

        if under_exposed_pct > 35.0:
            status = "UNDER_PENETRATED"
        elif over_exposed_pct > 25.0:
            status = "OVER_PENETRATED"
        elif under_exposed_pct > 20.0 or over_exposed_pct > 15.0:
            status = "BORDERLINE"
        else:
            status = "OPTIMAL"

        return round(under_exposed_pct, 2), round(over_exposed_pct, 2), status

    def compute_contrast(self, gray: np.ndarray) -> Tuple[float, str]:
        """
        Calculates Michelson Contrast using 5th and 95th percentiles:
        C = (P95 - P5) / (P95 + P5)
        """
        p5 = float(np.percentile(gray, 5))
        p95 = float(np.percentile(gray, 95))

        if p95 + p5 == 0:
            return 0.0, "POOR"

        michelson = (p95 - p5) / (p95 + p5)
        michelson = round(float(michelson), 3)

        if michelson >= 0.70:
            rating = "EXCELLENT"
        elif michelson >= 0.45:
            rating = "GOOD"
        elif michelson >= 0.30:
            rating = "MODERATE"
        else:
            rating = "POOR"

        return michelson, rating

    def evaluate(self, image: Union[np.ndarray, Image.Image, str]) -> Dict[str, Any]:
        """
        Executes complete Image Quality Assessment and returns structured score and recommendations.
        """
        gray = self._ensure_grayscale(image)
        height, width = gray.shape[:2]

        # 1. Individual metrics
        blur_val, blur_status = self.compute_blur(gray)
        under_pct, over_pct, exposure_status = self.compute_exposure(gray)
        contrast_val, contrast_status = self.compute_contrast(gray)

        # 2. Resolution check
        is_sub_resolution = (height < self.min_resolution or width < self.min_resolution)
        resolution_status = "SUB_DIAGNOSTIC" if is_sub_resolution else (
            "RECOMMENDED" if height >= self.recommended_resolution and width >= self.recommended_resolution else "ACCEPTABLE"
        )

        # 3. Composite Score Calculation (0 to 100)
        # Sharpness component (max 40 pts)
        sharpness_pts = min(40.0, (blur_val / self.blur_threshold_high) * 40.0)

        # Contrast component (max 30 pts)
        contrast_pts = min(30.0, (contrast_val / 0.75) * 30.0)

        # Exposure component (max 30 pts)
        penalty = (max(0.0, under_pct - 15.0) * 0.8) + (max(0.0, over_pct - 10.0) * 1.0)
        exposure_pts = max(0.0, 30.0 - penalty)

        overall_score = max(5.0, min(100.0, sharpness_pts + contrast_pts + exposure_pts))
        if is_sub_resolution:
            overall_score = min(overall_score, 45.0)

        overall_score = round(overall_score, 1)

        # 4. Status and Recommendations
        if overall_score >= 75.0:
            quality_tier = "GOOD"
            diagnostic_recommendation = "Suitable for AI-assisted clinical decision support."
            is_acceptable = True
        elif overall_score >= 50.0:
            quality_tier = "AVERAGE"
            diagnostic_recommendation = "Acceptable with automated contrast enhancement (CLAHE)."
            is_acceptable = True
        else:
            quality_tier = "POOR"
            diagnostic_recommendation = "Sub-diagnostic scan quality. Manual radiologist inspection or retake advised."
            is_acceptable = False

        return {
            "overall_score": overall_score,
            "quality_tier": quality_tier,
            "is_acceptable": is_acceptable,
            "recommendation": diagnostic_recommendation,
            "metrics": {
                "blur": {
                    "laplacian_variance": blur_val,
                    "status": blur_status
                },
                "exposure": {
                    "under_exposed_pct": under_pct,
                    "over_exposed_pct": over_pct,
                    "status": exposure_status
                },
                "contrast": {
                    "michelson_contrast": contrast_val,
                    "status": contrast_status
                },
                "resolution": {
                    "width": width,
                    "height": height,
                    "status": resolution_status
                }
            }
        }
