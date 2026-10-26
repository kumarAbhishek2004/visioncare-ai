"use client";

import React from "react";
import { CheckCircle2, AlertTriangle } from "lucide-react";
import { ClassificationData, IQAData } from "@/types";

interface SafetyBannerProps {
  classification: ClassificationData;
  iqa: IQAData;
}

export const SafetyBanner: React.FC<SafetyBannerProps> = ({ classification, iqa }) => {
  const isReady = classification.safety_triage === "ASSISTED_REVIEW_READY";

  return (
    <div
      className={`px-6 py-2.5 border-b text-xs flex items-center justify-between transition-all duration-300 ${
        isReady
          ? "bg-emerald-950/70 border-emerald-800 text-emerald-200"
          : "bg-amber-950/80 border-amber-800 text-amber-200"
      }`}
    >
      <div className="flex items-center space-x-3">
        <div className="p-1 rounded">
          {isReady ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          ) : (
            <AlertTriangle className="w-5 h-5 text-amber-400" />
          )}
        </div>
        <div>
          <span className="font-bold text-sm tracking-wide">
            {isReady ? "ASSISTED REVIEW READY" : "MANUAL REVIEW MANDATORY"}
          </span>
          <span className="ml-2 text-slate-300">
            {isReady
              ? "Model predictions exceed reliability thresholds. Calibrated probabilities ready for radiologist verification."
              : "Borderline confidence or high diagnostic uncertainty detected. Manual physician review is clinically mandated."}
          </span>
        </div>
      </div>
      <div className="flex items-center space-x-4">
        <span className="font-mono px-2 py-0.5 rounded bg-black/30">
          IQA: {iqa.overall_score}/100 ({iqa.quality_tier})
        </span>
        <span className="font-mono px-2 py-0.5 rounded bg-black/30">
          RELIABILITY: {classification.prediction_reliability}
        </span>
      </div>
    </div>
  );
};
