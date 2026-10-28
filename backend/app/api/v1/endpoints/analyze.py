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
import gc
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
from ml.dicom.dicom_parser import DICOMParser
from ml.biometrics.ctr_analyzer import CardiothoracicRatioAnalyzer
from ml.triage.emergency_triage import EmergencyTriageEngine
from ml.llm.radiology_chatbot import RadiologyChatbot
from backend.app.services.pdf_service import ClinicalPDFGenerator
from backend.app.schemas.study import (
    StudyAnalysisResponse,
    BatchTriageResponse,
    BatchTriageItem,
    ChatRequest,
    ChatResponse
)

router = APIRouter()

# Singletons for memory efficiency & fast inference
iqa_analyzer = ImageQualityAnalyzer()
optimizer = ImageOptimizer(clip_limit=2.0)
extractor = PulmonaryRegionExtractor()
classifier = DiseaseClassifier()
cam_engine = GradCAMPlusPlusEngine(classifier.model)
zone_mapper = AnatomicalZoneMapper()
synthesizer = ClinicalReportSynthesizer()
ctr_analyzer = CardiothoracicRatioAnalyzer()
pdf_generator = ClinicalPDFGenerator()
chatbot = RadiologyChatbot()

# In-memory study cache for PDF generation
STUDY_CACHE: Dict[str, Dict[str, Any]] = {}


def _encode_to_base64_data_uri(img_arr: np.ndarray, max_dim: int = 800) -> str:
    """
    Encodes an OpenCV image array to an optimized data:image/jpeg;base64 string.
    Reduces JSON network payload from ~24MB down to ~0.5MB, preventing 512MB RAM OOM crashes.
    """
    if len(img_arr.shape) == 2:
        img_arr = cv2.cvtColor(img_arr, cv2.COLOR_GRAY2RGB)
    elif img_arr.shape[2] == 4:
        img_arr = cv2.cvtColor(img_arr, cv2.COLOR_RGBA2RGB)
    elif img_arr.shape[2] == 3:
        img_arr = cv2.cvtColor(img_arr, cv2.COLOR_BGR2RGB)

    h, w = img_arr.shape[:2]
    if max(h, w) > max_dim:
        scale = float(max_dim) / max(h, w)
        img_arr = cv2.resize(img_arr, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    is_success, buffer = cv2.imencode(".jpg", img_arr, [cv2.IMWRITE_JPEG_QUALITY, 85])
    if not is_success:
        return ""
    b64_str = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/jpeg;base64,{b64_str}"


def _sanitize_numpy(obj: Any) -> Any:
    """Recursively converts numpy integers, floats, booleans, and arrays to native Python primitives for Pydantic v2."""
    if isinstance(obj, dict):
        return {k: _sanitize_numpy(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_sanitize_numpy(x) for x in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


@router.post("/analyze", response_model=StudyAnalysisResponse)
def analyze_study(
    file: UploadFile = File(...),
    patient_id: Optional[str] = Form("PT-001"),
    age: Optional[int] = Form(55),
    gender: Optional[str] = Form("M"),
    view_position: Optional[str] = Form("PA"),
    pixel_spacing_x: Optional[float] = Form(0.143),
    pixel_spacing_y: Optional[float] = Form(0.143),
    xai_method: Optional[str] = Form("gradcam++"),
    enhancement_preset: Optional[str] = Form("LUNG")
):
    """
    Unified end-to-end clinical analysis:
    Runs IQA -> CLAHE/Edge Optimization -> Pulmonary Extraction -> DenseNet Inference with Uncertainty Quantification -> Multi-method Attribution (Grad-CAM++, Grad-CAM, Integrated Gradients) -> Zone Mapping -> Gemini Report.
    Declared as synchronous def so FastAPI dispatches the heavy CPU/ML workload to a threadpool.
    """
    # Normalize direct function call parameter defaults (when invoked outside FastAPI router)
    if hasattr(patient_id, "default"):
        patient_id = str(patient_id.default)
    if hasattr(age, "default"):
        age = int(age.default) if age.default is not None else None
    if hasattr(gender, "default"):
        gender = str(gender.default)
    if hasattr(view_position, "default"):
        view_position = str(view_position.default)
    if hasattr(pixel_spacing_x, "default"):
        pixel_spacing_x = float(pixel_spacing_x.default) if pixel_spacing_x.default is not None else None
    if hasattr(pixel_spacing_y, "default"):
        pixel_spacing_y = float(pixel_spacing_y.default) if pixel_spacing_y.default is not None else None
    if hasattr(xai_method, "default"):
        xai_method = str(xai_method.default)
    if hasattr(enhancement_preset, "default"):
        enhancement_preset = str(enhancement_preset.default)

    xai_method = xai_method or "gradcam++"
    enhancement_preset = enhancement_preset or "LUNG"

    # 1. Read & decode uploaded image (support both standard formats and native DICOM)
    if hasattr(file, "file") and hasattr(file.file, "read"):
        try:
            file.file.seek(0)
        except Exception:
            pass
        contents = file.file.read()
    else:
        contents = file.read()

    fname = (file.filename or "").lower()
    is_dicom = DICOMParser.is_dicom_bytes(contents) or fname.endswith(".dcm")

    if is_dicom:
        dcm_data = DICOMParser.parse(contents)
        image_gray = dcm_data["image"]
        # Use DICOM metadata if available
        if patient_id in ("PT-001", "ANONYMOUS", None) and dcm_data["patient_id"] != "ANONYMOUS":
            patient_id = dcm_data["patient_id"]
        if dcm_data["age"] is not None:
            age = dcm_data["age"]
        if dcm_data["gender"] is not None:
            gender = dcm_data["gender"]
        if dcm_data["view_position"] is not None:
            view_position = dcm_data["view_position"]
        if dcm_data["pixel_spacing"] is not None:
            pixel_spacing_x, pixel_spacing_y = dcm_data["pixel_spacing"]
    else:
        nparr = np.frombuffer(contents, np.uint8)
        image_gray = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)

    if image_gray is None:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid or readable radiograph (DICOM/PNG/JPEG).")

    study_id = f"STD-{uuid.uuid4().hex[:8].upper()}"
    now_iso = datetime.now(timezone.utc).isoformat()
    pixel_spacing = (pixel_spacing_x, pixel_spacing_y) if pixel_spacing_x and pixel_spacing_y else (0.143, 0.143)
    demographics = {
        "age": age,
        "gender": gender,
        "view_position": view_position,
        "pixel_spacing": pixel_spacing,
        "is_dicom": is_dicom
    }

    # 2. Module 1: Image Quality Assessment (IQA)
    iqa_res = iqa_analyzer.evaluate(image_gray)
    blur_m = iqa_res.get("metrics", {}).get("blur", {})
    contrast_m = iqa_res.get("metrics", {}).get("contrast", {})
    exposure_m = iqa_res.get("metrics", {}).get("exposure", {})
    iqa_res["laplacian_variance"] = float(blur_m.get("laplacian_variance", 0.0))
    iqa_res["michelson_contrast"] = float(contrast_m.get("michelson_contrast", 0.0))
    iqa_res["under_exposed_pct"] = float(exposure_m.get("under_exposed_pct", 0.0))
    iqa_res["over_exposed_pct"] = float(exposure_m.get("over_exposed_pct", 0.0))
    iqa_res["dynamic_range"] = int(image_gray.max() - image_gray.min()) if image_gray is not None else 255

    # 3. Module 2: Diagnostic Optimization
    opt_res = optimizer.optimize(image_gray, preset=enhancement_preset)
    enhanced_img = opt_res["enhanced_image"]
    opt_bone = optimizer.optimize(image_gray, preset="BONE", enable_unsharp=True)
    opt_inverted = optimizer.optimize(image_gray, preset=enhancement_preset, invert=True)

    # 4. Module 3: Pulmonary Region Extraction
    seg_res = extractor.extract(enhanced_img)

    # 5. Module 4: Multi-Label Disease Classification & Calibration
    clf_res = classifier.predict(image_gray)

    # 6. Module 5A: Multi-Method Explainability Attribution
    # Target top detected pathology, or default to Pneumonia / Atelectasis
    primary = clf_res.get("primary_findings", [])
    target_disease = primary[0]["disease"] if primary else "Pneumonia"
    target_idx = DISEASE_CLASSES.index(target_disease) if target_disease in DISEASE_CLASSES else 0

    input_tensor = classifier.preprocess(image_gray)
    h, w = image_gray.shape[:2]
    heatmap = cam_engine.generate_heatmap(input_tensor, target_idx, target_size=(w, h), method=xai_method)
    boxes = cam_engine.extract_bounding_boxes(heatmap, threshold_percentile=75.0, pixel_spacing=pixel_spacing)
    heatmap_overlay = cam_engine.create_overlay(image_gray, heatmap, alpha=0.50)

    # 7. Module 5B: 5-Zone Anatomical Mapper
    zone_res = zone_mapper.map_heatmap_to_zones(heatmap, seg_res["lung_mask"])

    # 8. Module 8: Quantitative Cardiothoracic Ratio (CTR) Biometrics
    ctr_res = ctr_analyzer.analyze(image_gray, seg_res["lung_mask"], pixel_spacing=pixel_spacing)

    # 9. Module 9: Emergency Department (ED) STAT Triage Prioritization
    triage_res = EmergencyTriageEngine.evaluate_triage(clf_res, iqa_res, ctr_res)

    # 10. Module 5C: AI Decision Trace Logger
    xai_summary = {
        "xai_method": xai_method,
        "primary_zone_name": zone_res["primary_zone_name"],
        "primary_zone_percentage": zone_res["primary_zone_percentage"],
        "bounding_boxes": boxes,
        "ctr_percentage": ctr_res["ctr_percentage"],
        "triage_priority": triage_res["priority_tier"]
    }
    trace = DecisionTraceLogger.build_trace(
        iqa_result=iqa_res,
        enhancement_result=opt_res,
        segmentation_result=seg_res,
        classification_result=clf_res,
        explainability_result=xai_summary,
        study_id=study_id
    )

    # 11. Module 6: Structured Clinical Report Synthesizer
    clinical_report = synthesizer.synthesize(
        primary_findings=clf_res["primary_findings"],
        associated_findings=clf_res["associated_findings"],
        anatomical_zone=zone_res["primary_zone_name"],
        reliability=clf_res["prediction_reliability"],
        quality_tier=iqa_res["quality_tier"],
        demographics=demographics
    )

    # 12. Encode Image Assets for Single-Roundtrip UI Rendering
    image_assets = {
        "original": _encode_to_base64_data_uri(image_gray),
        "enhanced": _encode_to_base64_data_uri(enhanced_img),
        "enhanced_bone": _encode_to_base64_data_uri(opt_bone["enhanced_image"]),
        "enhanced_inverted": _encode_to_base64_data_uri(opt_inverted["enhanced_image"]),
        "lung_mask": _encode_to_base64_data_uri(seg_res["lung_mask"]),
        "overlay_mask": _encode_to_base64_data_uri(seg_res["overlay_view"]),
        "heatmap_overlay": _encode_to_base64_data_uri(heatmap_overlay),
        "caliper_overlay": _encode_to_base64_data_uri(ctr_res["caliper_overlay"])
    }

    # Clean non-serializable elements from ctr_res before returning
    ctr_clean = {k: v for k, v in ctr_res.items() if k != "caliper_overlay"}

    # Sanitize all outputs so numpy types (np.int64, np.float32) never reach Pydantic serializers
    ctr_clean = _sanitize_numpy(ctr_clean)
    iqa_clean = _sanitize_numpy(iqa_res)
    clf_clean = _sanitize_numpy(clf_res)
    zone_clean = _sanitize_numpy(zone_res)
    boxes_clean = _sanitize_numpy(boxes)
    triage_clean = _sanitize_numpy(triage_res)
    demographics_clean = _sanitize_numpy(demographics)
    pulmonary_clean = _sanitize_numpy({
        "lung_area_ratio": seg_res["lung_area_ratio"],
        "right_lung_area_ratio": seg_res.get("right_lung_area_ratio", 0.0),
        "left_lung_area_ratio": seg_res.get("left_lung_area_ratio", 0.0),
        "lung_symmetry_index": seg_res.get("lung_symmetry_index", 1.0),
        "thoracic_envelope": seg_res["thoracic_envelope"],
        "validation_status": seg_res["validation_status"],
        "status_message": seg_res["status_message"],
        "is_valid_frontal": seg_res["is_valid_frontal"]
    })

    # Cache study in memory for instantaneous PDF generation
    STUDY_CACHE[study_id] = {
        "analysis_data": {
            "study_id": study_id,
            "timestamp": now_iso,
            "patient_id": patient_id,
            "demographics": demographics_clean,
            "iqa": iqa_clean,
            "pulmonary_extraction": pulmonary_clean,
            "classification": clf_clean,
            "explainability": zone_clean,
            "ctr": ctr_clean,
            "emergency_triage": triage_clean,
            "clinical_report": clinical_report,
            "decision_trace": trace
        },
        "raw_images": {
            "original": image_gray,
            "enhanced": enhanced_img,
            "overlay_mask": seg_res["overlay_view"],
            "heatmap_overlay": heatmap_overlay,
            "caliper_overlay": ctr_res["caliper_overlay"]
        }
    }

    # Bound STUDY_CACHE to last 5 entries to preserve memory in cloud environments
    if len(STUDY_CACHE) > 5:
        oldest = list(STUDY_CACHE.keys())[:-5]
        for k in oldest:
            STUDY_CACHE.pop(k, None)

    # Free transient image variables & force Linux heap page trim
    del image_gray, enhanced_img, opt_bone, opt_inverted, heatmap, heatmap_overlay
    gc.collect()
    try:
        import ctypes
        libc = ctypes.CDLL("libc.so.6")
        libc.malloc_trim(0)
    except Exception:
        pass

    return StudyAnalysisResponse(
        study_id=study_id,
        timestamp=now_iso,
        patient_id=patient_id,
        demographics=demographics_clean,
        iqa=iqa_clean,
        pulmonary_extraction=pulmonary_clean,
        classification=clf_clean,
        explainability={
            "xai_method": xai_method,
            "available_methods": ["gradcam++", "gradcam", "integrated_gradients", "saliency"],
            "target_pathology": target_disease,
            "primary_zone": zone_clean["primary_zone"],
            "primary_zone_name": zone_clean["primary_zone_name"],
            "primary_zone_percentage": zone_clean["primary_zone_percentage"],
            "secondary_zone": zone_clean["secondary_zone"],
            "secondary_zone_percentage": zone_clean["secondary_zone_percentage"],
            "zone_breakdown_pct": zone_clean["zone_breakdown_pct"],
            "clinical_summary": zone_clean["clinical_summary"],
            "bounding_boxes": boxes_clean
        },
        ctr=ctr_clean,
        emergency_triage=triage_clean,
        clinical_report=clinical_report,
        decision_trace=trace,
        image_assets=image_assets
    )


@router.post("/batch", response_model=BatchTriageResponse)
def analyze_batch_triage(
    files: list[UploadFile] = File(...),
):
    """
    Hospital Emergency Department (ED) Batch Ingestion & STAT Triage Prioritization.
    Ingests multiple radiographs simultaneously, runs full pipeline inference,
    and returns a sorted clinical worklist ordered by urgency score.
    """
    items: list[BatchTriageItem] = []
    stat_cnt, urgent_cnt, routine_cnt = 0, 0, 0

    for idx, f in enumerate(files):
        p_id = f"PT-ED-{100 + idx}"
        try:
            res = analyze_study(file=f, patient_id=p_id)
            tri = res.emergency_triage or {}
            tier = tri.get("priority_tier", "ROUTINE")
            if tier == "STAT_CRITICAL":
                stat_cnt += 1
            elif tier == "URGENT":
                urgent_cnt += 1
            else:
                routine_cnt += 1

            top_find = "No Acute Findings"
            if res.classification.get("primary_findings"):
                top_find = res.classification["primary_findings"][0]["disease"]

            items.append(BatchTriageItem(
                study_id=res.study_id,
                patient_id=res.patient_id or p_id,
                priority_tier=tier,
                urgency_score=tri.get("urgency_score", 10.0),
                sla_turnaround=tri.get("sla_turnaround", "< 4 hours"),
                top_finding=top_find,
                reliability=res.classification.get("prediction_reliability", "MODERATE"),
                ctr_percentage=res.ctr.get("ctr_percentage") if res.ctr else None,
                triage_summary=tri.get("triage_summary", "Study processed.")
            ))
        except Exception as e:
            items.append(BatchTriageItem(
                study_id=f"STD-ERR-{idx}",
                patient_id=p_id,
                priority_tier="ROUTINE",
                urgency_score=0.0,
                sla_turnaround="--",
                top_finding="Error processing",
                reliability="LOW",
                ctr_percentage=None,
                triage_summary=f"Analysis failed: {str(e)}"
            ))
            routine_cnt += 1

    # Sort worklist in descending order of urgency score
    items.sort(key=lambda x: x.urgency_score, reverse=True)

    return BatchTriageResponse(
        total_studies=len(items),
        stat_critical_count=stat_cnt,
        urgent_count=urgent_cnt,
        routine_count=routine_cnt,
        worklist=items
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


@router.get("/chat/providers")
def get_chat_providers():
    """Returns available LLM providers configured on the backend."""
    return chatbot.get_available_providers()


@router.post("/chat", response_model=ChatResponse)
def chat_with_radiologist_copilot(req: ChatRequest):
    """
    Conversational clinical assistant grounded in chest X-ray findings,
    Grad-CAM++ explainability maps, CTR biometrics, and IQA metrics.
    """
    study_ctx = req.study_context
    if not study_ctx and req.study_id and req.study_id in STUDY_CACHE:
        study_ctx = STUDY_CACHE[req.study_id].get("analysis_data", {})

    if not study_ctx:
        study_ctx = {}

    history_dicts = [{"role": h.role, "content": h.content} for h in (req.history or [])]

    result = chatbot.chat(
        message=req.message,
        history=history_dicts,
        study_context=study_ctx,
        mode=req.mode or "clinical",
        preferred_model=req.preferred_model or "auto"
    )

    return ChatResponse(
        response=result["response"],
        suggested_questions=result.get("suggested_questions", []),
        source=result.get("source", "clinical_cds_engine"),
        model_name=result.get("model_name", "Clinical CDS Engine")
    )


