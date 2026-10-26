"""
========================================================================================
VisionCare AI: Unified Clinical Orchestration Endpoint
========================================================================================
Endpoint: POST /api/v1/studies/analyze
Purpose: Coordinates all 6 pipeline stages in memory in a single network round-trip (< 2.5s).
========================================================================================
"""

import os
import io
import uuid
import base64
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import cv2
import numpy as np
from PIL import Image

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Response
from fastapi.responses import JSONResponse

from ml.quality.iqa_analyzer import ImageQualityAnalyzer
from ml.enhancement.clahe_processor import ImageOptimizer
from ml.segmentation.monai_unet import PulmonaryRegionExtractor
from ml.classification.inference import DiseaseClassifier, DISEASE_CLASSES
from ml.explainability.gradcam_engine import GradCAMPlusPlusEngine
from ml.explainability.zone_mapper import AnatomicalZoneMapper
from ml.explainability.decision_trace import DecisionTraceLogger
from ml.llm.synthesizer import ClinicalReportSynthesizer
from backend.app.services.pdf_service import ClinicalPDFGenerator
from backend.app.schemas.study import StudyAnalysisResponse

router = APIRouter()

# Singletons for memory efficiency & fast inference
iqa_analyzer = ImageQualityAnalyzer()
optimizer = ImageOptimizer(clip_limit=2.0)
extractor = PulmonaryRegionExtractor()
classifier = DiseaseClassifier()
cam_engine = GradCAMPlusPlusEngine(classifier.model)
zone_mapper = AnatomicalZoneMapper()
synthesizer = ClinicalReportSynthesizer()
pdf_generator = ClinicalPDFGenerator()

# In-memory study cache for PDF generation
STUDY_CACHE: Dict[str, Dict[str, Any]] = {}


def _encode_to_base64_data_uri(img_arr: np.ndarray) -> str:
    """Encodes an OpenCV image array to a data:image/png;base64 string."""
    if len(img_arr.shape) == 2:
        img_arr = cv2.cvtColor(img_arr, cv2.COLOR_GRAY2RGB)
    elif img_arr.shape[2] == 4:
        img_arr = cv2.cvtColor(img_arr, cv2.COLOR_RGBA2RGB)
    elif img_arr.shape[2] == 3:
        img_arr = cv2.cvtColor(img_arr, cv2.COLOR_BGR2RGB)

    is_success, buffer = cv2.imencode(".png", img_arr)
    if not is_success:
        return ""
    b64_str = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/png;base64,{b64_str}"


@router.post("/analyze", response_model=StudyAnalysisResponse)
def analyze_study(
    file: UploadFile = File(...),
    patient_id: Optional[str] = Form("PT-001"),
    age: Optional[int] = Form(55),
    gender: Optional[str] = Form("M"),
    view_position: Optional[str] = Form("PA"),
    pixel_spacing_x: Optional[float] = Form(0.143),
    pixel_spacing_y: Optional[float] = Form(0.143)
):
    """
    Unified end-to-end clinical analysis:
    Runs IQA -> CLAHE -> Pulmonary Extraction -> DenseNet Inference -> Grad-CAM++ -> Zone Mapping -> Gemini Report.
    Declared as synchronous def so FastAPI dispatches the heavy CPU/ML workload to a threadpool.
    """
    # 1. Read & decode uploaded image
    if hasattr(file, "file") and hasattr(file.file, "read"):
        try:
            file.file.seek(0)
        except Exception:
            pass
        contents = file.file.read()
    else:
        contents = file.read()

    nparr = np.frombuffer(contents, np.uint8)
    image_gray = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)

    if image_gray is None:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid or readable image.")

    study_id = f"STD-{uuid.uuid4().hex[:8].upper()}"
    now_iso = datetime.now(timezone.utc).isoformat()
    pixel_spacing = (pixel_spacing_x, pixel_spacing_y) if pixel_spacing_x and pixel_spacing_y else (0.143, 0.143)
    demographics = {
        "age": age,
        "gender": gender,
        "view_position": view_position,
        "pixel_spacing": pixel_spacing
    }

    # 2. Module 1: Image Quality Assessment (IQA)
    iqa_res = iqa_analyzer.evaluate(image_gray)

    # 3. Module 2: Diagnostic Optimization
    opt_res = optimizer.optimize(image_gray, preset="LUNG")
    enhanced_img = opt_res["enhanced_image"]

    # 4. Module 3: Pulmonary Region Extraction
    seg_res = extractor.extract(enhanced_img)

    # 5. Module 4: Multi-Label Disease Classification & Calibration
    clf_res = classifier.predict(image_gray)

    # 6. Module 5A: Grad-CAM++ Feature Attribution
    # Target top detected pathology, or default to Pneumonia / Atelectasis
    primary = clf_res.get("primary_findings", [])
    target_disease = primary[0]["disease"] if primary else "Pneumonia"
    target_idx = DISEASE_CLASSES.index(target_disease) if target_disease in DISEASE_CLASSES else 0

    input_tensor = classifier.preprocess(image_gray)
    h, w = image_gray.shape[:2]
    heatmap = cam_engine.generate_heatmap(input_tensor, target_idx, target_size=(w, h))
    boxes = cam_engine.extract_bounding_boxes(heatmap, threshold_percentile=75.0, pixel_spacing=pixel_spacing)
    heatmap_overlay = cam_engine.create_overlay(image_gray, heatmap, alpha=0.50)

    # 7. Module 5B: 5-Zone Anatomical Mapper
    zone_res = zone_mapper.map_heatmap_to_zones(heatmap, seg_res["lung_mask"])

    # 8. Module 5C: AI Decision Trace Logger
    xai_summary = {
        "primary_zone_name": zone_res["primary_zone_name"],
        "primary_zone_percentage": zone_res["primary_zone_percentage"],
        "bounding_boxes": boxes
    }
    trace = DecisionTraceLogger.build_trace(
        iqa_result=iqa_res,
        enhancement_result=opt_res,
        segmentation_result=seg_res,
        classification_result=clf_res,
        explainability_result=xai_summary,
        study_id=study_id
    )

    # 9. Module 6: Structured Clinical Report Synthesizer
    clinical_report = synthesizer.synthesize(
        primary_findings=clf_res["primary_findings"],
        associated_findings=clf_res["associated_findings"],
        anatomical_zone=zone_res["primary_zone_name"],
        reliability=clf_res["prediction_reliability"],
        quality_tier=iqa_res["quality_tier"],
        demographics=demographics
    )

    # 10. Encode Image Assets for Single-Roundtrip UI Rendering
    image_assets = {
        "original": _encode_to_base64_data_uri(image_gray),
        "enhanced": _encode_to_base64_data_uri(enhanced_img),
        "lung_mask": _encode_to_base64_data_uri(seg_res["lung_mask"]),
        "overlay_mask": _encode_to_base64_data_uri(seg_res["overlay_view"]),
        "heatmap_overlay": _encode_to_base64_data_uri(heatmap_overlay)
    }

    # Cache study in memory for instantaneous PDF generation
    STUDY_CACHE[study_id] = {
        "analysis_data": {
            "study_id": study_id,
            "timestamp": now_iso,
            "patient_id": patient_id,
            "demographics": demographics,
            "iqa": iqa_res,
            "pulmonary_extraction": seg_res,
            "classification": clf_res,
            "explainability": zone_res,
            "clinical_report": clinical_report,
            "decision_trace": trace
        },
        "raw_images": {
            "original": image_gray,
            "enhanced": enhanced_img,
            "overlay_mask": seg_res["overlay_view"],
            "heatmap_overlay": heatmap_overlay
        }
    }

    return StudyAnalysisResponse(
        study_id=study_id,
        timestamp=now_iso,
        patient_id=patient_id,
        demographics=demographics,
        iqa=iqa_res,
        pulmonary_extraction={
            "lung_area_ratio": seg_res["lung_area_ratio"],
            "thoracic_envelope": seg_res["thoracic_envelope"],
            "validation_status": seg_res["validation_status"],
            "status_message": seg_res["status_message"],
            "is_valid_frontal": seg_res["is_valid_frontal"]
        },
        classification=clf_res,
        explainability={
            "target_pathology": target_disease,
            "primary_zone": zone_res["primary_zone"],
            "primary_zone_name": zone_res["primary_zone_name"],
            "primary_zone_percentage": zone_res["primary_zone_percentage"],
            "secondary_zone": zone_res["secondary_zone"],
            "secondary_zone_percentage": zone_res["secondary_zone_percentage"],
            "zone_breakdown_pct": zone_res["zone_breakdown_pct"],
            "clinical_summary": zone_res["clinical_summary"],
            "bounding_boxes": boxes
        },
        clinical_report=clinical_report,
        decision_trace=trace,
        image_assets=image_assets
    )


@router.get("/pdf/{study_id}")
def download_study_pdf(study_id: str):
    """
    Downloads clinical PDF study report with 4-panel image comparison and ACR narrative.
    """
    if study_id not in STUDY_CACHE:
        raise HTTPException(
            status_code=404,
            detail=f"Study with ID '{study_id}' not found in active session cache."
        )

    cached = STUDY_CACHE[study_id]
    pdf_bytes = pdf_generator.generate_pdf(
        analysis_data=cached["analysis_data"],
        image_dict=cached["raw_images"]
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=VisionCare_Report_{study_id}.pdf"}
    )
