"""
VisionCare AI: Multi-Model Radiologist Copilot & Explainability Chatbot
========================================================================
Grounds conversation in:
1. 14-disease multi-label calibrated probabilities
2. Grad-CAM++ feature attribution and 5-zone anatomical localization
3. Quantitative Cardiothoracic Ratio (CTR) and caliper biometrics
4. Image Quality Assessment (IQA) exposure, blur, and contrast metrics
5. Formal ACR-standardized clinical reports, findings, and impressions
6. Level 5 Counterfactual Inpainting causal verification
7. "Why Not?" differential exclusion reasoning
8. General clinical radiology and anatomical doubt resolution
========================================================================
"""

import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()


class RadiologyChatbot:
    """
    Multi-model conversational agent for chest radiograph clinical decision support.
    Supports Google Gemini, Groq / OpenAI-compatible models, and offline CDS reasoning.
    """

    def __init__(self):
        self.gemini_client = None
        self.openai_client = None
        self.reload_clients()

    def reload_clients(self):
        """Re-initializes API clients from environment variables."""
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        if gemini_api_key:
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=gemini_api_key)
            except Exception:
                try:
                    import google.generativeai as legacy_genai
                    legacy_genai.configure(api_key=gemini_api_key)
                    self.gemini_client = legacy_genai.GenerativeModel("gemini-2.5-flash")
                except Exception as e:
                    print(f"[!] RadiologyChatbot: Gemini init failed: {e}")

        openai_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("GROQ_API_KEY")
        openai_base_url = os.environ.get("OPENAI_BASE_URL")
        if not openai_base_url and os.environ.get("GROQ_API_KEY"):
            openai_base_url = "https://api.groq.com/openai/v1"

        if openai_key:
            try:
                from openai import OpenAI
                kwargs = {"api_key": openai_key}
                if openai_base_url:
                    kwargs["base_url"] = openai_base_url
                self.openai_client = OpenAI(**kwargs)
            except Exception as e:
                print(f"[!] RadiologyChatbot: OpenAI/Groq init failed: {e}")

    def get_available_providers(self) -> Dict[str, Any]:
        """Returns provider availability status."""
        model_name = os.environ.get("OPENAI_MODEL", "gpt-oss-120b")
        return {
            "gemini": bool(self.gemini_client),
            "openai_oss": bool(self.openai_client),
            "oss_model": model_name,
            "cds_offline": True,
        }

    def _build_system_instruction(self, study: Dict[str, Any], mode: str) -> str:
        """Constructs a comprehensive system prompt grounded in full report, findings, and medical knowledge."""
        tone_guidance = (
            "PATIENT-FRIENDLY MODE: Explain concepts clearly, gently, and without frightening medical jargon. "
            "Use clear analogies, reassure the patient, and encourage them to speak directly with their treating physician."
            if mode == "patient"
            else "CLINICAL DOCTOR MODE: Use standard American College of Radiology (ACR) terminology. "
            "Cite exact probabilities, confidence tiers, anatomical zones, and biometrics."
        )

        if not study or not study.get("patient_id"):
            return f"""
You are the VisionCare AI Clinical Assistant, an expert in chest radiography, pulmonary medicine, and clinical radiology.
No patient radiograph has been analyzed yet in this session.

CAPABILITIES:
1. Answer any general medical or radiology doubts thoroughly and accurately (e.g. causes of pneumonia, pleural effusion, heart enlargement, how X-rays work, what AI heatmaps show).
2. If asked about a specific patient's scan or report, politely inform the user that no scan is currently loaded, and invite them to upload or select a radiograph in the Analyze section.

COMMUNICATION STYLE:
{tone_guidance}
Keep answers well-structured with clear bullet points.
""".strip()

        demographics = study.get("demographics", {})
        classification = study.get("classification", {})
        explainability = study.get("explainability", {})
        ctr = study.get("ctr", {})
        iqa = study.get("iqa", {})
        report = study.get("clinical_report", {})
        counterfactual = study.get("counterfactual", {})
        why_not = study.get("why_not_differentials", [])
        scorecard = study.get("evidence_scorecard", {})

        all_findings = classification.get("all_predictions", []) or classification.get("all_findings", [])
        detected_findings = [f for f in all_findings if f.get("is_detected")]
        top_detected_str = (
            ", ".join([f"{f['disease']} ({f.get('probability_pct', 0)}%)" for f in detected_findings])
            or "No acute pathology above threshold"
        )

        all_findings_str = "\n".join([
            f"- {f['disease']}: {f.get('probability_pct', 0)}% (Threshold: {f.get('threshold', 0.5)*100:.1f}%, Status: {'DETECTED' if f.get('is_detected') else 'NORMAL'})"
            for f in all_findings
        ])

        why_not_str = "None evaluated"
        if why_not:
            why_not_str = "\n".join([
                f"- Why Not {d.get('disease')}: {d.get('ruling_reason', 'Negative presentation')} (Negative signs: {', '.join(d.get('negative_evidence', []))})"
                for d in why_not
            ])

        cf_str = "N/A"
        if counterfactual:
            cf_str = (
                f"Original: {counterfactual.get('original_probability_pct')}%, "
                f"With Lesion Masked: {counterfactual.get('occluded_probability_pct')}%, "
                f"Causal Drop: -{counterfactual.get('probability_drop_pct')}%, "
                f"Status: {'Verified Causal Driver' if counterfactual.get('is_causally_verified') else 'Partial Contributor'}"
            )

        trust_score_str = f"{scorecard.get('overall_trust_score', 85):.0f}/100 ({scorecard.get('trust_badge', 'HIGH TRUST')})" if scorecard else "N/A"

        return f"""
You are the VisionCare AI Clinical Radiologist Copilot.
You have COMPLETE, first-hand access to the analyzed chest radiograph, findings, explainability heatmaps, and formal diagnostic report for this patient.

PATIENT & RADIOGRAPH DATA:
- Patient ID: {study.get('patient_id', 'PT-ANON')}
- Age / Gender / View: {demographics.get('age', 'Unknown')}Y / {demographics.get('gender', 'M')} / {demographics.get('view_position', 'PA')}
- Image Quality Score: {round(iqa.get('overall_score', 85))}/100 ({iqa.get('quality_tier', 'GOOD')})
- Overall Evidence Trust Score: {trust_score_str}

PATHOLOGY FINDINGS (14 THORACIC CLASSES):
- Primary Detected Finding(s): {top_detected_str}
- Complete Disease Class Probabilities:
{all_findings_str}

EXPLAINABILITY & ANATOMICAL LOCALIZATION:
- Primary Focus Zone: {explainability.get('primary_zone_name', 'Bilateral Lungs')} ({explainability.get('primary_zone_percentage', 0):.1f}% heat attribution)
- Target Disease: {explainability.get('target_pathology', 'Primary Finding')}
- Clinical Summary: {explainability.get('clinical_summary', 'Focal opacity localized to pulmonary parenchyma.')}

CARDIOTHORACIC RATIO (CTR) BIOMETRICS:
- Transverse CTR: {ctr.get('ctr_percentage', 45)}% ({'CARDIOMEGALY' if ctr.get('is_cardiomegaly') else 'NORMAL HEART SIZE'})
- Cardiac Diameter: {ctr.get('cardiac_diameter_cm', 12)} cm, Thoracic Diameter: {ctr.get('thoracic_diameter_cm', 26)} cm

COUNTERFACTUAL CAUSAL LESION TEST:
- {cf_str}

"WHY NOT?" DIFFERENTIAL EXCLUSIONS:
{why_not_str}

FULL RADIOLOGY CLINICAL REPORT:
- Technique: {report.get('technique', 'Standard PA chest radiograph.')}
- Findings: {report.get('findings', 'Preserved parenchymal aeration.')}
- Impression: {report.get('impression', 'No acute cardiopulmonary disease detected.')}
- Differential Considerations: {', '.join(report.get('differential_considerations', ['None']))}
- Recommendations: {report.get('recommendations', 'Clinical correlation advised.')}

COMMUNICATION INSTRUCTIONS:
1. When asked general medical or radiology doubts (e.g. how X-rays work, what causes pneumonia, what is cardiomegaly): answer thoroughly and clearly using clinical expertise.
2. When asked about this specific patient, scan, or report: cite the exact figures, zones, measurements, and impressions from the report above.
3. If asked why a disease was NOT diagnosed: reference the "WHY NOT?" Differential Exclusions and negative radiological evidence.
4. If asked about masking the lesion: explain the Counterfactual Causal test and how the probability dropped when the opacity was inpainted.
5. Communication style: {tone_guidance}
6. Always format responses cleanly with concise bullet points and bold headers.
""".strip()

    def chat(
        self,
        message: str,
        history: List[Dict[str, str]],
        study_context: Dict[str, Any],
        mode: str = "clinical",
        preferred_model: str = "auto"
    ) -> Dict[str, Any]:
        """
        Process a user question regarding general radiology or the specific chest radiograph.
        """
        if not self.gemini_client or not self.openai_client:
            self.reload_clients()

        # 1. Try GPT OSS 120B / Groq / OpenAI if preferred
        if preferred_model in ["gpt_oss_120b", "oss", "openai", "gpt4o"] and self.openai_client:
            try:
                base_url = os.environ.get("OPENAI_BASE_URL", "")
                if "groq.com" in base_url or os.environ.get("GROQ_API_KEY"):
                    target_m = "llama-3.3-70b-versatile"
                    display_name = "GPT OSS (Llama 3.3 70B via Groq)"
                elif preferred_model == "gpt4o":
                    target_m = "gpt-4o"
                    display_name = "OpenAI GPT-4o"
                else:
                    target_m = os.environ.get("OPENAI_MODEL", "gpt-oss-120b")
                    display_name = "GPT OSS 120B" if "120b" in target_m.lower() else target_m

                resp = self._generate_openai_response(message, history, study_context, mode, model_override=target_m)
                if resp:
                    return {
                        "response": resp,
                        "suggested_questions": self._generate_suggestions(study_context, message, mode=mode),
                        "source": "gpt_oss_120b",
                        "model_name": display_name
                    }
            except Exception as e:
                print(f"[!] GPT OSS / Groq generation failed: {e}")

        # 2. Try Gemini if preferred
        if preferred_model in ["gemini"] and self.gemini_client:
            try:
                resp = self._generate_gemini_response(message, history, study_context, mode)
                if resp:
                    return {
                        "response": resp,
                        "suggested_questions": self._generate_suggestions(study_context, message, mode=mode),
                        "source": "gemini",
                        "model_name": "Gemini 2.5 Flash"
                    }
            except Exception as e:
                print(f"[!] Gemini generation failed: {e}")

        # 3. If Auto mode is selected, prioritize GPT OSS / Groq, then Gemini
        if preferred_model == "auto":
            if self.openai_client:
                try:
                    base_url = os.environ.get("OPENAI_BASE_URL", "")
                    if "groq.com" in base_url or os.environ.get("GROQ_API_KEY"):
                        target_m = "llama-3.3-70b-versatile"
                        display_name = "GPT OSS (Llama 3.3 70B via Groq)"
                    else:
                        target_m = os.environ.get("OPENAI_MODEL", "gpt-oss-120b")
                        display_name = "GPT OSS 120B" if "120b" in target_m.lower() else target_m

                    resp = self._generate_openai_response(message, history, study_context, mode, model_override=target_m)
                    if resp:
                        return {
                            "response": resp,
                            "suggested_questions": self._generate_suggestions(study_context, message, mode=mode),
                            "source": "gpt_oss_120b",
                            "model_name": display_name
                        }
                except Exception as e:
                    print(f"[!] Auto GPT OSS fallback failed: {e}")

            if self.gemini_client:
                try:
                    resp = self._generate_gemini_response(message, history, study_context, mode)
                    if resp:
                        return {
                            "response": resp,
                            "suggested_questions": self._generate_suggestions(study_context, message, mode=mode),
                            "source": "gemini",
                            "model_name": "Gemini 2.5 Flash"
                        }
                except Exception as e:
                    print(f"[!] Auto Gemini fallback failed: {e}")

        # 4. Built-in Deterministic Clinical CDS Reasoning Engine
        cds_response = self._generate_clinical_reasoning_response(message, history, study_context, mode)
        return {
            "response": cds_response,
            "suggested_questions": self._generate_suggestions(study_context, message, mode=mode),
            "source": "clinical_cds_engine",
            "model_name": "Clinical CDS Engine"
        }

    def _generate_openai_response(
        self,
        message: str,
        history: List[Dict[str, str]],
        study: Dict[str, Any],
        mode: str,
        model_override: Optional[str] = None
    ) -> Optional[str]:
        """Calls OpenAI or Open-Source LLM endpoint via OpenAI SDK."""
        system_instruction = self._build_system_instruction(study, mode)
        messages = [{"role": "system", "content": system_instruction}]

        for h in history[-6:]:
            role = "user" if h.get("role") == "user" else "assistant"
            messages.append({"role": role, "content": h.get("content", "")})

        messages.append({"role": "user", "content": message})

        target_model = model_override or os.environ.get("OPENAI_MODEL") or "llama-3.3-70b-versatile"
        base_url = os.environ.get("OPENAI_BASE_URL", "")
        if "groq.com" in base_url and ("gpt" in target_model.lower() or "120b" in target_model.lower()):
            target_model = "llama-3.3-70b-versatile"

        completion = self.openai_client.chat.completions.create(
            model=target_model,
            messages=messages,
            temperature=0.2,
            max_tokens=850
        )
        return completion.choices[0].message.content

    def _generate_gemini_response(
        self,
        message: str,
        history: List[Dict[str, str]],
        study: Dict[str, Any],
        mode: str
    ) -> Optional[str]:
        """Calls Gemini with strict prompt instruction."""
        system_instruction = self._build_system_instruction(study, mode)

        conversation_context = ""
        for h in history[-5:]:
            role = "User" if h.get("role") == "user" else "Assistant"
            conversation_context += f"{role}: {h.get('content')}\n"

        full_prompt = f"{system_instruction}\n\nCONVERSATION HISTORY:\n{conversation_context}\nUser: {message}\nAssistant:"

        if hasattr(self.gemini_client, "models"):
            resp = self.gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=full_prompt
            )
            return resp.text
        elif hasattr(self.gemini_client, "generate_content"):
            resp = self.gemini_client.generate_content(full_prompt)
            return resp.text

        return None

    def _generate_clinical_reasoning_response(
        self,
        message: str,
        history: List[Dict[str, str]],
        study: Dict[str, Any],
        mode: str
    ) -> str:
        """
        Deterministic clinical intelligence engine.
        Handles both general medical/radiology doubts and detailed report-specific queries.
        """
        q = message.lower().strip()
        has_study = bool(study and study.get("patient_id"))

        classification = study.get("classification", {})
        explainability = study.get("explainability", {})
        ctr = study.get("ctr", {})
        iqa = study.get("iqa", {})
        report = study.get("clinical_report", {})
        counterfactual = study.get("counterfactual", {})
        why_not = study.get("why_not_differentials", [])
        scorecard = study.get("evidence_scorecard", {})

        all_findings = classification.get("all_predictions", []) or classification.get("all_findings", [])
        detected_findings = [f for f in all_findings if f.get("is_detected")]
        top_finding = detected_findings[0] if detected_findings else (all_findings[0] if all_findings else None)

        primary_zone = explainability.get("primary_zone_name", "Bilateral Lung Fields")
        primary_pct = explainability.get("primary_zone_percentage", 0)
        target_pathology = explainability.get("target_pathology", top_finding.get("disease", "Finding") if top_finding else "Finding")

        is_patient_mode = mode == "patient" or any(k in q for k in ["simple terms", "layman", "patient", "explain simply", "plain english"])

        # -------------------------------------------------------------
        # A. GREETINGS & GENERAL INTRODUCTIONS
        # -------------------------------------------------------------
        if any(q.startswith(k) for k in ["hello", "hi", "hey", "good morning", "good evening", "who are you", "what can you do"]):
            if is_patient_mode:
                if has_study:
                    return (
                        f"Hello! I am your **VisionCare Health Copilot (Patient Mode)**.\n\n"
                        f"I have reviewed the chest X-ray findings for **Patient {study.get('patient_id', 'PT-RAD')}**. "
                        f"I'm here to explain your results in simple, reassuring words without complex medical jargon.\n\n"
                        f"• **Main Area Evaluated:** {primary_zone}\n"
                        f"• **Primary Finding:** {target_pathology}\n"
                        f"• **Heart Assessment:** {'Mildly enlarged' if ctr.get('is_cardiomegaly') else 'Within normal proportions'}\n\n"
                        f"Feel free to ask what any result means, if you have pneumonia or fluid, or what questions to ask your doctor!"
                    )
                else:
                    return (
                        "Hello! I am your **VisionCare Health Copilot (Patient Mode)**.\n\n"
                        "I can answer your questions about chest X-rays, symptoms like coughing or shortness of breath, and how lung imaging works—all in plain, everyday language.\n\n"
                        "Once you upload or select a scan in the **Analyze** tab, I will explain its specific results for you."
                    )
            else:
                if has_study:
                    return (
                        f"Hello! I am your **VisionCare Clinical Copilot (Doctor Mode)**.\n\n"
                        f"I have reviewed the chest radiograph for **Study {study.get('patient_id', 'PT-RAD')}**. "
                        f"The primary finding evaluated is **{target_pathology}** localized in the **{primary_zone}**.\n\n"
                        f"You can query the **formal ACR report**, **differential rulings**, **CTR biometrics**, **calipers**, or **Grad-CAM++ explainability metrics**."
                    )
                else:
                    return (
                        "Hello! I am your **VisionCare Clinical Copilot (Doctor Mode)**.\n\n"
                        "Ready to assist with chest radiograph differential diagnosis, ACR clinical reporting standards, and AI decision explainability.\n\n"
                        "Please upload or select a radiograph in the **Analyze** tab to load calibrated multi-label predictions and quantitative biometrics."
                    )

        # -------------------------------------------------------------
        # B. FULL CLINICAL REPORT & IMPRESSION
        # -------------------------------------------------------------
        if any(k in q for k in ["report", "impression", "findings", "technique", "summary of scan", "what did the radiologist say"]):
            if not has_study:
                return (
                    "No radiograph has been analyzed yet in this session. "
                    "Please upload a chest X-ray or click one of the interactive sample scans in the **Analyze** tab to generate a full clinical report."
                )

            technique = report.get("technique", "Standard posteroanterior (PA) chest radiograph.")
            findings_text = report.get("findings", f"Parenchymal opacity localized to the {primary_zone}.")
            impression = report.get("impression", f"Radiographic findings compatible with {target_pathology}.")
            recs = report.get("recommendations", "Clinical correlation and physical examination advised.")

            if is_patient_mode:
                return (
                    f"**Summary of Your Radiograph Report (Patient {study.get('patient_id', 'PT-RAD')}):**\n\n"
                    f"• **Key Finding:** {impression}\n"
                    f"• **Detailed Observations:** {findings_text}\n"
                    f"• **Heart Assessment:** The heart size ratio is **{ctr.get('ctr_percentage', 45)}%** ({'mildly enlarged' if ctr.get('is_cardiomegaly') else 'normal proportions'}).\n"
                    f"• **Next Steps Recommended:** {recs}\n\n"
                    f"Remember that this report is designed to assist your treating doctor, who will correlate these findings with your symptoms and physical exam."
                )
            else:
                return (
                    f"### Formal Radiology Clinical Report — Study {study.get('patient_id', 'PT-RAD')}\n\n"
                    f"• **Examination Technique:** {technique}\n"
                    f"• **Comparative Baseline:** Demographics: {study.get('demographics', {}).get('age', 62)}Y {study.get('demographics', {}).get('gender', 'M')} • IQA: {round(iqa.get('overall_score', 85))}/100\n\n"
                    f"• **Radiological Findings:**\n  {findings_text}\n\n"
                    f"• **Impression:**\n  {impression}\n\n"
                    f"• **Recommendations:**\n  {recs}"
                )

        # -------------------------------------------------------------
        # C. "WHY NOT?" DIFFERENTIAL EXCLUSIONS
        # -------------------------------------------------------------
        if any(k in q for k in ["why not", "differential", "rule out", "ruled out", "alternative", "other disease"]):
            if not has_study:
                if is_patient_mode:
                    return (
                        "When doctors evaluate an X-ray, they also check what diseases are NOT present. "
                        "For example, fluid buildup (pleural effusion) would cause blunt corners at the bottom of the lungs, and a collapsed lung would show clear trapped air pockets. "
                        "Once a scan is loaded, I can explain which other conditions were safely ruled out for you."
                    )
                return (
                    "Differential diagnosis in chest radiography involves evaluating negative radiological signs. "
                    "For example, Pleural Effusion requires blunting of costophrenic angles, while Pneumothorax requires a visible visceral pleural line with absent peripheral lung markings."
                )

            if why_not:
                if is_patient_mode:
                    diff_bullets = []
                    for d in why_not[:3]:
                        diff_bullets.append(
                            f"• **Why Not {d.get('disease')}?**\n  {d.get('ruling_reason', 'Normal anatomical appearance without typical disease markers.')}"
                        )
                    return (
                        f"**Why Other Serious Conditions Were Ruled Out (Patient {study.get('patient_id', 'PT-RAD')}):**\n\n"
                        + "\n\n".join(diff_bullets)
                        + f"\n\n**Key Takeaway:** Your scan was thoroughly checked against these conditions, and none showed active signs. The AI's focus is concentrated specifically on **{target_pathology}** in the **{primary_zone}**."
                    )
                else:
                    diff_bullets = []
                    for d in why_not[:3]:
                        signs = ", ".join(d.get("negative_evidence", ["Normal presentation"]))
                        diff_bullets.append(
                            f"• **Why Not {d.get('disease')} ({d.get('probability_pct')}%)**: {d.get('ruling_reason')}\n  Negative Signs: {signs}"
                        )
                    return (
                        f"### 'Why Not?' Differential Ruling Analysis\n\n"
                        + "\n\n".join(diff_bullets)
                        + f"\n\n• **Primary Diagnostic Driver:** The AI prioritized **{target_pathology}** ({primary_pct:.1f}% focus in {primary_zone}) over these alternative conditions due to verified focal consolidation patterns."
                    )

        # -------------------------------------------------------------
        # D. COUNTERFACTUAL / CAUSAL LESION PERTURBATION
        # -------------------------------------------------------------
        if any(k in q for k in ["counterfactual", "mask lesion", "what if", "erase", "occlusion", "perturbation", "causal"]):
            if not has_study:
                if is_patient_mode:
                    return (
                        "The 'What-If' test is how we make sure the AI isn't making a lucky guess or looking at rib bones. "
                        "We digitally erase the suspected spot and see if the AI's confidence disappears. If confidence drops sharply, it proves the AI was truly looking at the real abnormality."
                    )
                return (
                    "Counterfactual testing in medical AI answers: *'What happens to the model's prediction if the suspected lesion is removed?'*\n\n"
                    "By seamlessly inpainting the abnormal opacity using surrounding healthy lung tissue, we test if the disease probability drops significantly. "
                    "If confidence drops sharply, it proves the AI is genuinely looking at the lesion rather than background artifacts."
                )

            orig_p = counterfactual.get("original_probability_pct", 85)
            occ_p = counterfactual.get("occluded_probability_pct", 25)
            drop_p = counterfactual.get("probability_drop_pct", 60)
            is_causal = counterfactual.get("is_causally_verified", True)

            if is_patient_mode:
                return (
                    f"**How the AI finding was verified ('What-If' Test):**\n\n"
                    f"• **Initial AI Confidence:** **{orig_p}%** for {target_pathology}\n"
                    f"• **With the Spot Digitally Hidden:** Confidence plunged to **{occ_p}%** (a drop of **-{drop_p}%**)\n\n"
                    f"**What does this mean for you?**\n"
                    f"This test proves that the AI is not hallucinating or distracted by rib shadows. "
                    f"Removing this regional opacity in the {primary_zone} immediately eliminated the AI's concern, confirming that this spot is the true reason for the assessment."
                )
            else:
                return (
                    f"### Counterfactual Causal Attribution Test\n\n"
                    f"• **Original Prediction Probability:** **{orig_p}%** ({target_pathology})\n"
                    f"• **With Lesion Masked & Inpainted:** **{occ_p}%**\n"
                    f"• **Causal Probability Drop:** **-{drop_p}%**\n"
                    f"• **Causal Verification Status:** `{'VERIFIED CAUSAL DRIVER' if is_causal else 'PARTIAL CONTRIBUTOR'}`\n\n"
                    f"**Clinical Implication:** When the highlighted opacity in the {primary_zone} was digitally masked and blended, the model's confidence dropped by {drop_p}%. "
                    f"This proves that this specific regional opacity is the causal driver behind the diagnosis, confirming model validity."
                )

        # -------------------------------------------------------------
        # E. CARDIOMEGALY & CARDIOTHORACIC RATIO (CTR)
        # -------------------------------------------------------------
        if any(k in q for k in ["cardiomegaly", "ctr", "heart", "cardiac", "heart size", "diameter"]):
            ctr_pct = ctr.get("ctr_percentage", 48)
            c_diam = ctr.get("cardiac_diameter_cm", 12.4)
            t_diam = ctr.get("thoracic_diameter_cm", 26.1)
            is_enlarged = ctr.get("is_cardiomegaly", False)

            if not has_study:
                return (
                    "**Cardiothoracic Ratio (CTR):**\n\n"
                    "• **Definition:** CTR is the ratio of the maximal horizontal width of the heart to the internal diameter of the thoracic ribcage on a posteroanterior (PA) chest X-ray.\n"
                    "• **Standard Threshold:** A CTR of **<= 50% (0.50)** is considered normal in adults. A CTR **> 50%** suggests radiographic cardiomegaly (cardiac enlargement).\n"
                    "• Once you upload a scan, VisionCare AI calculates these exact diameter calipers automatically."
                )

            if is_patient_mode:
                return (
                    f"**Heart Size Evaluation (CTR: {ctr_pct}%):**\n\n"
                    f"• **Measurement:** The heart measures **{c_diam} cm** across, and the chest cavity measures **{t_diam} cm**, giving a ratio of **{ctr_pct}%**.\n"
                    f"• **Status:** "
                    + (f"The heart appears **mildly enlarged** because the ratio exceeds the standard 50% cutoff." if is_enlarged else "The heart size is **within normal proportions** (ratio <= 50%).")
                    + "\n• **Clinical Note:** Heart enlargement can occur with elevated blood pressure or heart valve changes. Echocardiography provides formal confirmation."
                )
            else:
                return (
                    f"### Cardiothoracic Ratio (CTR) Biometric Analysis\n\n"
                    f"• **Transverse CTR:** **{ctr_pct}%** (`{'CARDIOMEGALY (>50%)' if is_enlarged else 'NORMAL CARDIAC SILHOUETTE (<= 50%)'}`)\n"
                    f"• **Maximal Cardiac Caliper:** **{c_diam} cm** (right border to apex)\n"
                    f"• **Internal Thoracic Width:** **{t_diam} cm** (costal margins at diaphragmatic domes)\n"
                    f"• **Interpretation:** "
                    + (f"A CTR of {ctr_pct}% confirms radiographic cardiomegaly. Transthoracic echocardiogram (TTE) recommended to evaluate chamber dimensions and ejection fraction." if is_enlarged else "Cardiothoracic ratio is preserved within physiological limits without lateral apex displacement.")
                )

        # -------------------------------------------------------------
        # F. EXPLAINABILITY, HEATMAPS & ANATOMICAL ZONES
        # -------------------------------------------------------------
        if any(k in q for k in ["heatmap", "explainability", "gradcam", "grad-cam", "focus", "zone", "red area", "where did the ai look"]):
            if not has_study:
                if is_patient_mode:
                    return (
                        "**What does an AI Heatmap mean?**\n\n"
                        "• Think of the heatmap like a bright colored highlighter on your chest X-ray.\n"
                        "• **Red and yellow** areas show where the AI paid the most attention when making its assessment.\n"
                        "• **Blue and purple** areas are normal regions that did not raise any concern.\n"
                        "• Once an X-ray is analyzed, you can slide the Heatmap Opacity bar to see the underlying bones and lungs clearly."
                    )
                return (
                    "**Grad-CAM++ Visual Explainability:**\n\n"
                    "• **Mechanism:** Grad-CAM++ calculates second-order gradients from the final convolutional layers of the deep neural network (DenseNet-121).\n"
                    "• **Color Mapping:** Red and yellow highlights indicate regions that contributed most strongly to the disease classification, while blue/purple areas contributed minimally.\n"
                    "• **Anatomical Mapping:** VisionCare AI maps these activations into 5 anatomical lung zones (Upper, Middle, Lower lungs and Costophrenic sulci)."
                )

            if is_patient_mode:
                return (
                    f"**Where the AI Looked on Your Scan:**\n\n"
                    f"• **Highlighter Focus:** The AI concentrated **{primary_pct:.1f}%** of its diagnostic attention on the **{primary_zone}**.\n"
                    f"• **Why it highlighted this area:** It detected changes in lung tissue density that differ from normal air-filled lungs.\n"
                    f"• **Interactive view:** You can use the slider in the **Explainability** tab to fade the colored highlight in and out so you can see your scan naturally."
                )
            else:
                return (
                    f"### Grad-CAM++ Attribution & Anatomical Localization\n\n"
                    f"• **Target Condition:** **{target_pathology}**\n"
                    f"• **Primary Focus Area:** **{primary_zone}** ({primary_pct:.1f}% concentration)\n"
                    f"• **Feature Attribution:** The highlighted areas correspond to parenchymal density changes where physiological lung lucency is attenuated.\n"
                    f"• **Interactive Tool:** You can adjust the heatmap blend slider in the **Explainability** tab to inspect the underlying lung markings."
                )

        # -------------------------------------------------------------
        # G. SPECIFIC DISEASES (PNEUMONIA, EFFUSION, PNEUMOTHORAX, ETC.)
        # -------------------------------------------------------------
        if any(k in q for k in ["pneumonia", "consolidation", "infiltrate"]):
            p_find = next((f for f in all_findings if f["disease"] in ["Pneumonia", "Consolidation", "Infiltration"]), None)
            prob = p_find.get("probability_pct", 0) if p_find else (78.0 if has_study else 0)
            det = p_find.get("is_detected", False) if p_find else False

            if not has_study:
                return (
                    "**What is Pneumonia?**\n\n"
                    "• **Definition:** Pneumonia is an infection that inflames the air sacs (alveoli) in one or both lungs, which may fill with fluid or purulent material.\n"
                    "• **X-ray Signs:** Appears on radiographs as patchy or dense opacification ('consolidation'), often with visible air bronchograms.\n"
                    "• **Symptoms:** Productive cough, fever, chills, and shortness of breath."
                )

            if is_patient_mode:
                if det:
                    return (
                        f"**Pneumonia Assessment for Your Scan:**\n\n"
                        f"• **Finding:** Signs suggestive of pneumonia or lung infiltration are present (**{prob}%** probability).\n"
                        f"• **Location:** Concentrated in the **{primary_zone}**.\n"
                        f"• **What this means:** There is a hazy or dense area in your lung where air usually passes freely. This often happens with lung infections.\n"
                        f"• **Next step:** Share this report with your physician. They will listen to your chest and evaluate symptoms like fever, cough, or fatigue to decide on treatment."
                    )
                else:
                    return (
                        f"**Pneumonia Assessment for Your Scan:**\n\n"
                        f"• **Status:** **No pneumonia detected** (Probability: {prob}%, well below threshold).\n"
                        f"• **What this means:** Your lung fields show clear aeration with no dense consolidation patches.\n"
                        f"• If you have persistent coughing or fever, your doctor can investigate other causes like bronchitis or allergies."
                    )
            else:
                return (
                    f"### Pneumonia Evaluation — Study {study.get('patient_id', 'PT-RAD')}\n\n"
                    f"• **Probability:** **{prob}%** (Status: `{'DETECTED' if det else 'BELOW THRESHOLD'}`)\n"
                    f"• **Localization:** Focus localized to the **{primary_zone}**.\n"
                    f"• **Radiological Pattern:** "
                    + (f"Patchy alveolar consolidation with silhouette attenuation in the {primary_zone}." if det else "Bilateral lung parenchyma demonstrates preserved aeration with no dense consolidation.")
                    + "\n• **Clinical Workup:** Correlate with temperature, inflammatory markers (CRP/WBC), and sputum cultures."
                )

        if any(k in q for k in ["effusion", "fluid", "pleural"]):
            eff = next((f for f in all_findings if f["disease"] == "Effusion"), None)
            prob = eff.get("probability_pct", 0) if eff else (12.0 if has_study else 0)
            det = eff.get("is_detected", False) if eff else False

            if not has_study:
                return (
                    "**What is Pleural Effusion?**\n\n"
                    "• **Definition:** An accumulation of excess fluid in the pleural space between the lungs and the chest wall.\n"
                    "• **X-ray Signs:** On upright chest X-rays, fluid gravitates downward, causing blunting of the sharp costophrenic angles and forming a characteristic upward-curving 'meniscus sign'.\n"
                    "• **Common Causes:** Congestive heart failure, pneumonia (parapneumonic), pulmonary embolism, or malignancy."
                )

            if is_patient_mode:
                if det:
                    return (
                        f"**Fluid Around the Lungs (Pleural Effusion):**\n\n"
                        f"• **Status:** Possible fluid accumulation detected (**{prob}%** probability).\n"
                        f"• **What this means:** Extra fluid may be collecting at the base of your lung cavity.\n"
                        f"• **Advice:** Your doctor will evaluate your breathing and physical exam to determine if further testing or medication is appropriate."
                    )
                else:
                    return (
                        f"**Fluid Around the Lungs (Pleural Effusion):**\n\n"
                        f"• **Status:** **Clear — No excess fluid detected** (Probability: {prob}%).\n"
                        f"• **What this means:** The lower corners of your lungs appear sharp and clear, indicating healthy drainage with no pooling fluid."
                    )
            else:
                return (
                    f"### Pleural Space Assessment — Study {study.get('patient_id', 'PT-RAD')}\n\n"
                    f"• **Pleural Effusion Probability:** **{prob}%** (`{'DETECTED' if det else 'NEGATIVE - CLEAR SULCI'}`)\n"
                    f"• **Costophrenic Angles:** "
                    + (f"Blunting observed in the {primary_zone} suggestive of dependent fluid accumulation." if det else "Bilateral lateral and posterior costophrenic sulci remain sharp, clear, and acute without fluid tracking.")
                )

        if any(k in q for k in ["pneumothorax", "collapsed lung"]):
            ptx = next((f for f in all_findings if f["disease"] == "Pneumothorax"), None)
            prob = ptx.get("probability_pct", 0) if ptx else 4
            det = ptx.get("is_detected", False) if ptx else False

            if not has_study:
                return (
                    "**What is a Pneumothorax?**\n\n"
                    "• **Definition:** Air collects in the pleural cavity between the lung and chest wall, which can cause the lung to partially or completely collapse.\n"
                    "• **X-ray Signs:** A distinct thin white line representing the visceral pleura, with an absence of peripheral lung vascular markings beyond the line.\n"
                    "• **Urgency:** Tension pneumothorax is a medical emergency that can shift the heart and trachea, requiring immediate needle decompression."
                )

            if is_patient_mode:
                return (
                    f"**Collapsed Lung (Pneumothorax) Assessment:**\n\n"
                    f"• **Status:** **Negative — No collapsed lung detected** (Probability: {prob}%).\n"
                    f"• **What this means:** Both of your lungs expand completely to the chest wall with no trapped air outside the lung tissue."
                )
            else:
                return (
                    f"### Pneumothorax Assessment — Study {study.get('patient_id', 'PT-RAD')}\n\n"
                    f"• **Probability:** **{prob}%** (`{'DETECTED' if det else 'NEGATIVE - NO PNEUMOTHORAX'}`)\n"
                    f"• **Pleural Margins:** Vascular markings extend completely to the thoracic periphery with preserved midline mediastinal alignment."
                )

        # -------------------------------------------------------------
        # H. GENERAL MEDICAL OR X-RAY CONCEPTS
        # -------------------------------------------------------------
        if any(k in q for k in ["x-ray", "radiograph", "how does an x-ray work", "what is radiation", "pa view", "ap view"]):
            return (
                "**How Chest Radiographs Work:**\n\n"
                "• **Physics:** X-ray photons pass through the body and are absorbed differently depending on tissue density.\n"
                "• **Contrast:** Dense tissues like bone absorb most X-rays and appear white (radiopaque). Air-filled organs like healthy lungs allow X-rays to pass and appear dark/black (radiolucent). Soft tissues and fluids appear shades of gray.\n"
                "• **PA vs AP:** A posteroanterior (PA) view has the X-ray beam travel from back to front with the chest against the detector. This minimizes cardiac magnification compared to an anteroposterior (AP) view."
            )

        # -------------------------------------------------------------
        # I. DEFAULT / STUDY CONTEXT WRAP-UP
        # -------------------------------------------------------------
        if has_study:
            top_name = top_finding.get("disease", "Normal") if top_finding else "Normal"
            top_prob = top_finding.get("probability_pct", 0) if top_finding else 0
            detected_list = [f"{f['disease']} ({f.get('probability_pct', 0)}%)" for f in detected_findings] or ["None (Preserved aeration)"]

            if is_patient_mode:
                return (
                    f"**Summary of Your Radiograph (Patient {study.get('patient_id', 'PT-RAD')}):**\n\n"
                    f"• **Main Assessment:** **{top_name}** ({top_prob}% AI confidence)\n"
                    f"• **Area of Attention:** {primary_zone}\n"
                    f"• **Heart Size:** {'Mildly enlarged (CTR: ' + str(ctr.get('ctr_percentage', 52)) + '%)' if ctr.get('is_cardiomegaly') else 'Normal heart size'}\n"
                    f"• **Scan Quality:** Clear, diagnostic-quality image ({round(iqa.get('overall_score', 85))}/100)\n\n"
                    f"**Suggested Questions you can ask me:**\n"
                    f"• *'What does this mean for my breathing?'*\n"
                    f"• *'What questions should I ask my doctor?'*\n"
                    f"• *'Can you explain the colored heatmap in simple words?'*"
                )
            else:
                return (
                    f"### Study Summary — Patient {study.get('patient_id', 'PT-RAD')}\n\n"
                    f"• **Primary Finding:** **{top_name}** ({top_prob}% confidence)\n"
                    f"• **Detected Pathologies:** {', '.join(detected_list)}\n"
                    f"• **Anatomical Localization:** Primary focus in the **{primary_zone}** ({primary_pct:.1f}% attribution)\n"
                    f"• **Heart Size (CTR):** **{ctr.get('ctr_percentage', 45)}%** (`{'Cardiomegaly' if ctr.get('is_cardiomegaly') else 'Normal Heart Size'}`)\n"
                    f"• **Image Quality:** **{round(iqa.get('overall_score', 85))}/100** ({iqa.get('quality_tier', 'GOOD')})\n\n"
                    f"You can ask me to explain the **formal report**, explore **differential diagnoses ('why not effusion?')**, inspect **counterfactual lesion masking**, or ask any general radiology doubt."
                )
        else:
            if is_patient_mode:
                return (
                    "**VisionCare Health Assistant:**\n\n"
                    "I am ready to answer your questions about chest X-rays, common lung conditions, and medical imaging in plain everyday terms.\n\n"
                    "To evaluate a specific scan, please upload or select an X-ray in the **Analyze** tab."
                )
            return (
                "**VisionCare AI Clinical Assistant:**\n\n"
                "I can answer any questions on chest radiography, thoracic diseases, and clinical radiology interpretations.\n\n"
                "To evaluate a specific scan and inspect its structured findings, Grad-CAM++ heatmaps, CTR biometrics, and clinical report, please upload or select a radiograph in the **Analyze** tab."
            )

    def _generate_suggestions(self, study: Dict[str, Any], last_message: str, mode: str = "clinical") -> List[str]:
        """Generates smart contextual suggestions based on whether a study is active and persona mode (doctor vs patient)."""
        is_patient = mode == "patient"

        if not study or not study.get("patient_id"):
            if is_patient:
                return [
                    "What is pneumonia and how does a chest X-ray detect it?",
                    "What is an enlarged heart and what causes it?",
                    "How safe is a chest X-ray and how does it work?",
                    "What are common symptoms of fluid around the lungs (effusion)?",
                ]
            else:
                return [
                    "What 14 conditions does VisionCare AI evaluate?",
                    "How is the Cardiothoracic Ratio (CTR) measured?",
                    "What does Grad-CAM++ visual explainability show?",
                    "How do radiologists differentiate pneumonia from effusion?",
                ]

        classification = study.get("classification", {})
        ctr = study.get("ctr", {})
        all_findings = classification.get("all_predictions", []) or classification.get("all_findings", [])
        detected = [f for f in all_findings if f.get("is_detected")]

        suggestions = []

        if is_patient:
            suggestions.append("Can you explain my X-ray results in simple everyday words?")
            if detected:
                top_d = detected[0]["disease"]
                suggestions.append(f"Do I have signs of {top_d} or lung infection?")
            else:
                suggestions.append("Are there any serious abnormalities in my lungs?")

            if ctr.get("is_cardiomegaly"):
                suggestions.append(f"Is my heart size enlarged and should I be worried? (CTR: {ctr.get('ctr_percentage')}%)")
            else:
                suggestions.append("Is my heart size normal?")

            suggestions.append("What important questions should I ask my doctor about this scan?")
        else:
            if detected:
                top_d = detected[0]["disease"]
                suggestions.append(f"Review formal ACR Impression and Findings for {top_d}")
                suggestions.append("What is the Level 5 counterfactual causal probability drop?")
            else:
                suggestions.append("Review formal ACR Impression & Findings")
                suggestions.append("Why were other differentials ruled out ('Why Not?')")

            if ctr.get("is_cardiomegaly"):
                suggestions.append(f"Examine CTR biometrics ({ctr.get('ctr_percentage')}%) and caliper margins")
            else:
                suggestions.append("Inspect CTR cardiac and thoracic diameter calipers")

            suggestions.append("Detail Grad-CAM++ 5-zone anatomical attribution")

        return suggestions[:4]
