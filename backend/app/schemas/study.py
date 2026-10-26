"""
========================================================================================
VisionCare AI: API Schemas for Study Ingestion & Consolidated Analysis
========================================================================================
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class FindingItem(BaseModel):
    disease: str
    probability: float
    probability_pct: float
    threshold: float
    is_detected: bool
    confidence_tier: str


class BBoxItem(BaseModel):
    bbox_pixels: List[int]
    center: List[int]
    area_pixels: int
    mean_activation: float
    dimensions_cm: Optional[Dict[str, float]] = None


class DecisionTraceStep(BaseModel):
    step: int
    module: str
    status: str
    summary: str


class DecisionTrace(BaseModel):
    trace_id: str
    study_id: str
    generated_at: str
    total_steps: int
    safety_status: str
    steps: List[DecisionTraceStep]


class ClinicalReportResponse(BaseModel):
    technique: str
    findings: str
    impression: str
    differential_considerations: List[str]
    recommendations: str
    disclaimer: str


class StudyAnalysisResponse(BaseModel):
    """
    Consolidated response payload returned by POST /api/v1/studies/analyze.
    Contains the entire analysis in a single round-trip (< 2.5s).
    """
    study_id: str
    timestamp: str
    patient_id: Optional[str] = "ANONYMOUS"
    demographics: Dict[str, Any]
    iqa: Dict[str, Any]
    pulmonary_extraction: Dict[str, Any]
    classification: Dict[str, Any]
    explainability: Dict[str, Any]
    clinical_report: ClinicalReportResponse
    decision_trace: DecisionTrace
    image_assets: Dict[str, str] = Field(
        default_factory=dict,
        description="Base64 encoded data URIs or paths for original, enhanced, mask, and heatmap overlay"
    )
