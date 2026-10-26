"""
========================================================================================
VisionCare AI: Module 9 — Emergency Department (ED) STAT Clinical Triage Prioritizer
========================================================================================
Purpose: Automatically stratifies chest radiographs into clinical priority worklists.
Prioritization Hierarchy:
  - TIER 1: STAT / CRITICAL (SLA < 15 mins): Pneumothorax, Acute Edema, Massive Consolidation
  - TIER 2: URGENT (SLA < 60 mins): Mass, Infiltration, Pleural Effusion
  - TIER 3: ROUTINE (SLA < 4 hrs): Cardiomegaly, Atelectasis, Emphysema, Unremarkable
========================================================================================
"""

from typing import Dict, Any, List, Optional


class EmergencyTriageEngine:
    """
    Hospital Emergency Department Worklist Triage Engine.
    Computes Urgency Score (0 - 100) and assigns STAT / URGENT / ROUTINE routing.
    """

    CRITICAL_DISEASES = {"Pneumothorax", "Edema", "Consolidation"}
    URGENT_DISEASES = {"Mass", "Infiltration", "Effusion", "Pneumonia"}

    @classmethod
    def evaluate_triage(
        cls,
        classification_result: Dict[str, Any],
        iqa_result: Dict[str, Any],
        ctr_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculates triage category, numerical urgency score (0-100), and turnaround SLA.
        """
        all_findings = classification_result.get("all_findings", [])
        detected_findings = classification_result.get("primary_findings", [])

        # Map disease name to probability
        prob_map = {f["disease"]: f["probability"] for f in all_findings}

        stat_triggers = []
        urgent_triggers = []

        # Check critical conditions
        for d in cls.CRITICAL_DISEASES:
            prob = prob_map.get(d, 0.0)
            thresh = next((f["threshold"] for f in all_findings if f["disease"] == d), 0.5)
            if prob >= thresh:
                stat_triggers.append(f"{d} ({prob*100:.1f}%)")

        # Check urgent conditions
        for d in cls.URGENT_DISEASES:
            prob = prob_map.get(d, 0.0)
            thresh = next((f["threshold"] for f in all_findings if f["disease"] == d), 0.5)
            if prob >= thresh:
                urgent_triggers.append(f"{d} ({prob*100:.1f}%)")

        # Calculate Urgency Score (0 - 100)
        score = 10.0  # Baseline routine score

        # Add critical weights
        for d in cls.CRITICAL_DISEASES:
            score += prob_map.get(d, 0.0) * 45.0

        # Add urgent weights
        for d in cls.URGENT_DISEASES:
            score += prob_map.get(d, 0.0) * 20.0

        # Add severe cardiomegaly weight if CTR > 0.60
        if ctr_result and ctr_result.get("ctr_ratio", 0.0) > 0.60:
            score += 15.0
            urgent_triggers.append(f"Severe Cardiomegaly (CTR {ctr_result['ctr_percentage']}%)")

        # Cap score
        urgency_score = min(100.0, round(score, 1))

        # Assign Tier & SLA
        if len(stat_triggers) > 0 or urgency_score >= 65.0:
            priority_tier = "STAT_CRITICAL"
            priority_color = "#ef4444"  # Red
            sla_text = "< 15 minutes (Immediate Radiologist Review Required)"
            summary = f"CRITICAL: Immediate alert triggered by {', '.join(stat_triggers) if stat_triggers else 'High Urgency Score'}."
        elif len(urgent_triggers) > 0 or urgency_score >= 35.0:
            priority_tier = "URGENT"
            priority_color = "#f59e0b"  # Amber
            sla_text = "< 60 minutes"
            summary = f"URGENT: Prioritized review for {', '.join(urgent_triggers) if urgent_triggers else 'Intermediate Risk'}."
        else:
            priority_tier = "ROUTINE"
            priority_color = "#10b981"  # Emerald
            sla_text = "< 4 hours"
            summary = "ROUTINE: No acute life-threatening findings detected above clinical cutoffs."

        return {
            "priority_tier": priority_tier,
            "priority_color": priority_color,
            "urgency_score": urgency_score,
            "sla_turnaround": sla_text,
            "stat_triggers": stat_triggers,
            "urgent_triggers": urgent_triggers,
            "triage_summary": summary
        }
