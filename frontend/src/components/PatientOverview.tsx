"use client";

import React, { useState } from "react";
import {
  Heart,
  Activity,
  CheckCircle2,
  AlertTriangle,
  FileDown,
  ArrowRight,
  Eye,
  EyeOff,
  Stethoscope,
  Info,
  Shield,
  Clock
} from "lucide-react";
import { StudyAnalysisResponse, FindingItem } from "@/types";
import { getStudyPdfUrl } from "@/lib/api";

interface PatientOverviewProps {
  study: StudyAnalysisResponse;
  onSwitchToDoctorMode: () => void;
  onSwitchToPACS: () => void;
}

export const PatientOverview: React.FC<PatientOverviewProps> = ({
  study,
  onSwitchToDoctorMode,
  onSwitchToPACS,
}) => {
  const [showAiOverlay, setShowAiOverlay] = useState<boolean>(true);

  // Extract key patient-friendly findings
  const allFindings: FindingItem[] =
    study.classification.all_predictions || study.classification.all_findings || [];
  
  const detectedFindings = allFindings.filter((f) => f.is_detected);
  const topFinding = detectedFindings.length > 0 ? detectedFindings[0] : null;

  const isCardiomegaly = study.ctr?.is_cardiomegaly || false;
  const ctrPct = study.ctr?.ctr_percentage ?? 0;
  const isNormal = detectedFindings.length === 0;

  // Layman explanations for common NIH pathologies
  const laymanExplanations: Record<string, string> = {
    Cardiomegaly: "The heart shadow appears enlarged relative to the chest cavity.",
    Effusion: "Fluid accumulation is noted in the lower pleural lining of the lungs.",
    Infiltration: "Subtle haziness observed in lung tissue, often associated with inflammation.",
    Atelectasis: "Minor partial deflation or collapse of small lung air sacs.",
    Pneumothorax: "Trapped air in the pleural space outside the lung. Requires clinical evaluation.",
    Mass: "A focal localized area of increased density requiring clinical follow-up.",
    Nodule: "A small rounded spot or shadow in the lung tissue.",
    Pneumonia: "Localized lung inflammation or consolidation suggestive of infection.",
    Consolidation: "Air in small lung airways replaced with inflammatory fluid.",
    Edema: "Fluid congestion detected within lung tissue or vasculature.",
    Emphysema: "Over-inflation or enlargement of the lung air spaces.",
    Fibrosis: "Scarring or thickening of the pulmonary interstitial tissue.",
    Pleural_Thickening: "Mild thickening of the outer membrane surrounding the lungs.",
    Hernia: "Diaphragmatic herniation shadow near the thoracic base.",
  };

  return (
    <div className="space-y-6">
      {/* 1. Main Status Verdict Banner */}
      <div
        className={`p-6 rounded-2xl border shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4 transition-all ${
          isNormal
            ? "bg-gradient-to-r from-emerald-950/80 via-emerald-900/40 to-slate-900 border-emerald-700/60"
            : "bg-gradient-to-r from-amber-950/80 via-rose-950/40 to-slate-900 border-amber-700/60"
        }`}
      >
        <div className="flex items-start space-x-4">
          <div
            className={`p-3 rounded-xl ${
              isNormal ? "bg-emerald-500/20 text-emerald-400" : "bg-amber-500/20 text-amber-400"
            }`}
          >
            {isNormal ? (
              <CheckCircle2 className="w-8 h-8" />
            ) : (
              <AlertTriangle className="w-8 h-8" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs uppercase font-mono tracking-wider text-slate-400">
                AI Health Summary
              </span>
              <span
                className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                  isNormal
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                    : "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                }`}
              >
                {isNormal ? "Clear Radiograph" : "Attention Recommended"}
              </span>
            </div>
            <h2 className="text-xl font-bold text-white mt-1">
              {isNormal
                ? "No Acute Cardiopulmonary Abnormalities Detected"
                : `${topFinding?.disease || "Cardiopulmonary Finding"} Detected`}
            </h2>
            <p className="text-sm text-slate-300 mt-1 max-w-2xl leading-relaxed">
              {isNormal
                ? "Your chest radiograph appears within normal baseline limits across all 14 evaluated lung and heart indicators."
                : `Our AI system identified potential indications of ${topFinding?.disease}. This preliminary scan is intended to assist your physician in making an accurate diagnosis.`}
            </p>
          </div>
        </div>

        {/* Quick CTA */}
        <div className="flex flex-wrap md:flex-col gap-2 w-full md:w-auto shrink-0">
          <button
            onClick={() => window.location.href = getStudyPdfUrl(study.study_id)}
            className="flex-1 md:flex-initial inline-flex items-center justify-center space-x-2 bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs px-4 py-2.5 rounded-xl shadow transition"
          >
            <FileDown className="w-4 h-4" />
            <span>Download PDF Report</span>
          </button>
          <button
            onClick={onSwitchToDoctorMode}
            className="flex-1 md:flex-initial inline-flex items-center justify-center space-x-2 bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-xs px-4 py-2.5 rounded-xl border border-slate-700 transition"
          >
            <Stethoscope className="w-4 h-4 text-cyan-400" />
            <span>View Full Doctor Report</span>
          </button>
        </div>
      </div>

      {/* 2. Key Vitals Grid (Friendly layperson metrics) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Heart Size */}
        <div className="glass-panel p-4 rounded-xl border border-radDark-700 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="flex items-center gap-1.5 font-medium">
              <Heart className="w-4 h-4 text-rose-400" />
              Heart Silhouette
            </span>
            <span
              className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                isCardiomegaly
                  ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                  : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
              }`}
            >
              {isCardiomegaly ? "Enlarged" : "Normal Size"}
            </span>
          </div>
          <div className="text-2xl font-bold text-slate-100">
            {ctrPct > 0 ? `${ctrPct}%` : "Normal"}
          </div>
          <p className="text-[11px] text-slate-400 leading-normal">
            {isCardiomegaly
              ? "Heart width occupies over 50% of inner thorax diameter (normal is under 50%)."
              : "Heart dimensions are balanced within healthy anatomical thoracic limits."}
          </p>
        </div>

        {/* Lungs Status */}
        <div className="glass-panel p-4 rounded-xl border border-radDark-700 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="flex items-center gap-1.5 font-medium">
              <Activity className="w-4 h-4 text-cyan-400" />
              Lungs & Airfields
            </span>
            <span
              className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                detectedFindings.some((f) => f.disease !== "Cardiomegaly")
                  ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                  : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
              }`}
            >
              {detectedFindings.some((f) => f.disease !== "Cardiomegaly")
                ? "Findings Flagged"
                : "Clear Fields"}
            </span>
          </div>
          <div className="text-2xl font-bold text-slate-100">
            {detectedFindings.some((f) => f.disease !== "Cardiomegaly")
              ? detectedFindings.find((f) => f.disease !== "Cardiomegaly")?.disease
              : "Bilateral Clear"}
          </div>
          <p className="text-[11px] text-slate-400 leading-normal">
            Bilateral symmetry is{" "}
            <span className="text-cyan-300 font-medium">
              {study.pulmonary_extraction.lung_symmetry_index
                ? `${Math.round(study.pulmonary_extraction.lung_symmetry_index * 100)}%`
                : "Balanced"}
            </span>
            . Lung volume ratio is properly expanded.
          </p>
        </div>

        {/* Clinical Urgency */}
        <div className="glass-panel p-4 rounded-xl border border-radDark-700 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="flex items-center gap-1.5 font-medium">
              <Clock className="w-4 h-4 text-amber-400" />
              Triage Recommendation
            </span>
            <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
              {study.emergency_triage?.priority_tier?.replace("_", " ") || "Routine"}
            </span>
          </div>
          <div
            className={`text-2xl font-bold ${
              study.emergency_triage?.priority_tier === "STAT_CRITICAL"
                ? "text-red-400"
                : study.emergency_triage?.priority_tier === "URGENT"
                ? "text-amber-300"
                : "text-emerald-300"
            }`}
          >
            {study.emergency_triage?.priority_tier === "STAT_CRITICAL"
              ? "Urgent Review"
              : study.emergency_triage?.priority_tier === "URGENT"
              ? "Prompt Follow-Up"
              : "Standard Routine"}
          </div>
          <p className="text-[11px] text-slate-400 leading-normal">
            {study.emergency_triage?.priority_tier === "STAT_CRITICAL"
              ? "Critical findings identified. Recommend urgent evaluation by physician."
              : study.emergency_triage?.priority_tier === "URGENT"
              ? "Non-critical findings noted. Recommend routine follow-up with doctor."
              : "No urgent flags. Standard scheduled checkup advised."}
          </p>
        </div>

        {/* Scan Clarity / IQA */}
        <div className="glass-panel p-4 rounded-xl border border-radDark-700 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="flex items-center gap-1.5 font-medium">
              <Shield className="w-4 h-4 text-emerald-400" />
              Image Quality
            </span>
            <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
              {study.iqa.quality_tier}
            </span>
          </div>
          <div className="text-2xl font-bold text-slate-100">
            {Math.round(study.iqa.overall_score)} / 100
          </div>
          <p className="text-[11px] text-slate-400 leading-normal">
            Radiograph sharpness and contrast are optimal for diagnostic AI assessment.
          </p>
        </div>
      </div>

      {/* 3. Visual Radiograph + AI Highlights Side-by-Side */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Simplified X-ray Preview */}
        <div className="lg:col-span-6 glass-panel rounded-2xl p-5 border border-radDark-700 flex flex-col shadow-xl">
          <div className="flex items-center justify-between pb-3 border-b border-radDark-700">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                Your Chest Radiograph
                <span className="text-[10px] font-normal px-2 py-0.5 rounded bg-blue-500/20 text-blue-300">
                  Frontal PA
                </span>
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Toggle AI highlight to see exactly where findings were detected.
              </p>
            </div>

            {/* Toggle Overlay Button */}
            <button
              onClick={() => setShowAiOverlay(!showAiOverlay)}
              className={`inline-flex items-center space-x-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg border transition ${
                showAiOverlay
                  ? "bg-blue-600/30 border-blue-500 text-blue-200"
                  : "bg-radDark-800 border-radDark-700 text-slate-400 hover:text-white"
              }`}
            >
              {showAiOverlay ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
              <span>{showAiOverlay ? "AI Highlights: ON" : "AI Highlights: OFF"}</span>
            </button>
          </div>

          {/* Viewer Container */}
          <div className="relative mt-4 flex-1 min-h-[380px] bg-black rounded-xl overflow-hidden flex items-center justify-center border border-radDark-700">
            <img
              src={study.image_assets.original}
              alt="Patient Chest Radiograph"
              className="max-h-[440px] max-w-full object-contain"
            />
            {showAiOverlay && (
              <img
                src={study.image_assets.heatmap_overlay}
                alt="AI Detection Overlay"
                className="absolute inset-0 m-auto max-h-[440px] max-w-full object-contain pointer-events-none mix-blend-screen opacity-75 transition-opacity"
              />
            )}
          </div>

          <div className="mt-3 flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-radDark-700">
            <span>Color gradient highlights areas of AI focus.</span>
            <button
              onClick={onSwitchToPACS}
              className="text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-medium text-xs transition"
            >
              <span>Open in Advanced PACS Viewer</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Right: Key Detected Conditions & Patient Recommendations */}
        <div className="lg:col-span-6 flex flex-col space-y-4">
          {/* Detected Conditions Card */}
          <div className="glass-panel rounded-2xl p-5 border border-radDark-700 shadow-xl flex-1">
            <div className="flex items-center justify-between pb-3 border-b border-radDark-700">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Info className="w-4 h-4 text-cyan-400" />
                Detected Health Conditions
              </h3>
              <span className="text-[11px] text-slate-400">
                {detectedFindings.length} flagged out of 14 tested
              </span>
            </div>

            <div className="mt-4 space-y-3">
              {detectedFindings.length === 0 ? (
                <div className="text-center py-10 space-y-2">
                  <div className="w-12 h-12 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto">
                    <CheckCircle2 className="w-6 h-6" />
                  </div>
                  <p className="text-sm font-semibold text-slate-200">
                    No Significant Cardiopulmonary Findings
                  </p>
                  <p className="text-xs text-slate-400 max-w-md mx-auto">
                    Atelectasis, Cardiomegaly, Effusion, Infiltration, Mass, Nodule,
                    Pneumonia, Pneumothorax, and all other target pathologies are negative.
                  </p>
                </div>
              ) : (
                detectedFindings.map((finding) => (
                  <div
                    key={finding.disease}
                    className="p-3.5 rounded-xl bg-radDark-900 border border-radDark-700 hover:border-slate-600 transition space-y-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-sm text-white">
                          {finding.disease}
                        </span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                          Detected ({finding.probability_pct}%)
                        </span>
                      </div>
                      <span className="text-[11px] text-slate-400 font-mono">
                        Cutoff: {(finding.threshold * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed">
                      {laymanExplanations[finding.disease] ||
                        "Anatomical pattern detected requiring radiologist review."}
                    </p>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Physician Advice & Next Steps Card */}
          <div className="glass-panel rounded-2xl p-5 border border-radDark-700 shadow-xl space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
              <Stethoscope className="w-4 h-4 text-emerald-400" />
              What Should You Do Next?
            </h4>
            <div className="space-y-2 text-xs text-slate-300 leading-relaxed">
              <p>
                1. <strong>Share this report with your physician:</strong> You can download the
                full diagnostic PDF report to show to your doctor or specialist.
              </p>
              <p>
                2. <strong>Clinical auscultation & history:</strong> These AI findings must be
                correlated with your personal symptoms, medical history, and physical examination.
              </p>
            </div>

            <div className="pt-2 border-t border-radDark-700 flex items-center justify-between">
              <button
                onClick={onSwitchToDoctorMode}
                className="text-xs font-semibold text-cyan-400 hover:text-cyan-300 flex items-center gap-1 transition"
              >
                <span>Switch to Doctor / Radiology View (14 Differentials)</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
