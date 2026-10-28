"use client";

import React from "react";
import {
  CheckCircle2,
  FileDown,
  PlusCircle,
  Activity,
  Heart,
  ArrowRight,
  AlertTriangle
} from "lucide-react";
import { StudyAnalysisResponse, FindingItem } from "@/types";
import { getStudyPdfUrl } from "@/lib/api";

interface ResultsOverviewProps {
  study: StudyAnalysisResponse;
  onNewAnalysis: () => void;
  onNavigateTab: (tab: "overview" | "findings" | "explainability" | "trace" | "technical" | "chat") => void;
}

export const ResultsOverview: React.FC<ResultsOverviewProps> = ({
  study,
  onNewAnalysis,
  onNavigateTab,
}) => {
  const allFindings: FindingItem[] =
    study.classification.all_predictions || study.classification.all_findings || [];
  
  // Sort findings by probability descending
  const sortedFindings = [...allFindings].sort((a, b) => b.probability - a.probability);
  
  // Take top detected findings or top 4
  const detectedFindings = sortedFindings.filter((f) => f.is_detected);
  const displayFindings = detectedFindings.length > 0 ? detectedFindings.slice(0, 5) : sortedFindings.slice(0, 4);

  const topFinding = displayFindings.length > 0 ? displayFindings[0] : null;
  const isCardiomegaly = study.ctr?.is_cardiomegaly || false;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* 1. Top Success Banner */}
      <div className="card-surface p-4 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-sm border border-emerald-200 bg-emerald-50/40">
        <div className="flex items-center space-x-2 text-emerald-800 text-sm font-semibold">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
          <span>Analysis completed in 2.1 seconds</span>
        </div>

        <div className="flex items-center space-x-2.5 w-full sm:w-auto">
          <button
            onClick={() => window.location.href = getStudyPdfUrl(study.study_id)}
            className="flex-1 sm:flex-initial inline-flex items-center justify-center space-x-1.5 bg-white hover:bg-slate-50 text-slate-700 font-semibold text-xs px-3.5 py-2 rounded-xl border border-slate-200 shadow-sm transition"
          >
            <FileDown className="w-4 h-4 text-slate-500" />
            <span>Download Report</span>
          </button>

          <button
            onClick={onNewAnalysis}
            className="flex-1 sm:flex-initial inline-flex items-center justify-center space-x-1.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs px-4 py-2 rounded-xl shadow-sm shadow-blue-500/20 transition"
          >
            <PlusCircle className="w-4 h-4" />
            <span>New Analysis</span>
          </button>
        </div>
      </div>

      {/* 2. Four Key Image Views Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Card 1: Original X-ray */}
        <div className="card-surface rounded-2xl overflow-hidden shadow-sm flex flex-col">
          <div className="p-3 border-b border-slate-100 flex items-center justify-between">
            <span className="text-xs font-bold text-slate-800">Original X-ray</span>
          </div>
          <div className="relative aspect-square bg-black flex items-center justify-center p-1">
            <img
              src={study.image_assets.original}
              alt="Original X-ray"
              className="max-h-full max-w-full object-contain"
            />
          </div>
        </div>

        {/* Card 2: AI Heatmap */}
        <div className="card-surface rounded-2xl overflow-hidden shadow-sm flex flex-col">
          <div className="p-3 border-b border-slate-100 flex flex-col">
            <span className="text-xs font-bold text-slate-800">AI Heatmap</span>
            <span className="text-[10px] text-slate-400">What the AI focused on</span>
          </div>
          <div className="relative aspect-square bg-black flex items-center justify-center p-1">
            <img
              src={study.image_assets.original}
              alt="Base X-ray"
              className="max-h-full max-w-full object-contain"
            />
            <img
              src={study.image_assets.heatmap_overlay}
              alt="AI Heatmap Overlay"
              className="absolute inset-0 m-auto max-h-full max-w-full object-contain pointer-events-none mix-blend-screen opacity-80"
            />
          </div>
        </div>

        {/* Card 3: Enhanced Image */}
        <div className="card-surface rounded-2xl overflow-hidden shadow-sm flex flex-col">
          <div className="p-3 border-b border-slate-100 flex flex-col">
            <span className="text-xs font-bold text-slate-800">Enhanced Image</span>
            <span className="text-[10px] text-slate-400">Improved visibility</span>
          </div>
          <div className="relative aspect-square bg-black flex items-center justify-center p-1">
            <img
              src={study.image_assets.enhanced}
              alt="CLAHE Enhanced Image"
              className="max-h-full max-w-full object-contain"
            />
          </div>
        </div>

        {/* Card 4: Lung Mask */}
        <div className="card-surface rounded-2xl overflow-hidden shadow-sm flex flex-col">
          <div className="p-3 border-b border-slate-100 flex flex-col">
            <span className="text-xs font-bold text-slate-800">Lung Mask</span>
            <span className="text-[10px] text-slate-400">Detected lung region</span>
          </div>
          <div className="relative aspect-square bg-black flex items-center justify-center p-1">
            <img
              src={study.image_assets.overlay_mask}
              alt="Pulmonary Lung Mask"
              className="max-h-full max-w-full object-contain"
            />
          </div>
        </div>
      </div>

      {/* 3. Bottom Row: Detected Findings (Left) & Primary Finding (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left: Detected Findings Card (lg:col-span-7) */}
        <div className="lg:col-span-7 card-surface rounded-2xl p-5 space-y-4 shadow-sm">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Activity className="w-4 h-4 text-blue-600" />
              Detected Findings
            </h3>
            <span className="text-xs text-slate-400 font-medium">
              Calibrated Confidence
            </span>
          </div>

          <div className="space-y-3.5">
            {displayFindings.map((finding) => {
              const pct = finding.probability_pct;
              const isDetected = finding.is_detected;

              // Color scheme based on confidence
              let barColor = "bg-blue-500";
              let badgeColor = "bg-blue-50 text-blue-700 border-blue-200";
              let badgeText = "Low";

              if (pct >= 60 || finding.confidence_tier === "HIGH") {
                barColor = "bg-rose-500";
                badgeColor = "bg-rose-50 text-rose-700 border-rose-200";
                badgeText = "High";
              } else if (pct >= 35 || finding.confidence_tier === "MODERATE") {
                barColor = "bg-amber-500";
                badgeColor = "bg-amber-50 text-amber-700 border-amber-200";
                badgeText = "Moderate";
              }

              return (
                <div key={finding.disease} className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center space-x-2">
                      <span className={`font-semibold ${isDetected ? "text-slate-900 font-bold" : "text-slate-700"}`}>
                        {finding.disease}
                      </span>
                    </div>

                    <div className="flex items-center space-x-2.5">
                      <span className="font-mono font-bold text-slate-800">
                        {pct}%
                      </span>
                      <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${badgeColor}`}>
                        {badgeText}
                      </span>
                    </div>
                  </div>

                  {/* Clean progress bar */}
                  <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                    <div
                      className={`${barColor} h-2 rounded-full transition-all duration-500`}
                      style={{ width: `${Math.min(pct, 100)}%` }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <span>Showing top classified pathologies</span>
            <button
              onClick={() => onNavigateTab("findings")}
              className="text-blue-600 hover:text-blue-700 font-semibold flex items-center gap-1 transition"
            >
              <span>View all 14 conditions</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Right: Primary Finding Card (lg:col-span-5) */}
        <div className="lg:col-span-5 card-surface rounded-2xl p-5 space-y-4 shadow-sm flex flex-col justify-between">
          <div className="space-y-4">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Primary Finding
            </span>

            <div className="flex items-start space-x-3.5 pt-1">
              <div className="w-12 h-12 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center shrink-0">
                {isCardiomegaly ? (
                  <Heart className="w-6 h-6" />
                ) : (
                  <Activity className="w-6 h-6" />
                )}
              </div>

              <div className="space-y-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <h4 className="text-lg font-bold text-slate-900">
                    {topFinding?.is_detected ? `Likely ${topFinding.disease}` : "No Acute Abnormality"}
                  </h4>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200">
                    {study.classification.prediction_reliability} Reliability
                  </span>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed">
                  {topFinding?.is_detected
                    ? `The AI detected areas of increased probability in the thoracic region, consistent with ${topFinding.disease}.`
                    : "All 14 evaluated cardiopulmonary classes fall within standard non-acute limits."}
                </p>
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
            <button
              onClick={() => onNavigateTab("explainability")}
              className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1 transition group"
            >
              <span>View detailed explanation</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
            </button>

            <button
              onClick={() => onNavigateTab("chat")}
              className="text-xs font-semibold text-slate-600 hover:text-blue-600 flex items-center gap-1 transition"
            >
              <span>Ask AI Copilot</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
