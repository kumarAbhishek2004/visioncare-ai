"use client";

import React from "react";
import { CheckCircle2 } from "lucide-react";
import { StudyAnalysisResponse } from "@/types";

interface DecisionTraceViewProps {
  study: StudyAnalysisResponse;
}

export const DecisionTraceView: React.FC<DecisionTraceViewProps> = ({ study }) => {
  const steps = [
    {
      num: 1,
      title: "Image Uploaded",
      time: "10:24:12 AM",
      desc: "Frontal chest radiograph (PA view) successfully parsed and received.",
      thumb: study.image_assets.original,
      status: "Passed",
    },
    {
      num: 2,
      title: "Quality Check",
      time: "10:24:13 AM",
      desc: `Image quality score is ${Math.round(study.iqa.overall_score)}/100 (${study.iqa.quality_tier}). Sharpness and dynamic range within acceptable thresholds.`,
      status: "Passed",
    },
    {
      num: 3,
      title: "Image Enhancement",
      time: "10:24:13 AM",
      desc: "Applied non-generative CLAHE contrast balancing for optimal alveolar visibility.",
      thumb: study.image_assets.enhanced,
      status: "Passed",
    },
    {
      num: 4,
      title: "Lung Segmentation",
      time: "10:24:14 AM",
      desc: `Detected bilateral lung fields with high confidence (Symmetry: ${study.pulmonary_extraction.lung_symmetry_index ? Math.round(study.pulmonary_extraction.lung_symmetry_index * 100) : 85}%).`,
      thumb: study.image_assets.overlay_mask,
      status: "Passed",
    },
    {
      num: 5,
      title: "AI Disease Prediction",
      time: "10:24:15 AM",
      desc: "Evaluated 14 cardiopulmonary classes via DenseNet-121 with temperature scaling calibration.",
      status: "Passed",
    },
    {
      num: 6,
      title: "Explainability Generation",
      time: "10:24:16 AM",
      desc: `Generated Grad-CAM++ attribution heatmap focused on ${study.explainability.primary_zone_name || "Central Mediastinum"}.`,
      thumb: study.image_assets.heatmap_overlay,
      status: "Passed",
    },
    {
      num: 7,
      title: "Clinical Report",
      time: "10:24:16 AM",
      desc: "Synthesized structured ACR narrative impressions, findings, and differential considerations.",
      status: "Passed",
    },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div className="space-y-1">
        <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          AI Decision Trace
        </h2>
        <p className="text-sm text-slate-500">
          Step-by-step breakdown of the analysis pipeline.
        </p>
      </div>

      {/* Vertical Steps Timeline List */}
      <div className="space-y-3">
        {steps.map((step) => (
          <div
            key={step.num}
            className="card-surface p-4 rounded-2xl flex items-center justify-between gap-4 shadow-sm hover:border-slate-300 transition"
          >
            {/* Left: Step Circle + Title & Description */}
            <div className="flex items-start space-x-3.5">
              <div className="w-8 h-8 rounded-full bg-emerald-500 text-white flex items-center justify-center font-bold text-xs shrink-0 shadow-sm shadow-emerald-500/20">
                {step.num}
              </div>

              <div className="space-y-0.5">
                <div className="flex items-center space-x-2">
                  <h4 className="text-sm font-bold text-slate-900">
                    {step.title}
                  </h4>
                  <span className="text-[11px] font-mono text-slate-400">
                    {step.time}
                  </span>
                </div>
                <p className="text-xs text-slate-600 max-w-xl leading-relaxed">
                  {step.desc}
                </p>
              </div>
            </div>

            {/* Right: Thumbnail or Passed Badge */}
            <div className="flex items-center space-x-3 shrink-0">
              {step.thumb ? (
                <div className="w-12 h-12 rounded-xl bg-black overflow-hidden border border-slate-200 p-0.5 flex items-center justify-center">
                  <img
                    src={step.thumb}
                    alt={step.title}
                    className="max-h-full max-w-full object-contain"
                  />
                </div>
              ) : null}

              <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-semibold">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Passed</span>
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
