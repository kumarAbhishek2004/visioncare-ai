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
    ci_lower: Optional[float] = Field(default=None, description="95% Confidence Interval lower bound")
    ci_upper: Optional[float] = Field(default=None, description="95% Confidence Interval upper bound")
    epistemic_uncertainty: Optional[float] = Field(default=None, description="Test-time perturbation standard deviation")
    decision_margin: Optional[float] = Field(default=None, description="Distance from operating threshold (P - Tau)")
    boundary_stability: Optional[str] = Field(default=None, description="ROBUST, BORDERLINE, or CLEAR_NEGATIVE")


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
    ctr: Optional[Dict[str, Any]] = Field(default=None, description="Quantitative Cardiothoracic Ratio Biometrics")
    emergency_triage: Optional[Dict[str, Any]] = Field(default=None, description="ED STAT Clinical Triage Prioritization")
    clinical_report: ClinicalReportResponse
    decision_trace: DecisionTrace
    image_assets: Dict[str, str] = Field(
        default_factory=dict,
        description="Base64 encoded data URIs or paths for original, enhanced, mask, and heatmap overlay"
    )


class BatchTriageItem(BaseModel):
    study_id: str
    patient_id: str
    priority_tier: str
    urgency_score: float
    sla_turnaround: str
    top_finding: str
    reliability: str
    ctr_percentage: Optional[float] = None
    triage_summary: str


class BatchTriageResponse(BaseModel):
    total_studies: int
    stat_critical_count: int
    urgent_count: int
    routine_count: int
    worklist: List[BatchTriageItem]


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = Field(default_factory=list)
    study_id: Optional[str] = None
    study_context: Optional[Dict[str, Any]] = None
    mode: Optional[str] = "clinical"
    preferred_model: Optional[str] = "auto"
    api_key: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    suggested_questions: List[str] = Field(default_factory=list)
    source: str
    model_name: Optional[str] = "Clinical CDS Engine"


