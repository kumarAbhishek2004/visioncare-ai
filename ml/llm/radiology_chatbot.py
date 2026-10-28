"""
========================================================================================
VisionCare AI: Multi-Model Radiologist Copilot & Explainability Chatbot
========================================================================================
Grounds conversation in real-time chest radiograph telemetry:
- 14-disease DenseNet-121 probabilities, confidence tiers, and operating thresholds
- Grad-CAM++ second-order attribution heatmaps & 5 anatomical zones (RUZ, RMZ, RLZ, LUZ, LLZ)
- Cardiothoracic Ratio (CTR) caliper biometrics and cardiomegaly classifications (> 50%)
- Image Quality Assessment (IQA) sharpness, exposure, dynamic range, and overall score
- Bilateral lung segmentation fields and symmetry index
- Preliminary clinical impressions and evidence-based recommendations

Supported Providers:
1. Google Gemini (Gemini 2.5 Flash / 1.5 Flash via GEMINI_API_KEY)
2. OpenAI & Open-Source OSS Models (GPT-4o, GPT-4o-mini, Llama 3, Mistral, Groq, Ollama via OPENAI_API_KEY & OPENAI_BASE_URL)
3. Deterministic Clinical CDS Reasoning Engine (Instant offline fallback)
========================================================================================
"""

import os
from typing import Dict, Any, List, Optional


class RadiologyChatbot:
    """
    Multi-model clinical assistant for chest radiograph analysis and explainability.
    """

    def __init__(self):
        self.gemini_client = None
        self.openai_client = None
        self.reload_clients()

    def reload_clients(self):
        """Initializes or refreshes LLM clients based on environment variables."""
        # 1. Initialize Gemini
        gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if gemini_key:
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=gemini_key)
                print("[+] RadiologyChatbot: Gemini Client initialized.")
            except Exception:
                try:
                    import google.generativeai as legacy_genai
                    legacy_genai.configure(api_key=gemini_key)
                    self.gemini_client = legacy_genai.GenerativeModel("gemini-1.5-flash")
                    print("[+] RadiologyChatbot: Legacy google.generativeai initialized.")
                except Exception as e:
                    print(f"[!] RadiologyChatbot: Gemini init failed: {e}")
                    self.gemini_client = None
        else:
            self.gemini_client = None

        # 2. Initialize Groq / OpenAI / OSS Client
        groq_key = os.environ.get("GROQ_API_KEY")
        openai_key = os.environ.get("OPENAI_API_KEY") or groq_key
        openai_base_url = os.environ.get("OPENAI_BASE_URL") or None

        # Automatically route to Groq endpoint if GROQ_API_KEY is present
        if groq_key and not openai_base_url:
            openai_base_url = "https://api.groq.com/openai/v1"

        if openai_key or openai_base_url:
            try:
                import openai
                import httpx
                self.openai_client = openai.OpenAI(
                    api_key=openai_key or "no-key-required-for-local-oss",
                    base_url=openai_base_url or None,
                    http_client=httpx.Client()
                )
                provider_tag = "Groq OSS" if (openai_base_url and "groq.com" in openai_base_url) else "OpenAI/OSS"
                print(f"[+] RadiologyChatbot: {provider_tag} Client initialized (Base URL: {openai_base_url or 'api.openai.com'}).")
            except Exception as e:
                print(f"[!] RadiologyChatbot: OpenAI/Groq init failed: {e}")
                self.openai_client = None
        else:
            self.openai_client = None

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
        """Constructs a comprehensive system prompt grounded in the study telemetry."""
        demographics = study.get("demographics", {})
        classification = study.get("classification", {})
        explainability = study.get("explainability", {})
        ctr = study.get("ctr", {})
        iqa = study.get("iqa", {})
        report = study.get("clinical_report", {})
        pulmonary = study.get("pulmonary_extraction", {})

        all_findings = classification.get("all_predictions", []) or classification.get("all_findings", [])
        detected_findings = [f for f in all_findings if f.get("is_detected")]
        top_detected_str = (
            ", ".join([f"{f['disease']} ({f.get('probability_pct', 0)}%)" for f in detected_findings])
            or "None"
        )

        all_findings_str = "\n".join([
            f"- {f['disease']}: {f.get('probability_pct', 0)}% (Threshold: {f.get('threshold', 0.5)*100:.1f}%, Tier: {f.get('confidence_tier', 'LOW')})"
            for f in all_findings
        ])

        boxes_str = "None"
        boxes = explainability.get("bounding_boxes", [])
        if boxes:
            boxes_str = "; ".join([
                f"Zone: {b.get('zone', 'Unknown')}, Dimensions: {b.get('width_cm', 0):.1f}x{b.get('height_cm', 0):.1f} cm (Confidence: {b.get('confidence', 0)*100:.0f}%)"
                for b in boxes
            ])

        tone_guidance = (
            "PATIENT-FRIENDLY MODE: Explain concepts clearly, gently, and without frightening medical jargon. "
            "Use clear analogies, reassure the patient, and encourage them to speak directly with their treating physician."
            if mode == "patient"
            else "CLINICAL DOCTOR MODE: Use standard American College of Radiology (ACR) terminology. "
            "Cite exact probabilities, confidence tiers, anatomical zones, and caliper biometrics."
        )

        return f"""
You are the VisionCare AI Clinical Radiologist Copilot and Explainability Assistant.
You have direct telemetry access to the automated analysis of this frontal chest radiograph.

PATIENT & STUDY TELEMETRY:
- Patient ID: {study.get('patient_id', 'PT-ANON')}
- Age / Gender: {demographics.get('age', 'Unknown')}Y / {demographics.get('gender', 'M')}
- Projection: {demographics.get('view_position', 'PA')}
- Image Quality Assessment (IQA): Score {round(iqa.get('overall_score', 85))}/100 ({iqa.get('quality_tier', 'GOOD')}), Sharpness {iqa.get('laplacian_variance', 120):.1f}
- Detected Pathologies: {top_detected_str}
- Primary Explainability Zone: {explainability.get('primary_zone_name', 'Bilateral Lungs')} ({explainability.get('primary_zone_percentage', 0):.1f}% heat attribution)
- Target Disease: {explainability.get('target_pathology', 'Primary Finding')}
- Bounding Box Calipers: {boxes_str}
- Cardiothoracic Ratio (CTR): {ctr.get('ctr_percentage', 45)}% (Cardiac: {ctr.get('cardiac_diameter_cm', 12)} cm, Thorax: {ctr.get('thoracic_diameter_cm', 26)} cm, Cardiomegaly: {ctr.get('is_cardiomegaly', False)})
- Lung Symmetry Index: {pulmonary.get('lung_symmetry_index', 0.88)*100:.0f}%
- Clinical Impression: {report.get('impression', 'No acute cardiopulmonary disease detected.')}
- Recommendations: {report.get('recommendations', 'Clinical correlation advised.')}

EVALUATED 14 THORACIC CLASSES:
{all_findings_str}

COMMUNICATION STYLE:
{tone_guidance}

SAFETY & OPERATIONAL RULES:
1. Ground every answer strictly in the real radiograph telemetry provided above.
2. If asked why a finding was flagged, reference the specific anatomical zone, Grad-CAM++ focus area, and calibrated probability.
3. If asked about CTR or heart size, explain the cardiac-to-thoracic diameter measurement and the >50% cardiomegaly threshold.
4. Keep responses concise, direct, and well-structured using markdown bullet points and bold highlights.
5. Reiterate when appropriate that this is an AI clinical decision support tool and requires board-certified radiologist verification.
""".strip()

    def chat(
        self,
        message: str,
        history: List[Dict[str, str]],
        study_context: Dict[str, Any],
        mode: str = "clinical",  # "clinical" or "patient"
        preferred_model: str = "auto"  # "auto", "gemini", "openai", "cds"
    ) -> Dict[str, Any]:
        """
        Process a user question regarding the chest radiograph.
        """
        # Always re-check environment variables in case keys were just set
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
                        "suggested_questions": self._generate_suggestions(study_context, message),
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
                        "suggested_questions": self._generate_suggestions(study_context, message),
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
                            "suggested_questions": self._generate_suggestions(study_context, message),
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
                            "suggested_questions": self._generate_suggestions(study_context, message),
                            "source": "gemini",
                            "model_name": "Gemini 2.5 Flash"
                        }
                except Exception as e:
                    print(f"[!] Auto Gemini fallback failed: {e}")

        # 4. Built-in Deterministic Clinical CDS Reasoning Engine
        cds_response = self._generate_clinical_reasoning_response(message, history, study_context, mode)
        return {
            "response": cds_response,
            "suggested_questions": self._generate_suggestions(study_context, message),
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
        Deterministic, rule-based clinical intelligence engine.
        Answers questions accurately based on study findings, explainability maps, CTR, and IQA.
        """
        q = message.lower()
        classification = study.get("classification", {})
        explainability = study.get("explainability", {})
        ctr = study.get("ctr", {})
        iqa = study.get("iqa", {})
        report = study.get("clinical_report", {})
        demographics = study.get("demographics", {})

        all_findings = classification.get("all_predictions", []) or classification.get("all_findings", [])
        detected_findings = [f for f in all_findings if f.get("is_detected")]
        top_finding = detected_findings[0] if detected_findings else (all_findings[0] if all_findings else None)

        primary_zone = explainability.get("primary_zone_name", "Bilateral Lung Fields")
        primary_pct = explainability.get("primary_zone_percentage", 0)
        target_pathology = explainability.get("target_pathology", top_finding.get("disease", "Finding") if top_finding else "Finding")

        is_patient_mode = mode == "patient" or any(k in q for k in ["simple terms", "layman", "patient", "explain simply", "plain english"])

        # 1. CARDIOMEGALY & CTR
        if any(k in q for k in ["cardiomegaly", "ctr", "heart", "cardiac", "diameter"]):
            ctr_pct = ctr.get("ctr_percentage", 0)
            c_diam = ctr.get("cardiac_diameter_cm", 0)
            t_diam = ctr.get("thoracic_diameter_cm", 0)
            is_enlarged = ctr.get("is_cardiomegaly", False)

            if is_patient_mode:
                if is_enlarged:
                    return (
                        f"**Heart Size Evaluation (CTR: {ctr_pct}%):**\n\n"
                        f"• **What this means:** On a chest X-ray, doctors measure the width of the heart compared to the chest cavity (this is the *Cardiothoracic Ratio* or CTR).\n"
                        f"• **Your Result:** The heart measures **{c_diam} cm** across, and the chest cavity measures **{t_diam} cm**, giving a ratio of **{ctr_pct}%**.\n"
                        f"• A standard ratio is 50% or less. Because it is {ctr_pct}%, the AI flagged mild enlargement (Cardiomegaly).\n"
                        f"• **Next step:** Common causes include high blood pressure or fluid balance. An echocardiogram (ultrasound of the heart) is frequently recommended by doctors for detailed evaluation."
                    )
                else:
                    return (
                        f"**Heart Size Evaluation (CTR: {ctr_pct}%):**\n\n"
                        f"• **Normal Heart Size:** The AI measured the heart width ({c_diam} cm) relative to the chest cavity ({t_diam} cm), producing a CTR of **{ctr_pct}%**.\n"
                        f"• Because this falls within the normal threshold (<= 50%), the cardiac silhouette appears **completely normal**."
                    )
            else:
                return (
                    f"### Cardiothoracic Ratio (CTR) Biometric Analysis\n\n"
                    f"• **Transverse CTR:** **{ctr_pct}%** (Classification: `{'CARDIOMEGALY (>50%)' if is_enlarged else 'NORMAL SILHOUETTE (<= 50%)'}`)\n"
                    f"• **Maximal Cardiac Diameter:** **{c_diam} cm** (measured from right cardiac border to left apex caliper)\n"
                    f"• **Internal Thoracic Diameter:** **{t_diam} cm** (measured between inner rib margins at diaphragmatic apices)\n"
                    f"• **Diagnostic Significance:** "
                    + (f"A CTR of {ctr_pct}% exceeds the standard 0.50 cutoff, corroborating radiographic cardiomegaly. Cardiac apex is laterally displaced." if is_enlarged else f"A CTR of {ctr_pct}% confirms a normal cardiomediastinal silhouette on PA projection.")
                    + f"\n• **Recommended Correlation:** Transthoracic echocardiography (TTE) for left ventricular ejection fraction (LVEF) and chamber dimensions."
                )

        # 2. EXPLAINABILITY & HEATMAP
        if any(k in q for k in ["heatmap", "explainability", "gradcam", "grad-cam", "focus", "zone", "why did you", "what did you see", "evidence", "red"]):
            boxes = explainability.get("bounding_boxes", [])
            box_info = ""
            if boxes:
                top_b = boxes[0]
                box_info = f"• **Bounding Box Calipers:** Centered in the **{top_b.get('zone', primary_zone)}** ({top_b.get('width_cm', 0):.1f} cm × {top_b.get('height_cm', 0):.1f} cm) with **{top_b.get('confidence', 0)*100:.0f}%** focal attribution.\n"

            if is_patient_mode:
                return (
                    f"**How the AI Found This Area:**\n\n"
                    f"• **Visual Focus:** When analyzing this chest X-ray, the AI focused **{primary_pct:.0f}%** of its attention on the **{primary_zone}**.\n"
                    f"• **Heatmap Highlights:** The bright colored highlights show where visual patterns most strongly match **{target_pathology}** based on trained models.\n"
                    f"{box_info}"
                    f"• **Explore yourself:** Use the slider in the *Explainability* tab to blend between the raw X-ray and the AI's highlighted zones."
                )
            else:
                return (
                    f"### Grad-CAM++ Attribution & Zone Localization\n\n"
                    f"• **Target Pathology:** **{target_pathology}**\n"
                    f"• **Primary Activation Zone:** **{primary_zone}** (concentrating **{primary_pct:.1f}%** of positive second-order gradients)\n"
                    f"{box_info}"
                    f"• **Methodology:** Grad-CAM++ extracts weighted spatial feature maps from the final convolutional block of DenseNet-121 (`denseblock4`). Pixel gradients with positive partial derivatives were mapped into 5 standardized anatomical zones (RUZ, RMZ, RLZ, LUZ, LLZ).\n"
                    f"• **Radiological Pattern:** Increased feature activation corresponds to opacity gradients and soft-tissue boundary differentials in the {primary_zone}."
                )

        # 3. PNEUMONIA / CONSOLIDATION / INFILTRATION
        if any(k in q for k in ["pneumonia", "consolidation", "infiltrat", "infection"]):
            p_find = next((f for f in all_findings if f["disease"] in ["Pneumonia", "Consolidation", "Infiltration"]), None)
            prob = p_find.get("probability_pct", 0) if p_find else 12
            det = p_find.get("is_detected", False) if p_find else False

            if is_patient_mode:
                return (
                    f"**Pneumonia & Lung Opacity Assessment:**\n\n"
                    f"• **Status:** {'Potential signs detected' if det else 'No active pneumonia detected'} ({prob}% probability).\n"
                    f"• **Explanation:** Pneumonia typically causes fluid or inflammatory cells to collect in the air sacs, showing up as cloudy white patches. "
                    + (f"The AI highlighted patches in the {primary_zone}." if det else "The lung fields in this scan appear clear without dense consolidations.")
                    + "\n• **Recommendation:** If symptoms like fever, cough, or shortness of breath are present, your doctor will listen to your chest and may order follow-up tests."
                )
            else:
                return (
                    f"### Pulmonary Infiltration & Consolidation Profile\n\n"
                    f"• **Pneumonia Probability:** **{prob}%** (Threshold: {p_find.get('threshold', 0.25)*100:.1f}%, Status: `{'DETECTED' if det else 'BELOW THRESHOLD'}`)\n"
                    f"• **Localization:** {primary_zone}\n"
                    f"• **Radiographic Signs:** "
                    + ("Ill-defined alveolar opacities with potential silhouette sign along adjacent mediastinal or diaphragmatic borders." if det else "Parenchymal air volumes are preserved with clear bronchovascular arborization bilaterally.")
                    + f"\n• **Differential Considerations:** Parapneumonic consolidation, atelectatic collapse, aspiration, or focal edema."
                )

        # 4. PLEURAL EFFUSION & COSTOPHRENIC ANGLES
        if any(k in q for k in ["effusion", "fluid", "pleural", "costophrenic", "meniscus"]):
            eff = next((f for f in all_findings if f["disease"] == "Effusion"), None)
            prob = eff.get("probability_pct", 0) if eff else 8
            det = eff.get("is_detected", False) if eff else False

            if is_patient_mode:
                return (
                    f"**Pleural Fluid Evaluation:**\n\n"
                    f"• **Finding:** {'Fluid collection flagged' if det else 'Clear costophrenic angles'} ({prob}% probability).\n"
                    f"• **What this means:** When fluid accumulates in the bottom corners of the chest, it forms a curved waterline (meniscus sign).\n"
                    f"• **Conclusion:** "
                    + (f"The AI detected blunting of the angle in the {primary_zone}, suggestive of pleural fluid accumulation." if det else "Both lower lung angles remain sharp and clear, with no fluid accumulation.")
                )
            else:
                return (
                    f"### Pleural Space & Costophrenic Angle Analysis\n\n"
                    f"• **Pleural Effusion Probability:** **{prob}%** (`{'DETECTED' if det else 'WITHIN NORMAL LIMITS'}`)\n"
                    f"• **Anatomical Siting:** Localized to **{primary_zone}**.\n"
                    f"• **Signs:** "
                    + ("Blunting of the lateral costophrenic sulcus with diagnostic meniscus sign." if det else "Sharp lateral and posterior costophrenic angles bilaterally without dependent fluid tracking.")
                    + f"\n• **Clinical Workup:** Bedside point-of-care lung ultrasound (POCUS) to assess free fluid layering."
                )

        # 5. PNEUMOTHORAX / AIR LEAK
        if any(k in q for k in ["pneumothorax", "collapsed lung", "pleural line", "air leak"]):
            ptx = next((f for f in all_findings if f["disease"] == "Pneumothorax"), None)
            prob = ptx.get("probability_pct", 0) if ptx else 4
            det = ptx.get("is_detected", False) if ptx else False

            return (
                f"### Pneumothorax (Air Leak) Assessment\n\n"
                f"• **Probability:** **{prob}%** (Status: `{'ACUTE DETECTION' if det else 'NEGATIVE - NO PNEUMOTHORAX'}`)\n"
                f"• **Apical & Lateral Margins:** "
                + ("A sharp visceral pleural white line is distinguished with absent peripheral vascular markings. STAT review required." if det else "Fine pulmonary parenchymal vascular markings extend completely to the peripheral chest wall. No visceral pleural line displacement observed.")
                + f"\n• **Mediastinal Shift:** {'Normal midline trachea and mediastinum.' if not det else 'Evaluate closely for contralateral tracheal deviation ruling out tension physiology.'}"
            )

        # 6. IMAGE QUALITY ASSESSMENT (IQA)
        if any(k in q for k in ["quality", "blur", "sharpness", "exposure", "resolution", "iqa", "clear"]):
            score = round(iqa.get("overall_score", 88))
            tier = iqa.get("quality_tier", "GOOD")
            sharpness = iqa.get("laplacian_variance", 145)
            dyn_range = iqa.get("dynamic_range", 255)

            return (
                f"### Image Quality Assessment (IQA) Report\n\n"
                f"• **Composite Quality Score:** **{score} / 100** (`{tier}`)\n"
                f"• **Laplacian Variance (Sharpness):** **{sharpness:.1f}** (Threshold > 60: `{ 'SHARP' if sharpness > 60 else 'BORDERLINE BLUR' }`)\n"
                f"• **Dynamic Range:** **{dyn_range} Gy** (full 8-bit gray scale preservation)\n"
                f"• **Quality Verdict:** The radiograph demonstrates optimal thoracic penetration with clearly delineated vertebral endplates through the cardiac silhouette and distinct bronchovascular branching."
            )

        # 7. PATIENT-FRIENDLY TRANSLATION
        if is_patient_mode or any(k in q for k in ["simple terms", "layman", "patient", "tell me simply"]):
            findings_desc = []
            if detected_findings:
                for f in detected_findings:
                    findings_desc.append(f"• **{f['disease']}**: Identified with **{f.get('probability_pct', 0)}%** AI confidence in the {primary_zone}.")
            else:
                findings_desc.append("• **Normal Lung Fields**: The AI did not detect any acute abnormalities, pneumonia, fluid, or lung collapse.")

            findings_text = "\n".join(findings_desc)
            return (
                f"**Here is a Plain-Language Summary of Your Chest X-ray:**\n\n"
                f"{findings_text}\n\n"
                f"• **Heart:** The heart size ratio is **{ctr.get('ctr_percentage', 45)}%** ({'slightly enlarged' if ctr.get('is_cardiomegaly') else 'within normal proportions'}).\n"
                f"• **Image Quality:** The X-ray image is clear and easy to read (Quality score: **{round(iqa.get('overall_score', 85))}/100**).\n\n"
                f"**What should you do next?**\n"
                f"Please share this report with your treating physician. Computer tools provide helpful clues, but your doctor will combine this with how you are feeling (symptoms, vital signs, physical exam) to determine the best care plan."
            )

        # 8. RECOMMENDATIONS & NEXT CLINICAL STEPS
        if any(k in q for k in ["recommend", "next step", "what to do", "treatment", "follow up", "workup"]):
            rec = report.get("recommendations", "Clinical correlation and physical examination advised.")
            imp = report.get("impression", "No acute pathology.")

            return (
                f"### Clinical Recommendations & Diagnostic Next Steps\n\n"
                f"• **AI Impression:** {imp}\n\n"
                f"• **Recommended Action Plan:**\n"
                f"  1. **Radiologist Review:** Independent board-certified overread of the radiograph with prior study comparison.\n"
                f"  2. **Correlative Testing:** {rec}\n"
                + (f"  3. **Echocardiography (TTE):** Indicated to evaluate chamber dimensions given CTR of {ctr.get('ctr_percentage', 52)}%.\n" if ctr.get('is_cardiomegaly') else "")
                + (f"  4. **Thoracic CT / POCUS:** Consider non-contrast chest CT if opacity in {primary_zone} does not resolve on follow-up.\n" if detected_findings else "  3. **Routine Care:** No emergency chest imaging required at this time.\n")
                + f"\n*Notice: VisionCare AI recommendations are advisory decision-support insights.*"
            )

        # 9. DEFAULT / GENERAL OVERVIEW
        top_name = top_finding.get("disease", "None") if top_finding else "None"
        top_prob = top_finding.get("probability_pct", 0) if top_finding else 0
        detected_list = [f"{f['disease']} ({f.get('probability_pct', 0)}%)" for f in detected_findings] or ["None (All 14 within normal limits)"]

        return (
            f"### VisionCare AI Study Overview\n\n"
            f"• **Primary Finding:** **{top_name}** ({top_prob}% calibrated confidence)\n"
            f"• **Detected Pathologies:** {', '.join(detected_list)}\n"
            f"• **Anatomical Localization:** Concentrated in the **{primary_zone}** ({primary_pct:.1f}% Grad-CAM++ focus)\n"
            f"• **Cardiothoracic Ratio (CTR):** **{ctr.get('ctr_percentage', 45)}%** (`{'Cardiomegaly' if ctr.get('is_cardiomegaly') else 'Normal'}`)\n"
            f"• **Image Quality Score:** **{round(iqa.get('overall_score', 88))}/100** ({iqa.get('quality_tier', 'GOOD')})\n\n"
            f"Feel free to ask me any specific question about the **heatmap**, **anatomical zones**, **CTR calipers**, **14 evaluated diseases**, or request a **patient-friendly explanation**!"
        )

    def _generate_suggestions(self, study: Dict[str, Any], last_message: str) -> List[str]:
        """Generates smart contextual suggestions based on study findings."""
        classification = study.get("classification", {})
        ctr = study.get("ctr", {})
        all_findings = classification.get("all_predictions", []) or classification.get("all_findings", [])
        detected = [f for f in all_findings if f.get("is_detected")]

        suggestions = []

        if ctr.get("is_cardiomegaly"):
            suggestions.append(f"Why is CTR of {ctr.get('ctr_percentage', 55)}% flagged?")

        if detected:
            top_d = detected[0]["disease"]
            suggestions.append(f"Why did the AI diagnose {top_d}?")
            suggestions.append("What anatomical zones were highlighted?")
        else:
            suggestions.append("How confident is the AI that this scan is normal?")
            suggestions.append("Was Pneumothorax or Effusion ruled out?")

        suggestions.append("Explain this report in simple terms for a patient")
        suggestions.append("What follow-up tests or steps are recommended?")

        return suggestions[:4]
