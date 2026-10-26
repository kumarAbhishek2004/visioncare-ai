"""
========================================================================================
VisionCare AI: Module 5B — 5-Zone Anatomical Localization Mapper
========================================================================================
Purpose: Translates raw spatial heatmaps into standard ACR radiological zones:
         - RUZ: Right Upper Zone (Apex to upper hilum)
         - RMZ: Right Middle Zone (Hilar region / middle lobe)
         - RLZ: Right Lower Zone (Basilar field / costophrenic angle)
         - LUZ: Left Upper Zone (Apex to hilum)
         - LLZ: Left Lower Zone (Basilar field / retrocardiac space)
         - MEDIASTINUM: Cardiac silhouette & central vascular structures
========================================================================================
"""

from typing import Dict, Any, Tuple, List, Optional
import numpy as np
import cv2


class AnatomicalZoneMapper:
    """
    Partitions segmented lung fields into standard clinical zones and computes
    spatial intersection with Grad-CAM++ activation maps.
    """

    ZONE_NAMES = {
        "RUZ": "Right Upper Zone (RUZ)",
        "RMZ": "Right Middle Zone (RMZ)",
        "RLZ": "Right Lower Zone (RLZ)",
        "LUZ": "Left Upper Zone (LUZ)",
        "LLZ": "Left Lower Zone (LLZ)",
        "MEDIASTINUM": "Central Mediastinum / Cardiac Silhouette"
    }

    def partition_lung_zones(self, lung_mask: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Splits bilateral lung masks into 5 standard anatomical zones:
        Right lung is trisected vertically (RUZ, RMZ, RLZ).
        Left lung is bisected vertically (LUZ, LLZ).
        """
        h, w = lung_mask.shape
        mid_x = w // 2

        # Split into Right Lung (left side of image in frontal view) and Left Lung (right side)
        right_lung_mask = np.zeros_like(lung_mask)
        left_lung_mask  = np.zeros_like(lung_mask)

        right_lung_mask[:, :mid_x] = lung_mask[:, :mid_x]
        left_lung_mask[:, mid_x:]  = lung_mask[:, mid_x:]

        zones = {}

        # 1. Right Lung Trisection (RUZ, RMZ, RLZ)
        y_right = np.where(right_lung_mask > 0)[0]
        if len(y_right) > 0:
            r_top = int(np.min(y_right))
            r_bot = int(np.max(y_right))
            r_third = (r_bot - r_top) // 3

            ruz_mask = np.zeros_like(lung_mask)
            rmz_mask = np.zeros_like(lung_mask)
            rlz_mask = np.zeros_like(lung_mask)

            ruz_mask[r_top : r_top + r_third, :mid_x] = right_lung_mask[r_top : r_top + r_third, :mid_x]
            rmz_mask[r_top + r_third : r_top + 2 * r_third, :mid_x] = right_lung_mask[r_top + r_third : r_top + 2 * r_third, :mid_x]
            rlz_mask[r_top + 2 * r_third : r_bot + 1, :mid_x] = right_lung_mask[r_top + 2 * r_third : r_bot + 1, :mid_x]

            zones["RUZ"] = ruz_mask
            zones["RMZ"] = rmz_mask
            zones["RLZ"] = rlz_mask
        else:
            zones["RUZ"] = np.zeros_like(lung_mask)
            zones["RMZ"] = np.zeros_like(lung_mask)
            zones["RLZ"] = np.zeros_like(lung_mask)

        # 2. Left Lung Bisection (LUZ, LLZ)
        y_left = np.where(left_lung_mask > 0)[0]
        if len(y_left) > 0:
            l_top = int(np.min(y_left))
            l_bot = int(np.max(y_left))
            l_half = (l_bot - l_top) // 2

            luz_mask = np.zeros_like(lung_mask)
            llz_mask = np.zeros_like(lung_mask)

            luz_mask[l_top : l_top + l_half, mid_x:] = left_lung_mask[l_top : l_top + l_half, mid_x:]
            llz_mask[l_top + l_half : l_bot + 1, mid_x:] = left_lung_mask[l_top + l_half : l_bot + 1, mid_x:]

            zones["LUZ"] = luz_mask
            zones["LLZ"] = llz_mask
        else:
            zones["LUZ"] = np.zeros_like(lung_mask)
            zones["LLZ"] = np.zeros_like(lung_mask)

        # 3. Mediastinum (Region between lungs)
        mediastinum_mask = np.zeros_like(lung_mask)
        if len(y_right) > 0 and len(y_left) > 0:
            med_top = min(int(np.min(y_right)), int(np.min(y_left)))
            med_bot = max(int(np.max(y_right)), int(np.max(y_left)))
            # Central column
            med_left = int(mid_x - w * 0.12)
            med_right = int(mid_x + w * 0.12)
            mediastinum_mask[med_top:med_bot, med_left:med_right] = 255
            # Exclude lung fields from mediastinum
            mediastinum_mask = cv2.bitwise_and(mediastinum_mask, cv2.bitwise_not(lung_mask))

        zones["MEDIASTINUM"] = mediastinum_mask
        return zones

    def map_heatmap_to_zones(
        self,
        heatmap: np.ndarray,
        lung_mask: np.ndarray,
        threshold_percentile: float = 70.0
    ) -> Dict[str, Any]:
        """
        Calculates the spatial percentage of Grad-CAM++ activation inside each clinical zone.
        Returns primary localized zone, percentage, and clinical text summary.
        """
        # Ensure dimensions match
        if heatmap.shape != lung_mask.shape:
            heatmap = cv2.resize(heatmap, (lung_mask.shape[1], lung_mask.shape[0]))

        # Threshold to focus on dominant activation
        thresh_val = np.percentile(heatmap, threshold_percentile)
        active_heatmap = np.where(heatmap >= thresh_val, heatmap, 0.0)
        total_activation = float(np.sum(active_heatmap))

        zones = self.partition_lung_zones(lung_mask)
        zone_breakdown = {}

        if total_activation > 1e-6:
            for zone_key, zmask in zones.items():
                zone_act = float(np.sum(active_heatmap[zmask > 0]))
                pct = (zone_act / total_activation) * 100.0
                zone_breakdown[zone_key] = round(pct, 1)
        else:
            for zone_key in zones:
                zone_breakdown[zone_key] = 0.0

        # Sort zones by activation percentage descending
        sorted_zones = sorted(zone_breakdown.items(), key=lambda x: x[1], reverse=True)
        primary_zone_key, primary_pct = sorted_zones[0]
        secondary_zone_key, secondary_pct = sorted_zones[1]

        # Clinical text description
        primary_name = self.ZONE_NAMES.get(primary_zone_key, primary_zone_key)
        if primary_pct >= 50.0:
            summary_text = f"Primary focal activation localized to {primary_name} ({primary_pct}% attribution)."
        elif primary_pct >= 25.0:
            secondary_name = self.ZONE_NAMES.get(secondary_zone_key, secondary_zone_key)
            summary_text = (
                f"Bilateral/multizonal activation predominantly in {primary_name} ({primary_pct}%) "
                f"and {secondary_name} ({secondary_pct}%)."
            )
        else:
            summary_text = "Diffuse activation across pulmonary fields without focal zone predilection."

        return {
            "primary_zone": primary_zone_key,
            "primary_zone_name": primary_name,
            "primary_zone_percentage": primary_pct,
            "secondary_zone": secondary_zone_key,
            "secondary_zone_percentage": secondary_pct,
            "zone_breakdown_pct": zone_breakdown,
            "clinical_summary": summary_text
        }
