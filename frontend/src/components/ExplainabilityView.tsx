"use client";

import React, { useState } from "react";
import {
  MapPin,
  Eye,
  Maximize2,
  Stethoscope,
  Info,
  Sliders,
  Layers,
  Sparkles
} from "lucide-react";
import { StudyAnalysisResponse } from "@/types";

interface ExplainabilityViewProps {
  study: StudyAnalysisResponse;
}

export const ExplainabilityView: React.FC<ExplainabilityViewProps> = ({ study }) => {
  const [activeTab, setActiveTab] = useState<"visual" | "region" | "areas" | "patterns">("visual");
  const [heatmapWeight, setHeatmapWeight] = useState<number>(75);

  const primaryZone = study.explainability.primary_zone_name || "Bilateral Lungs";
  const primaryPct = study.explainability.primary_zone_percentage || 0;
  const targetDisease = study.explainability.target_pathology || "Primary Finding";
  const boxes = study.explainability.bounding_boxes || [];
  const topBox = boxes.length > 0 ? boxes[0] : null;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* 1. Header */}
      <div className="space-y-1">
        <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          Explainability
        </h2>
        <p className="text-sm text-slate-500">
          Understand what the AI saw and why it made this prediction.
        </p>
      </div>

      {/* 2. Secondary Tab Buttons */}
      <div className="flex space-x-1 sm:space-x-2 border-b border-slate-200 pb-2">
        <button
          onClick={() => setActiveTab("visual")}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
            activeTab === "visual"
              ? "bg-blue-600 text-white shadow-sm"
              : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
          }`}
        >
          Visual Explanation
        </button>
        <button
          onClick={() => setActiveTab("region")}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
            activeTab === "region"
              ? "bg-blue-600 text-white shadow-sm"
              : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
          }`}
        >
          Region Analysis
        </button>
        <button
          onClick={() => setActiveTab("areas")}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
            activeTab === "areas"
              ? "bg-blue-600 text-white shadow-sm"
              : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
          }`}
        >
          Affected Areas
        </button>
        <button
          onClick={() => setActiveTab("patterns")}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
            activeTab === "patterns"
              ? "bg-blue-600 text-white shadow-sm"
              : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
          }`}
        >
          Common Patterns
        </button>
      </div>

      {/* 3. Main Split View */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left: Large Radiograph with Interactive Heatmap Slider (lg:col-span-7) */}
        <div className="lg:col-span-7 card-surface rounded-2xl p-5 space-y-4 shadow-sm flex flex-col items-center">
          <div className="relative w-full aspect-square max-h-[500px] bg-black rounded-xl overflow-hidden flex items-center justify-center border border-slate-200 shadow-inner">
            {/* Base Image */}
            <img
              src={study.image_assets.original}
              alt="Base Radiograph"
              className="max-h-full max-w-full object-contain"
            />

            {/* Grad-CAM++ Heatmap Overlay */}
            <img
              src={study.image_assets.heatmap_overlay}
              alt="Heatmap Attribution"
              className="absolute inset-0 m-auto max-h-full max-w-full object-contain pointer-events-none mix-blend-screen transition-opacity duration-150"
              style={{ opacity: heatmapWeight / 100.0 }}
            />

            {/* Simulated Lesion Bounding Box Indicator */}
            {topBox && (
              <div
                className="absolute border-2 border-dashed border-amber-400 bg-amber-400/10 pointer-events-none rounded"
                style={{
                  left: "28%",
                  top: "45%",
                  width: "35%",
                  height: "30%",
                }}
              ></div>
            )}
          </div>

          {/* Interactive Opacity Slider */}
          <div className="w-full flex items-center justify-between space-x-4 pt-2 px-2 text-xs text-slate-500">
            <span className="font-semibold text-slate-700">Original</span>
            <input
              type="range"
              min="0"
              max="100"
              value={heatmapWeight}
              onChange={(e) => setHeatmapWeight(Number(e.target.value))}
              className="flex-1 h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
            <span className="font-semibold text-blue-600">AI Heatmap ({heatmapWeight}%)</span>
          </div>
        </div>

        {/* Right: "What the AI Focused On" Structured Card (lg:col-span-5) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="card-surface rounded-2xl p-6 space-y-5 shadow-sm">
            <div>
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-blue-600" />
                What the AI Focused On
              </h3>
              <p className="text-xs text-slate-500 mt-1">
                The highlighted area shows the region that most influenced the prediction.
              </p>
            </div>

            {/* 4 Structured Metric Rows */}
            <div className="space-y-4 text-xs">
              {/* Row 1: Location */}
              <div className="flex items-start space-x-3 p-3 rounded-xl bg-slate-50 border border-slate-100">
                <div className="w-8 h-8 rounded-lg bg-blue-100 text-blue-600 flex items-center justify-center shrink-0">
                  <MapPin className="w-4 h-4" />
                </div>
                <div>
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                    Location
                  </span>
                  <p className="font-semibold text-slate-800 text-sm mt-0.5">
                    {primaryZone} ({primaryPct}%)
                  </p>
                </div>
              </div>

              {/* Row 2: Appearance */}
              <div className="flex items-start space-x-3 p-3 rounded-xl bg-slate-50 border border-slate-100">
                <div className="w-8 h-8 rounded-lg bg-cyan-100 text-cyan-600 flex items-center justify-center shrink-0">
                  <Eye className="w-4 h-4" />
                </div>
                <div>
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                    Appearance
                  </span>
                  <p className="font-semibold text-slate-800 text-sm mt-0.5">
                    Increased opacity (whiter area) with focal attenuation
                  </p>
                </div>
              </div>

              {/* Row 3: Size */}
              <div className="flex items-start space-x-3 p-3 rounded-xl bg-slate-50 border border-slate-100">
                <div className="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-600 flex items-center justify-center shrink-0">
                  <Maximize2 className="w-4 h-4" />
                </div>
                <div>
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                    Estimated ROI Size
                  </span>
                  <p className="font-semibold text-slate-800 text-sm mt-0.5">
                    {topBox?.dimensions_cm
                      ? `${topBox.dimensions_cm.width_cm} cm × ${topBox.dimensions_cm.height_cm} cm`
                      : "Moderate anatomical area"}
                  </p>
                </div>
              </div>

              {/* Row 4: Common Causes */}
              <div className="flex items-start space-x-3 p-3 rounded-xl bg-slate-50 border border-slate-100">
                <div className="w-8 h-8 rounded-lg bg-rose-100 text-rose-600 flex items-center justify-center shrink-0">
                  <Stethoscope className="w-4 h-4" />
                </div>
                <div>
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                    Common Causes
                  </span>
                  <p className="font-semibold text-slate-800 text-sm mt-0.5">
                    {targetDisease}, Consolidation, or Infiltrative change
                  </p>
                </div>
              </div>
            </div>

            {/* Informational Callout Note */}
            <div className="p-3.5 rounded-xl bg-blue-50/70 border border-blue-200 text-xs text-blue-900 flex items-start space-x-2.5">
              <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
              <p className="leading-relaxed">
                <strong>Note:</strong> This heatmap shows where the AI looked, not a confirmed lesion.
                It visualizes mathematical activation to assist clinical verification.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
