"""
========================================================================================
VisionCare AI: Medical PDF Report Generator
========================================================================================
Purpose: Generates professional, audit-ready clinical study reports using ReportLab.
Includes: Patient demographics, 4-panel image comparison, multi-label probability table,
          ACR narrative findings, and regulatory disclaimer.
========================================================================================
"""

import os
import io
import cv2
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


class ClinicalPDFGenerator:
    """
    Renders structured clinical radiology reports into publication-grade PDF documents.
    """

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._init_custom_styles()

    def _init_custom_styles(self):
        self.styles.add(ParagraphStyle(
            name="ReportTitle",
            parent=self.styles["Heading1"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold"
        ))
        self.styles.add(ParagraphStyle(
            name="SectionHeading",
            parent=self.styles["Heading2"],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#1e293b"),
            fontName="Helvetica-Bold",
            spaceAfter=4
        ))
        self.styles.add(ParagraphStyle(
            name="BodySmall",
            parent=self.styles["Normal"],
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#334155")
        ))
        self.styles.add(ParagraphStyle(
            name="DisclaimerText",
            parent=self.styles["Normal"],
            fontSize=7,
            leading=9,
            textColor=colors.HexColor("#64748b"),
            fontName="Helvetica-Oblique"
        ))

    def _convert_cv_image_to_rl(self, img_arr: np.ndarray, target_w: int = 125, target_h: int = 125) -> RLImage:
        """Converts an OpenCV uint8 array to a ReportLab Flowable Image via in-memory buffer."""
        resized = cv2.resize(img_arr, (target_w, target_h))
        if len(resized.shape) == 2:
            resized = cv2.cvtColor(resized, cv2.COLOR_GRAY2RGB)
        elif resized.shape[2] == 4:
            resized = cv2.cvtColor(resized, cv2.COLOR_BGRA2RGB)
        else:
            resized = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

        is_success, buffer = cv2.imencode(".png", resized)
        io_buf = io.BytesIO(buffer)
        return RLImage(io_buf, width=target_w, height=target_h)

    def generate_pdf(
        self,
        analysis_data: Dict[str, Any],
        image_dict: Dict[str, np.ndarray],
        output_path: Optional[str] = None
    ) -> bytes:
        """
        Builds the clinical PDF document.
        Returns: PDF binary bytes.
        """
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            output_path if output_path else pdf_buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        elements = []
        study_id = analysis_data.get("study_id", "STD-UNKNOWN")
        patient_id = analysis_data.get("patient_id", "PT-UNKNOWN")
        demographics = analysis_data.get("demographics", {})
        age = demographics.get("age", 55)
        gender = demographics.get("gender", "M")
        view = demographics.get("view_position", "PA")
        timestamp = analysis_data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M UTC"))

        # 1. Header Banner
        header_data = [
            [
                Paragraph("<b>VISIONCARE AI WORKSTATION</b><br/><font size=8 color='#64748b'>Explainable Radiology Decision Support</font>", self.styles["Normal"]),
                Paragraph(f"<b>Study ID:</b> {study_id}<br/><b>Patient ID:</b> {patient_id} ({age}y, {gender})<br/><b>Projection:</b> {view} | <b>Date:</b> {timestamp[:10]}", self.styles["BodySmall"])
            ]
        ]
        header_table = Table(header_data, colWidths=[270, 270])
        header_table.setStyle(TableStyle([
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LINEBELOW", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 10))

        # 2. Quality & Safety Summary Banner
        iqa = analysis_data.get("iqa", {})
        iqa_score = iqa.get("overall_score", 0.0)
        iqa_tier = iqa.get("quality_tier", "AVERAGE")
        clf = analysis_data.get("classification", {})
        reliability = clf.get("prediction_reliability", "MODERATE")
        safety_triage = clf.get("safety_triage", "ASSISTED_REVIEW_READY")

        badge_color = "#16a34a" if reliability == "HIGH" else ("#d97706" if reliability == "MODERATE" else "#dc2626")

        triage_data = [
            [
                Paragraph(f"<b>Image Quality:</b> {iqa_score}/100 ({iqa_tier})", self.styles["BodySmall"]),
                Paragraph(f"<b>Prediction Reliability:</b> <font color='{badge_color}'><b>{reliability}</b></font>", self.styles["BodySmall"]),
                Paragraph(f"<b>Triage Status:</b> <b>{safety_triage}</b>", self.styles["BodySmall"])
            ]
        ]
        triage_table = Table(triage_data, colWidths=[180, 180, 180])
        triage_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("PADDING", (0, 0), (-1, -1), 6),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ]))
        elements.append(triage_table)
        elements.append(Spacer(1, 10))

        # 3. 4-Panel Diagnostic Image Comparison Grid
        elements.append(Paragraph("Diagnostic Image Triangulation & Feature Attribution", self.styles["SectionHeading"]))

        orig_rl = self._convert_cv_image_to_rl(image_dict.get("original", np.zeros((100, 100), dtype=np.uint8)))
        enh_rl  = self._convert_cv_image_to_rl(image_dict.get("enhanced", np.zeros((100, 100), dtype=np.uint8)))
        mask_rl = self._convert_cv_image_to_rl(image_dict.get("overlay_mask", np.zeros((100, 100, 3), dtype=np.uint8)))
        cam_rl  = self._convert_cv_image_to_rl(image_dict.get("heatmap_overlay", np.zeros((100, 100, 3), dtype=np.uint8)))

        image_grid_data = [
            [orig_rl, enh_rl, mask_rl, cam_rl],
            [
                Paragraph("<font size=7 color='#475569'>A: Original Scan</font>", self.styles["Normal"]),
                Paragraph("<font size=7 color='#475569'>B: CLAHE Enhanced</font>", self.styles["Normal"]),
                Paragraph("<font size=7 color='#475569'>C: Segmented Parenchyma</font>", self.styles["Normal"]),
                Paragraph("<font size=7 color='#475569'>D: Grad-CAM++ Attribution</font>", self.styles["Normal"])
            ]
        ]
        image_grid_table = Table(image_grid_data, colWidths=[135, 135, 135, 135])
        image_grid_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 2),
        ]))
        elements.append(image_grid_table)
        elements.append(Spacer(1, 10))

        # 4. Multi-Label Finding Probabilities
        elements.append(Paragraph("Calibrated Pathological Findings", self.styles["SectionHeading"]))
        findings_rows = [
            [
                Paragraph("<b>Detected Pathology</b>", self.styles["BodySmall"]),
                Paragraph("<b>Calibrated Probability</b>", self.styles["BodySmall"]),
                Paragraph("<b>Operating Threshold</b>", self.styles["BodySmall"]),
                Paragraph("<b>Diagnostic Status</b>", self.styles["BodySmall"])
            ]
        ]

        top_findings = clf.get("all_predictions", [])[:5]
        for f in top_findings:
            det_label = "POSITIVE" if f["is_detected"] else "NEGATIVE"
            det_color = "#dc2626" if f["is_detected"] else "#64748b"
            findings_rows.append([
                Paragraph(f"{f['disease']}", self.styles["BodySmall"]),
                Paragraph(f"{f['probability_pct']}%", self.styles["BodySmall"]),
                Paragraph(f"{f['threshold']*100:.1f}%", self.styles["BodySmall"]),
                Paragraph(f"<font color='{det_color}'><b>{det_label}</b></font>", self.styles["BodySmall"])
            ])

        findings_table = Table(findings_rows, colWidths=[150, 130, 130, 130])
        findings_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ("PADDING", (0, 0), (-1, -1), 4),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ]))
        elements.append(findings_table)
        elements.append(Spacer(1, 10))

        # 5. Narrative Clinical Synthesis (ACR Format)
        report = analysis_data.get("clinical_report", {})
        xai = analysis_data.get("explainability", {})
        primary_zone = xai.get("primary_zone_name", "Pulmonary field")
        primary_pct = xai.get("primary_zone_percentage", 0.0)

        elements.append(Paragraph("Clinical Observations & Decision Support", self.styles["SectionHeading"]))

        narrative_text = (
            f"<b>TECHNIQUE:</b> {report.get('technique', 'Frontal chest radiograph.')}<br/><br/>"
            f"<b>ANATOMICAL LOCALIZATION:</b> Focal feature activation localized to <b>{primary_zone}</b> ({primary_pct}% attribution).<br/><br/>"
            f"<b>FINDINGS:</b> {report.get('findings', 'Lungs are clear.')}<br/><br/>"
            f"<b>IMPRESSION:</b> {report.get('impression', 'No acute cardiopulmonary disease.')}<br/><br/>"
            f"<b>DIFFERENTIAL CONSIDERATIONS:</b> {', '.join(report.get('differential_considerations', ['None']))}.<br/><br/>"
            f"<b>RECOMMENDATIONS:</b> {report.get('recommendations', 'Clinical follow-up as indicated.')}"
        )
        elements.append(Paragraph(narrative_text, self.styles["BodySmall"]))
        elements.append(Spacer(1, 12))

        # 6. Regulatory Disclaimer
        elements.append(Paragraph(
            "<b>DISCLAIMER:</b> VisionCare AI is an assistive decision-support research system. "
            "This document is an AI-generated synthesis intended solely to assist licensed medical professionals. "
            "Final diagnosis and patient management decisions remain the exclusive responsibility of the treating physician.",
            self.styles["DisclaimerText"]
        ))

        doc.build(elements)
        pdf_bytes = pdf_buffer.getvalue()
        pdf_buffer.close()
        return pdf_bytes
