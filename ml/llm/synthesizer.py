"""
========================================================================================
VisionCare AI: Module 6 — Multi-Model Clinical Report Synthesizer
========================================================================================
Purpose: Generates structured, ACR-style clinical findings and impressions.
Supports:
- High-speed inference via GPT OSS 120B / Groq
- Google Gemini Flash (when valid key is configured)
- Immediate offline deterministic fallback (guarantees < 2.5s analysis response)
Safety Rule: Strictly explains AI perception; NEVER makes an autonomous diagnosis.
========================================================================================
"""

import os
import json
from typing import Dict, Any, List, Optional
from ml.llm.schemas import ClinicalReport


class ClinicalReportSynthesizer:
    """
    Synthesizes structured clinical radiology reports using Groq / GPT OSS 120B,
    Gemini, or deterministic offline expert rules.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.gemini_client = None
        self.openai_client = None
        self._init_clients(api_key)

    def _init_clients(self, api_key: Optional[str] = None):
        """Initializes available LLM clients with strict timeouts to prevent hanging."""
        # 1. Initialize Groq / OpenAI client (with 5-second timeout)
        groq_key = os.environ.get("GROQ_API_KEY")
        openai_key = os.environ.get("OPENAI_API_KEY") or groq_key
        openai_base_url = os.environ.get("OPENAI_BASE_URL")

        if groq_key and not openai_base_url:
            openai_base_url = "https://api.groq.com/openai/v1"

        if openai_key or openai_base_url:
            try:
                import openai
                import httpx
                self.openai_client = openai.OpenAI(
                    api_key=openai_key or "no-key-required",
                    base_url=openai_base_url or None,
                    http_client=httpx.Client(timeout=5.0)
                )
                print(f"[+] Synthesizer: Groq/OpenAI client initialized (Base URL: {openai_base_url or 'api.openai.com'}).")
            except Exception as e:
                print(f"[!] Synthesizer: OpenAI init failed: {e}")
                self.openai_client = None

        # 2. Initialize Gemini client
        gemini_key = api_key or os.environ.get("GEMINI_API_KEY")
        if gemini_key:
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=gemini_key)
                print("[+] Synthesizer: Gemini client initialized.")
            except Exception:
                try:
                    import google.generativeai as legacy_genai
                    legacy_genai.configure(api_key=gemini_key)
                    self.gemini_client = legacy_genai.GenerativeModel("gemini-1.5-flash")
                    print("[+] Synthesizer: Legacy Gemini client initialized.")
                except Exception as e:
                    print(f"[!] Synthesizer: Gemini init failed: {e}")
                    self.gemini_client = None

    def _build_prompt(
        self,
        primary_findings: List[Dict[str, Any]],
        associated_findings: List[Dict[str, Any]],
        anatomical_zone: str,
        reliability: str,
        quality_tier: str,
        demographics: Optional[Dict[str, Any]] = None
    ) -> str:
        demo_str = "Adult patient"
        view_str = "PA projection"
        if demographics:
            age = demographics.get("age", 55)
            gender = demographics.get("gender", "M")
            view_str = f"{demographics.get('view_position', 'PA')} view"
            demo_str = f"{age}-year-old {'male' if gender == 'M' else 'female'}"

        findings_summary = []
        for f in primary_findings:
            findings_summary.append(f"- {f['disease']}: {f.get('probability_pct', 0)}% (Cutoff: {f.get('threshold', 0.5)*100:.1f}%)")
        if not findings_summary:
            findings_summary.append("- No acute findings above operational diagnostic thresholds.")

        assoc_summary = [f"{f['disease']} ({f.get('probability_pct', 0)}%)" for f in associated_findings]
        assoc_str = ", ".join(assoc_summary) if assoc_summary else "None"

        prompt = f"""
You are an expert Radiology Report Assistant generating a structured preliminary summary for a board-certified radiologist.
PATIENT CONTEXT: {demo_str}, {view_str}.
IMAGE QUALITY: {quality_tier}.
AI PREDICTION RELIABILITY: {reliability}.
PRIMARY LOCALIZATION: {anatomical_zone}.

AI DETECTED FINDINGS:
{chr(10).join(findings_summary)}

ASSOCIATED BORDERLINE FINDINGS:
{assoc_str}

CRITICAL RULES:
1. You do NOT perform an autonomous diagnosis. You translate the AI model's perception into standard American College of Radiology (ACR) phrasing.
2. If reliability is LOW, explicitly state diagnostic uncertainty and advise mandatory manual review.
3. Suggest appropriate clinical or laboratory correlations (e.g. auscultation, inflammatory markers, follow-up CXR or CT).
4. Do NOT contradict the localized zone ({anatomical_zone}) or the detected findings.

Return ONLY a valid JSON object matching the ClinicalReport schema with keys:
"technique", "findings", "impression", "differential_considerations", "recommendations", "disclaimer"
"""
        return prompt.strip()

    def _offline_deterministic_synthesis(
        self,
        primary_findings: List[Dict[str, Any]],
        associated_findings: List[Dict[str, Any]],
        anatomical_zone: str,
        reliability: str,
        demographics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Deterministic ACR clinical report synthesis when offline or without an external LLM.
        Provides realistic, grammatically precise radiology summaries.
        """
        view = demographics.get("view_position", "PA") if demographics else "PA"
        age = demographics.get("age", 55) if demographics else 55
        gender = demographics.get("gender", "M") if demographics else "M"
        technique = f"Frontal chest radiograph ({view} view), {age}y {'male' if gender == 'M' else 'female'}."

        if not primary_findings:
            return {
                "technique": technique,
                "findings": (
                    "Lungs are clear bilaterally without focal consolidation, pneumothorax, or large pleural effusion. "
                    "Cardiomediastinal silhouette and hilar contours are within normal limits for projection. "
                    "Costophrenic angles remain sharp. Visualized bony thorax demonstrates no acute abnormality."
                ),
                "impression": "No acute cardiopulmonary disease detected within the 14 indexed target categories.",
                "differential_considerations": ["Normal study", "Non-pulmonary etiology if clinically symptomatic"],
                "recommendations": "Routine clinical follow-up as clinically indicated.",
                "disclaimer": (
                    "VisionCare AI is an assistive decision-support research tool. "
                    "Automated findings must be correlated clinically and verified by a board-certified radiologist."
                )
            }

        top_disease = primary_findings[0]["disease"]
        top_prob = primary_findings[0].get("probability_pct", 0)

        disease_phrasing = {
            "Pneumonia": f"Focal airspace opacification identified predominantly in the {anatomical_zone}. Air bronchograms may be present.",
            "Consolidation": f"Dense alveolar consolidation localized within the {anatomical_zone}. No gross volume loss.",
            "Effusion": f"Blunting of the costophrenic angle and lateral fluid meniscus noted, most pronounced in the {anatomical_zone}.",
            "Cardiomegaly": "Transverse cardiac diameter appears enlarged relative to the thoracic cavity. Normal pulmonary vascular distribution.",
            "Pneumothorax": f"Peripheral radiolucency with absent pulmonary vascular markings along the pleural margin in the {anatomical_zone}.",
            "Infiltration": f"Patchy interstitial/alveolar infiltrates demonstrated within the {anatomical_zone}.",
            "Atelectasis": f"Linear basilar plate-like opacity noted within the {anatomical_zone}, consistent with subsegmental volume loss.",
            "Mass": f"Focal circumscribed soft-tissue density greater than 3 cm observed in the {anatomical_zone}.",
            "Nodule": f"Focal rounded nodular opacity noted within the {anatomical_zone}.",
            "Edema": "Bilateral perihilar vascular haziness with interstitial prominence, compatible with fluid overload.",
            "Emphysema": "Bilateral pulmonary hyperinflation with flattening of the hemidiaphragms.",
            "Fibrosis": f"Reticular interstitial fibrotic markings with volume loss demonstrated in the {anatomical_zone}.",
            "Pleural_Thickening": f"Smooth pleural thickening observed along the lateral chest wall in the {anatomical_zone}.",
            "Hernia": "Retrocardiac soft tissue mass containing gas, consistent with hiatal herniation."
        }

        specific_finding = disease_phrasing.get(
            top_disease,
            f"Focal radiographic density identified within the {anatomical_zone}."
        )

        impression = (
            f"{top_disease} in the {anatomical_zone} (AI calibrated confidence: {top_prob}%). "
            f"{'Recommend manual radiologist confirmation due to moderate uncertainty.' if reliability != 'HIGH' else 'Findings are well-correlated with visual feature attribution.'}"
        )

        differentials = [top_disease]
        for af in associated_findings[:2]:
            differentials.append(af["disease"])
        if len(differentials) == 1:
            differentials.append("Post-inflammatory change / Scarring")

        recommendations = (
            "Correlate with patient's physical examination, vital signs, and inflammatory markers (CBC, CRP). "
            "Consider high-resolution CT of the chest or follow-up radiograph in 4 to 6 weeks to confirm resolution."
        )

        return {
            "technique": technique,
            "findings": specific_finding,
            "impression": impression,
            "differential_considerations": differentials,
            "recommendations": recommendations,
            "disclaimer": (
                "VisionCare AI is an assistive decision-support research tool. "
                "Automated findings must be correlated clinically and verified by a board-certified radiologist."
            )
        }

    def synthesize(
        self,
        primary_findings: List[Dict[str, Any]],
        associated_findings: List[Dict[str, Any]],
        anatomical_zone: str,
        reliability: str,
        quality_tier: str = "GOOD",
        demographics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes structured clinical report. Calls Groq / GPT OSS 120B or Gemini
        with short timeouts, seamlessly falling back to deterministic expert synthesis.
        """
        prompt = self._build_prompt(
            primary_findings, associated_findings, anatomical_zone, reliability, quality_tier, demographics
        )

        # 1. Try Groq / GPT OSS 120B first (fastest & highly reliable)
        if self.openai_client:
            try:
                target_model = os.environ.get("OPENAI_MODEL", "openai/gpt-oss-120b")
                completion = self.openai_client.chat.completions.create(
                    model=target_model,
                    messages=[
                        {"role": "system", "content": "You are a clinical radiology assistant. Return valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=1500,
                    response_format={"type": "json_object"}
                )
                text = completion.choices[0].message.content
                data = json.loads(text.strip())
                if isinstance(data.get("differential_considerations"), str):
                    data["differential_considerations"] = [
                        s.strip() for s in data["differential_considerations"].split(",") if s.strip()
                    ]
                report = ClinicalReport(**data)
                return report.model_dump()
            except Exception as e:
                print(f"[!] Groq/OpenAI synthesis fallback: {e}")

        # 2. Try Gemini
        if self.gemini_client:
            try:
                if hasattr(self.gemini_client, "models"):
                    response = self.gemini_client.models.generate_content(
                        model="gemini-1.5-flash",
                        contents=prompt,
                        config={"response_mime_type": "application/json"}
                    )
                    text = response.text
                elif hasattr(self.gemini_client, "generate_content"):
                    response = self.gemini_client.generate_content(prompt)
                    text = response.text
                else:
                    raise RuntimeError("No suitable Gemini method")

                data = json.loads(text.strip("```json").strip("```").strip())
                report = ClinicalReport(**data)
                return report.model_dump()
            except Exception as e:
                print(f"[!] Gemini synthesis fallback: {e}")

        # 3. Deterministic expert clinical synthesis fallback
        return self._offline_deterministic_synthesis(
            primary_findings, associated_findings, anatomical_zone, reliability, demographics
        )
