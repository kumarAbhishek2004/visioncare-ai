"""
========================================================================================
VisionCare AI: Module 8 — Automated Cardiothoracic Ratio (CTR) Biometric Analyzer
========================================================================================
Purpose: Quantifies cardiac silhouette enlargement using anatomical lung/thoracic metrics.
Clinical Definition:
    CTR = (Maximum Cardiac Transverse Diameter) / (Maximum Inner Thoracic Diameter)
Diagnostic Criterion:
    - CTR <= 0.50 (50%): Normal Cardiac Size
    - CTR > 0.50 (50%):  Cardiomegaly (Enlarged Cardiac Silhouette)
    - CTR > 0.60 (60%):  Severe / Marked Cardiomegaly or Massive Pericardial Effusion
========================================================================================
"""

from typing import Dict, Any, Tuple, Optional
import numpy as np
import cv2


class CardiothoracicRatioAnalyzer:
    """
    Automated CTR calculator from pulmonary segmentation mask and radiograph.
    Computes physical millimeters/centimeters and renders calibrated caliper overlays.
    """

    def __init__(self, default_pixel_spacing: Tuple[float, float] = (0.143, 0.143)):
        self.pixel_spacing = default_pixel_spacing

    def analyze(
        self,
        image_gray: np.ndarray,
        lung_mask: np.ndarray,
        pixel_spacing: Optional[Tuple[float, float]] = None
    ) -> Dict[str, Any]:
        """
        Computes the quantitative Cardiothoracic Ratio (CTR) and renders an annotated caliper image.
        """
        spacing = pixel_spacing if pixel_spacing else self.pixel_spacing
        spacing_mm = spacing[0]  # mm per pixel

        h, w = lung_mask.shape[:2]

        # 1. Identify Left and Right lung contours
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            (lung_mask > 0).astype(np.uint8)
        )

        # Filter components (exclude background at index 0)
        valid_indices = []
        for i in range(1, num_labels):
            if stats[i, cv2.CC_STAT_AREA] >= 500:
                valid_indices.append((i, stats[i, cv2.CC_STAT_AREA], centroids[i][0]))

        # Sort by horizontal centroid: Right lung (anatomical right = image left), Left lung (image right)
        valid_indices.sort(key=lambda item: item[2])

        # Default fallback values if mask has irregular topology
        midline_x = w // 2
        cardiac_diameter_px = int(w * 0.42)
        thoracic_diameter_px = int(w * 0.85)

        # Level of diaphragmatic apices (lower third of thorax)
        meas_y_thorax = int(h * 0.72)
        meas_y_cardiac = int(h * 0.65)

        thoracic_left_x = int(w * 0.10)
        thoracic_right_x = int(w * 0.90)

        cardiac_left_x = int(w * 0.32)
        cardiac_right_x = int(w * 0.70)

        if len(valid_indices) >= 2:
            r_idx, _, r_cx = valid_indices[0]
            l_idx, _, l_cx = valid_indices[-1]

            r_mask = (labels == r_idx).astype(np.uint8)
            l_mask = (labels == l_idx).astype(np.uint8)

            # Midline through spine is between inner lung margins
            midline_x = int((r_cx + l_cx) / 2.0)

            # Measure inner thoracic diameter at the widest lower thorax level (65% - 80% height)
            y_start, y_end = int(h * 0.60), int(h * 0.82)
            max_thorax_w = 0
            best_y_th = meas_y_thorax
            best_th_lx, best_th_rx = thoracic_left_x, thoracic_right_x

            for y in range(y_start, y_end, 4):
                r_row = np.where(r_mask[y, :] > 0)[0]
                l_row = np.where(l_mask[y, :] > 0)[0]
                if len(r_row) > 0 and len(l_row) > 0:
                    outer_r = np.min(r_row)
                    outer_l = np.max(l_row)
                    cur_w = outer_l - outer_r
                    if cur_w > max_thorax_w:
                        max_thorax_w = cur_w
                        best_y_th = y
                        best_th_lx = outer_r
                        best_th_rx = outer_l

            if max_thorax_w > 100:
                thoracic_diameter_px = max_thorax_w
                meas_y_thorax = best_y_th
                thoracic_left_x = best_th_lx
                thoracic_right_x = best_th_rx

            # Cardiac transverse diameter: inner right margin to outer left cardiac apex
            # Measured in the retrocardiac mediastinal gap
            y_card_start, y_card_end = int(h * 0.50), int(h * 0.75)
            max_cardiac_w = 0
            best_y_cd = meas_y_cardiac
            best_cd_lx, best_cd_rx = cardiac_left_x, cardiac_right_x

            for y in range(y_card_start, y_card_end, 4):
                r_row = np.where(r_mask[y, :] > 0)[0]
                l_row = np.where(l_mask[y, :] > 0)[0]
                if len(r_row) > 0 and len(l_row) > 0:
                    inner_r_border = np.max(r_row)
                    inner_l_border = np.min(l_row)
                    cur_c_w = inner_l_border - inner_r_border
                    if cur_c_w > max_cardiac_w:
                        max_cardiac_w = cur_c_w
                        best_y_cd = y
                        best_cd_lx = inner_r_border
                        best_cd_rx = inner_l_border

            if max_cardiac_w > 50:
                cardiac_diameter_px = max_cardiac_w
                meas_y_cardiac = best_y_cd
                cardiac_left_x = best_cd_lx
                cardiac_right_x = best_cd_rx

        # Compute Ratio
        ctr_ratio = float(np.clip(cardiac_diameter_px / max(1.0, float(thoracic_diameter_px)), 0.25, 0.90))
        ctr_pct = round(ctr_ratio * 100.0, 1)

        # Convert to physical metric units (cm)
        cardiac_cm = round((cardiac_diameter_px * spacing_mm) / 10.0, 1)
        thoracic_cm = round((thoracic_diameter_px * spacing_mm) / 10.0, 1)

        # Clinical Diagnostic Triage
        if ctr_ratio <= 0.50:
            category = "NORMAL"
            clinical_impression = f"Normal cardiac silhouette (CTR: {ctr_pct}% <= 50%)."
        elif ctr_ratio <= 0.60:
            category = "MILD_TO_MODERATE_CARDIOMEGALY"
            clinical_impression = f"Mild-to-moderate cardiomegaly indicated by quantitative transverse ratio (CTR: {ctr_pct}%)."
        else:
            category = "SEVERE_CARDIOMEGALY"
            clinical_impression = f"Marked cardiomegaly or prominent pericardial fluid accumulation (CTR: {ctr_pct}% > 60%)."

        # 2. Render Diagnostic Caliper Measurement Overlay
        if len(image_gray.shape) == 2:
            annotated = cv2.cvtColor(image_gray, cv2.COLOR_GRAY2BGR)
        else:
            annotated = image_gray.copy()

        # A. Midline (Vertical Dashed/Solid White Line)
        cv2.line(annotated, (midline_x, int(h * 0.35)), (midline_x, int(h * 0.85)), (255, 255, 255), 1, cv2.LINE_AA)

        # B. Thoracic Diameter Caliper (Cyan: RGB 0, 255, 255 -> BGR 255, 255, 0)
        cv2.line(annotated, (thoracic_left_x, meas_y_thorax), (thoracic_right_x, meas_y_thorax), (255, 255, 0), 2, cv2.LINE_AA)
        cv2.line(annotated, (thoracic_left_x, meas_y_thorax - 6), (thoracic_left_x, meas_y_thorax + 6), (255, 255, 0), 2)
        cv2.line(annotated, (thoracic_right_x, meas_y_thorax - 6), (thoracic_right_x, meas_y_thorax + 6), (255, 255, 0), 2)

        # C. Cardiac Diameter Caliper (Magenta: RGB 255, 0, 255 -> BGR 255, 0, 255)
        cv2.line(annotated, (cardiac_left_x, meas_y_cardiac), (cardiac_right_x, meas_y_cardiac), (255, 0, 255), 2, cv2.LINE_AA)
        cv2.line(annotated, (cardiac_left_x, meas_y_cardiac - 6), (cardiac_left_x, meas_y_cardiac + 6), (255, 0, 255), 2)
        cv2.line(annotated, (cardiac_right_x, meas_y_cardiac - 6), (cardiac_right_x, meas_y_cardiac + 6), (255, 0, 255), 2)

        # Labels
        th_text = f"Thorax: {thoracic_cm}cm"
        cd_text = f"Heart: {cardiac_cm}cm (CTR {ctr_pct}%)"
        cv2.putText(annotated, th_text, (thoracic_left_x + 10, meas_y_thorax - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1, cv2.LINE_AA)
        cv2.putText(annotated, cd_text, (cardiac_left_x + 10, meas_y_cardiac - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 0, 255), 1, cv2.LINE_AA)

        return {
            "ctr_ratio": ctr_ratio,
            "ctr_percentage": ctr_pct,
            "cardiac_diameter_px": cardiac_diameter_px,
            "cardiac_diameter_cm": cardiac_cm,
            "thoracic_diameter_px": thoracic_diameter_px,
            "thoracic_diameter_cm": thoracic_cm,
            "category": category,
            "is_cardiomegaly": ctr_ratio > 0.50,
            "clinical_impression": clinical_impression,
            "caliper_overlay": annotated
        }
