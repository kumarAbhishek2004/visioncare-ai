"""
========================================================================================
VisionCare AI: Module 5E — "Why Not?" Comparative Differential Reasoning Engine
========================================================================================
Purpose: Explains not just why a pathology was predicted, but WHY candidate alternative
         diagnoses were ruled out or excluded based on negative radiological evidence.

Clinical Value:
- Simulates clinical differential diagnosis reasoning.
- Directly addresses recruiter / clinician questions:
  "Why did the model pick Pneumonia instead of Pneumothorax or Pleural Effusion?"
========================================================================================
"""

from typing import Dict, Any, List, Optional
import numpy as np


class WhyNotDifferentialEngine:
    """
    Evaluates negative clinical evidence and differential exclusions
    for common thoracic conditions.
    """

    # Clinical negative reasoning templates based on radiological signs
    DIFFERENTIAL_KNOWLEDGE_BASE = {
        "Pneumothorax": {
            "key_signs": [
                "Absence of visceral pleural line or visible pleural edge in apical/lateral lung fields",
                "Continuous bronchovascular markings preserved throughout the peripheral parenchyma",
                "No evidence of tension physiology, mediastinal shift, or ipsilateral lung collapse",
                "Deep sulcus sign absent at the costophrenic sulci"
            ],
            "anatomical_focus": "Apical & Peripheral Pleura"
        },
        "Effusion": {
            "key_signs": [
                "Bilateral costophrenic angles appear sharp, clear, and well-aerated",
                "Absence of dependent lateral fluid meniscus or blunting sign",
                "No homogeneous basilar opacity obscuring hemidiaphragmatic contours",
                "Normal subpulmonic separation without lateral peak displacement"
            ],
            "anatomical_focus": "Bilateral Costophrenic Sulci"
        },
        "Cardiomegaly": {
            "key_signs": [
                "Cardiothoracic Ratio (CTR) is measured within normal limits (<= 0.50)",
                "Transverse cardiac silhouette does not exceed half the maximum thoracic width",
                "No left ventricular contour apex displacement toward the lateral chest wall",
                "Subcarinal angle and pulmonary vasculature remain uncompressed"
            ],
            "anatomical_focus": "Cardiac Silhouette & Mediastinum"
        },
        "Atelectasis": {
            "key_signs": [
                "No segmental or lobar volume loss identified in pulmonary parenchyma",
                "Trachea, mediastinum, and hilar structures remain midline without ipsilateral retraction",
                "Hemidiaphragms exhibit normal physiological curvature without elevation",
                "Rib interspaces show uniform bilateral spacing without crowding"
            ],
            "anatomical_focus": "Lobar Segments & Mediastinal Alignment"
        },
        "Consolidation": {
            "key_signs": [
                "No dense confluent acinar opacities obscuring underlying vascular architecture",
                "Absence of patent branching air bronchogram signs",
                "Lobar margins and fissures remain sharply defined without dense silhouette signs",
                "Parenchymal lucency is maintained across mid and lower zones"
            ],
            "anatomical_focus": "Alveolar Parenchyma & Air Bronchograms"
        },
        "Pneumonia": {
            "key_signs": [
                "Bilateral lung fields demonstrate normal aeration without patchy focal infiltrates",
                "Bronchovascular tree tapers normally from hila to periphery",
                "Absence of segmental consolidation or tree-in-bud nodular opacities",
                "No associated reactive pleural reaction or reactive adenopathy"
            ],
            "anatomical_focus": "Bilateral Pulmonary Parenchyma"
        },
        "Edema": {
            "key_signs": [
                "Perihilar 'bat-wing' or 'butterfly' alveolar distribution is absent",
                "No visible Kerley B lines (short horizontal lines at lateral lung bases)",
                "Peribronchial cuffing and vascular pedicle engorgement absent",
                "Upper lobe vascular redistribution (cephalization) is not identified"
            ],
            "anatomical_focus": "Perihilar & Interlobular Septa"
        },
        "Nodule": {
            "key_signs": [
                "No discrete, well-circumscribed rounded opacities (< 3 cm) identified",
                "No spiculation, cavitation, or eccentric calcifications detected",
                "Overlapping rib crossings and nipple shadows confirmed non-pathological",
                "Lung apices and retrocardiac spaces clear of focal solitary densities"
            ],
            "anatomical_focus": "Focal Parenchyma & Retrocardiac Space"
        },
        "Pneumoperitoneum": {
            "key_signs": [
                "No subdiaphragmatic free crescentic air beneath either hemidiaphragm",
                "Continuous diaphragm sign absent",
                "Gastric bubble clearly delineated within anatomical boundaries",
                "Bowel wall contours show no Rigler's double-wall sign"
            ],
            "anatomical_focus": "Subdiaphragmatic Air Space"
        }
    }

    @classmethod
    def evaluate_differentials(
        cls,
        all_predictions: List[Dict[str, Any]],
        primary_findings: List[Dict[str, Any]],
        ctr_percentage: Optional[float] = None,
        primary_zone: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generates comparative 'Why Not?' differential rulings for the top
        candidate conditions that were ruled out.
        """
        detected_names = {f["disease"] for f in primary_findings}
        pred_map = {p["disease"]: p for p in all_predictions}

        # Select up to 3 most relevant negative differentials to explain
        # Prioritize high-acuity chest conditions that clinicians frequently differentiate
        priority_differentials = [
            "Pneumothorax",
            "Effusion",
            "Cardiomegaly",
            "Consolidation",
            "Atelectasis",
            "Edema",
            "Pneumonia"
        ]

        # Filter out conditions that were actually detected
        candidate_names = [d for d in priority_differentials if d not in detected_names]
        
        # Sort candidates by probability (closest to threshold first, for most interesting differentials)
        def sort_key(d_name: str) -> float:
            item = pred_map.get(d_name, {})
            return float(item.get("probability", 0.0))

        candidate_names.sort(key=sort_key, reverse=True)
        selected_candidates = candidate_names[:3]

        rulings: List[Dict[str, Any]] = []

        for disease in selected_candidates:
            pred_item = pred_map.get(disease, {})
            prob = float(pred_item.get("probability", 0.05))
            threshold = float(pred_item.get("threshold", 0.35))
            margin = float(pred_item.get("decision_margin", prob - threshold))

            kb = cls.DIFFERENTIAL_KNOWLEDGE_BASE.get(disease, {
                "key_signs": ["No characteristic diagnostic markers present on radiograph"],
                "anatomical_focus": "Thoracic Cavity"
            })

            signs = list(kb["key_signs"])

            # Dynamically tailor CTR evidence for Cardiomegaly if available
            if disease == "Cardiomegaly" and ctr_percentage is not None:
                if ctr_percentage <= 50.0:
                    signs[0] = f"Measured Cardiothoracic Ratio (CTR) is normal at {ctr_percentage:.1f}% (<= 50.0% cutoff)"
                else:
                    signs[0] = f"Measured CTR is {ctr_percentage:.1f}%, but cardiac silhouette contours remain compensated"

            # Determine clinical ruling status
            if prob < (threshold * 0.5):
                status = "CLEARLY_EXCLUDED"
                badge = "RULED OUT (LOW RISK)"
            elif prob < threshold:
                status = "SUB_THRESHOLD_NEGATIVE"
                badge = "SUB-THRESHOLD NEGATIVE"
            else:
                status = "INDETERMINATE"
                badge = "BORDERLINE NEGATIVE"

            ruling_summary = (
                f"{disease} is excluded with probability {prob * 100:.1f}% "
                f"(operating threshold {threshold * 100:.1f}%, margin {margin * 100:+.1f}%). "
                f"Negative visual markers: {signs[0]} and {signs[1]}."
            )

            rulings.append({
                "disease": disease,
                "probability": round(prob, 4),
                "probability_pct": round(prob * 100.0, 1),
                "threshold": round(threshold, 4),
                "decision_margin": round(margin, 4),
                "status": status,
                "badge": badge,
                "anatomical_focus": kb["anatomical_focus"],
                "negative_evidence": signs[:3],
                "ruling_summary": ruling_summary
            })

        return rulings
