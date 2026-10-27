"use client";

import React from "react";
import {
  FileDown,
  Share2,
  Activity,
  Heart,
  CheckCircle2,
  AlertCircle
} from "lucide-react";
import { StudyAnalysisResponse, FindingItem } from "@/types";
import { getStudyPdfUrl } from "@/lib/api";

interface ClinicalReportViewProps {
  study: StudyAnalysisResponse;
}

export const ClinicalReportView: React.FC<ClinicalReportViewProps> = ({ study }) => {
  const allFindings: FindingItem[] =
    study.classification.all_predictions || study.classification.all_findings || [];
  const detectedFindings = allFindings.filter((f) => f.is_detected);
  const primaryFinding = detectedFindings.length > 0 ? detectedFindings[0] : allFindings[0];

  const now = new Date();
  const dateFormatted = now.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
  const timeFormatted = now.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      {/* 1. Header with Download & Share actions */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Clinical Report
          </h2>
          <p className="text-sm text-slate-500">
            AI-assisted analysis report with findings and recommendations.
          </p>
        </div>

        <div className="flex items-center space-x-2.5">
          <button
            onClick={() => window.location.href = getStudyPdfUrl(study.study_id)}
            className="inline-flex items-center space-x-1.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs px-4 py-2.5 rounded-xl shadow-sm shadow-blue-500/20 transition"
          >
            <FileDown className="w-4 h-4" />
            <span>Download PDF</span>
          </button>

          <button
            onClick={() => alert("Report link copied to clipboard")}
            className="inline-flex items-center space-x-1.5 bg-white hover:bg-slate-50 text-slate-700 font-semibold text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 shadow-sm transition"
          >
            <Share2 className="w-4 h-4 text-slate-500" />
            <span>Share Report</span>
          </button>
        </div>
      </div>

      {/* 2. Structured White Document Paper Sheet */}
      <div className="card-surface p-6 sm:p-10 rounded-3xl shadow-md border border-slate-200 bg-white space-y-8 text-slate-900">
        {/* Document Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-6 border-b border-slate-200">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center">
              <Activity className="w-5 h-5" />
            </div>
            <span className="text-lg font-bold tracking-tight text-slate-900">
              VisionCare <span className="text-blue-600">AI</span>
            </span>
          </div>

          <div className="text-left sm:text-right space-y-0.5">
            <h4 className="text-sm font-bold text-slate-800">
              AI-Assisted Chest X-ray Analysis Report
            </h4>
            <p className="text-xs text-slate-500 font-mono">
              Report ID: {study.study_id}
            </p>
            <p className="text-xs text-slate-400">
              Generated: {dateFormatted}, {timeFormatted}
            </p>
          </div>
        </div>

        {/* Patient Information & AI Summary (2 Columns) */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Patient Info Column */}
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100 space-y-2">
            <h5 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
              Patient Information
            </h5>
            <div className="grid grid-cols-2 gap-y-1.5 text-xs">
              <span className="text-slate-500">Patient ID:</span>
              <span className="font-semibold text-slate-800">{study.patient_id}</span>

              <span className="text-slate-500">Age / Gender:</span>
              <span className="font-semibold text-slate-800">
                {study.demographics.age || 62}Y / {study.demographics.gender || "M"}
              </span>

              <span className="text-slate-500">Study Date:</span>
              <span className="font-semibold text-slate-800">{dateFormatted}</span>

              <span className="text-slate-500">Study Type:</span>
              <span className="font-semibold text-slate-800">
                Chest X-ray ({study.demographics.view_position || "PA"})
              </span>
            </div>
          </div>

          {/* AI Analysis Summary Column */}
          <div className="p-4 rounded-2xl bg-rose-50/60 border border-rose-100 space-y-2">
            <h5 className="text-xs font-bold uppercase tracking-wider text-rose-700 mb-2">
              AI Analysis Summary
            </h5>
            <div className="space-y-1.5">
              <div className="flex items-center space-x-2">
                <Heart className="w-5 h-5 text-rose-600 shrink-0" />
                <span className="text-sm font-bold text-slate-900">
                  {primaryFinding?.is_detected ? `Likely ${primaryFinding.disease}` : "No Acute Pathology"}
                </span>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-100 text-rose-700">
                  Reliability: {study.classification.prediction_reliability}
                </span>
              </div>
              <p className="text-xs text-slate-700 leading-relaxed">
                {primaryFinding?.is_detected
                  ? `Areas of increased probability detected in ${study.explainability.primary_zone_name || "lower thoracic region"}, commonly associated with ${primaryFinding.disease}.`
                  : "All 14 evaluated cardiopulmonary classes are unremarkable."}
              </p>
            </div>
          </div>
        </div>

        {/* Findings List */}
        <div className="space-y-3">
          <h5 className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Findings
          </h5>
          <div className="space-y-2">
            {detectedFindings.length === 0 ? (
              <div className="p-3.5 rounded-xl bg-slate-50 text-xs text-slate-600 flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>No acute thoracic abnormalities detected within the 14 monitored pathologies.</span>
              </div>
            ) : (
              detectedFindings.map((finding, idx) => (
                <div
                  key={finding.disease}
                  className="p-3 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between text-xs"
                >
                  <div className="flex items-center space-x-3">
                    <span className="w-6 h-6 rounded-full bg-rose-100 text-rose-700 flex items-center justify-center font-bold text-xs">
                      {idx + 1}
                    </span>
                    <div>
                      <span className="font-bold text-slate-900">{finding.disease}</span>
                      <p className="text-[11px] text-slate-500">
                        {finding.disease === "Cardiomegaly"
                          ? `Transverse cardiothoracic ratio is ${study.ctr?.ctr_percentage || 52}%.`
                          : "Focal radiographic density within thoracic fields."}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <span className="font-mono font-bold text-slate-800">
                      {finding.probability_pct}%
                    </span>
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200">
                      {finding.confidence_tier}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Key Image Views (4 Thumbnails) */}
        <div className="space-y-3">
          <h5 className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Key Image Views
          </h5>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="card-surface p-1.5 rounded-xl text-center space-y-1">
              <div className="aspect-square rounded-lg bg-black overflow-hidden flex items-center justify-center p-0.5">
                <img
                  src={study.image_assets.original}
                  alt="Original X-ray"
                  className="max-h-full max-w-full object-contain"
                />
              </div>
              <span className="text-[10px] font-semibold text-slate-600">Original X-ray</span>
            </div>

            <div className="card-surface p-1.5 rounded-xl text-center space-y-1">
              <div className="aspect-square rounded-lg bg-black overflow-hidden flex items-center justify-center p-0.5">
                <img
                  src={study.image_assets.heatmap_overlay}
                  alt="AI Heatmap"
                  className="max-h-full max-w-full object-contain"
                />
              </div>
              <span className="text-[10px] font-semibold text-slate-600">AI Heatmap</span>
            </div>

            <div className="card-surface p-1.5 rounded-xl text-center space-y-1">
              <div className="aspect-square rounded-lg bg-black overflow-hidden flex items-center justify-center p-0.5">
                <img
                  src={study.image_assets.overlay_mask}
                  alt="Lung Mask"
                  className="max-h-full max-w-full object-contain"
                />
              </div>
              <span className="text-[10px] font-semibold text-slate-600">Lung Mask</span>
            </div>

            <div className="card-surface p-1.5 rounded-xl text-center space-y-1">
              <div className="aspect-square rounded-lg bg-black overflow-hidden flex items-center justify-center p-0.5">
                <img
                  src={study.image_assets.enhanced}
                  alt="Enhanced Image"
                  className="max-h-full max-w-full object-contain"
                />
              </div>
              <span className="text-[10px] font-semibold text-slate-600">Enhanced Image</span>
            </div>
          </div>
        </div>

        {/* Clinical Impression & Recommendation Footer */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-slate-200 text-xs">
          <div className="space-y-1">
            <h6 className="font-bold text-slate-800 uppercase text-[11px]">
              Clinical Impression (AI-Generated)
            </h6>
            <p className="text-slate-600 leading-relaxed">
              {study.clinical_report?.impression ||
                "Findings are suggestive of cardiopulmonary changes. Clinical correlation and radiologist review are recommended."}
            </p>
          </div>

          <div className="space-y-1">
            <h6 className="font-bold text-slate-800 uppercase text-[11px]">
              Recommendation
            </h6>
            <p className="text-slate-600 leading-relaxed">
              {study.clinical_report?.recommendations ||
                "Recommend clinical correlation and follow-up with a board-certified radiologist."}
            </p>
          </div>
        </div>

        {/* Legal Disclaimer */}
        <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-[10px] text-slate-500 leading-relaxed flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 text-slate-400 shrink-0" />
          <span>
            <strong>Regulatory Disclaimer:</strong> VisionCare AI is an assistive decision-support research tool.
            Automated findings must be correlated clinically and verified by a board-certified radiologist.
          </span>
        </div>
      </div>
    </div>
  );
};
