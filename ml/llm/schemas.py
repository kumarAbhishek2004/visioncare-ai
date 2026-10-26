"""
========================================================================================
VisionCare AI: Module 6 — Pydantic Schemas for Structured Clinical JSON
========================================================================================
Purpose: Defines the rigid typed schema for LLM clinical summaries,
         preventing free-form hallucinations and guaranteeing UI compatibility.
========================================================================================
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ClinicalReport(BaseModel):
    """Structured Clinical Radiology Report Schema."""
    technique: str = Field(
        ...,
        description="Radiographic examination technique, e.g. 'Frontal chest radiograph (PA view)'"
    )
    findings: str = Field(
        ...,
        description="Objective anatomical observations across pulmonary fields, cardiac silhouette, and costophrenic angles."
    )
    impression: str = Field(
        ...,
        description="Primary clinical summary correlated with model confidence."
    )
    differential_considerations: List[str] = Field(
        default_factory=list,
        description="Differential diagnoses ranked by clinical likelihood."
    )
    recommendations: str = Field(
        ...,
        description="Suggested clinical correlation, lab tests, or follow-up imaging."
    )
    disclaimer: str = Field(
        default=(
            "VisionCare AI is an assistive decision-support research tool. "
            "Automated findings must be correlated clinically and verified by a board-certified radiologist."
        ),
        description="Mandatory regulatory disclaimer."
    )
