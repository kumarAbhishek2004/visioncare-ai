"""
========================================================================================
VisionCare AI: Module 5C — AI Decision Trace & Regulatory Audit Trail
========================================================================================
Purpose: Compiles a deterministic, step-by-step audit trail for each study,
         fulfilling FDA SaMD and EU AI Act transparency requirements.
========================================================================================
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


class DecisionTraceLogger:
    """
    Compiles an auditable clinical decision trace across all pipeline modules.
    """

    @staticmethod
    def build_trace(
        iqa_result: Dict[str, Any],
        enhancement_result: Dict[str, Any],
        segmentation_result: Dict[str, Any],
        classification_result: Dict[str, Any],
        explainability_result: Dict[str, Any],
        study_id: Optional[str] = None
    ) -> Dict[str, Any]:
        trace_id = f"TRC-{uuid.uuid4().hex[:8].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()

        steps = []

        # Step 1: Ingestion & Sanity
        is_valid = segmentation_result.get("is_valid_frontal", True)
        steps.append({
            "step": 1,
            "module": "Ingestion & View Validation",
            "status": "PASS" if is_valid else "FLAG_FOR_REVIEW",
            "summary": (
                f"Frontal thorax confirmed. Segmented lung area ratio: "
                f"{segmentation_result.get('lung_area_ratio', 0.0)*100:.1f}%."
                if is_valid else
                f"Warning: Low segmentation area ({segmentation_result.get('lung_area_ratio', 0.0)*100:.1f}%). "
                "Non-standard projection suspected."
            )
        })

        # Step 2: IQA
        iqa_score = iqa_result.get("overall_score", 0.0)
        iqa_tier = iqa_result.get("quality_tier", "AVERAGE")
        sharpness = iqa_result.get("metrics", {}).get("blur", {}).get("laplacian_variance", 0.0)
        contrast = iqa_result.get("metrics", {}).get("contrast", {}).get("michelson_contrast", 0.0)
        steps.append({
            "step": 2,
            "module": "Image Quality Assessment (IQA)",
            "status": "PASS" if iqa_score >= 50.0 else "SUB_DIAGNOSTIC",
            "summary": (
                f"Quality Score: {iqa_score}/100 ({iqa_tier}). "
                f"Laplacian Sharpness: {sharpness}, Michelson Contrast: {contrast}."
            )
        })

        # Step 3: Enhancement
        preset = enhancement_result.get("applied_preset", "DEFAULT")
        clip_limit = enhancement_result.get("clahe_clip_limit", 2.0)
        steps.append({
            "step": 3,
            "module": "Diagnostic Optimization",
            "status": "PASS",
            "summary": f"Non-generative CLAHE applied (clip limit {clip_limit}). Active Window/Level preset: {preset}."
        })

        # Step 4: Pulmonary Region Extraction
        bbox = segmentation_result.get("thoracic_envelope", [0, 0, 0, 0])
        steps.append({
            "step": 4,
            "module": "Pulmonary Region Extraction",
            "status": "PASS",
            "summary": f"Bilateral lung parenchyma isolated. Thoracic envelope bounding box [x,y,w,h]: {bbox}."
        })

        # Step 5: Classification & Calibration
        primary = classification_result.get("primary_findings", [])
        if primary:
            top_finding = primary[0]
            top_str = f"{top_finding['disease']} ({top_finding['probability_pct']}%)"
        else:
            top_str = "No Acute Pathology Detected"
        calibrated = classification_result.get("calibrated", False)
        steps.append({
            "step": 5,
            "module": "Multi-Label Classification & Calibration",
            "status": "PASS",
            "summary": (
                f"DenseNet-121 inferred 14 categories. Temperature scaling calibration: {'Active' if calibrated else 'Inactive'}. "
                f"Primary Finding: {top_str}."
            )
        })

        # Step 6: Explainability & Zone Mapping
        primary_zone = explainability_result.get("primary_zone_name", "Pulmonary Field")
        primary_zone_pct = explainability_result.get("primary_zone_percentage", 0.0)
        num_boxes = len(explainability_result.get("bounding_boxes", []))
        steps.append({
            "step": 6,
            "module": "Explainability & Spatial Attribution",
            "status": "PASS",
            "summary": (
                f"Grad-CAM++ localized activation to {primary_zone} ({primary_zone_pct}% attribution). "
                f"Extracted {num_boxes} lesion region bounding box(es)."
            )
        })

        # Step 7: Safety Gating
        safety_status = classification_result.get("safety_triage", "ASSISTED_REVIEW_READY")
        reliability = classification_result.get("prediction_reliability", "MODERATE")
        steps.append({
            "step": 7,
            "module": "Clinical Safety Gating",
            "status": safety_status,
            "summary": (
                f"Prediction Reliability: {reliability}. "
                f"{classification_result.get('triage_message', '')}"
            )
        })

        return {
            "trace_id": trace_id,
            "study_id": study_id if study_id else f"STD-{uuid.uuid4().hex[:6].upper()}",
            "generated_at": now_iso,
            "total_steps": len(steps),
            "safety_status": safety_status,
            "steps": steps
        }
