"use client";

import React, { useState } from "react";
import { Scan, ImagePlus, SunMoon, RefreshCw } from "lucide-react";
import { StudyAnalysisResponse } from "@/types";

interface ViewportSyncProps {
  study: StudyAnalysisResponse | null;
  isLoading: boolean;
}

type ViewMode = "original" | "enhanced" | "bone" | "mask" | "caliper" | "cam";

export const ViewportSync: React.FC<ViewportSyncProps> = ({ study, isLoading }) => {
  const [viewMode, setViewMode] = useState<ViewMode>("cam");
  const [camOpacity, setCamOpacity] = useState<number>(70);
  const [isInverted, setIsInverted] = useState<boolean>(false);

  const getActiveImageSrc = () => {
    if (!study) return "";
    switch (viewMode) {
      case "original":
        return study.image_assets.original;
      case "enhanced":
        return study.image_assets.enhanced;
      case "bone":
        return study.image_assets.enhanced_bone || study.image_assets.enhanced;
      case "mask":
        return study.image_assets.overlay_mask;
      case "caliper":
        return study.image_assets.caliper_overlay || study.image_assets.original;
      case "cam":
        return study.image_assets.original;
    }
  };

  const getHudLabel = () => {
    switch (viewMode) {
      case "original":
        return "ORIGINAL RADIOGRAPH (PA)";
      case "enhanced":
        return "CLAHE DIAGNOSTIC OPTIMIZED";
      case "bone":
        return "BONE & PLEURAL EDGE SHARPENING";
      case "mask":
        return "PULMONARY PARENCHYMA MASK";
      case "caliper":
        return "CARDIOTHORACIC RATIO (CTR) BIOMETRICS";
      case "cam":
        return `${(study?.explainability?.xai_method || "GRAD-CAM++").toUpperCase()} ATTRIBUTION`;
    }
  };

  return (
    <div className="glass-panel rounded-xl p-4 flex flex-col flex-1 shadow-xl">
      {/* Viewport Top Bar */}
      <div className="flex items-center justify-between pb-3 border-b border-radDark-700">
        <div className="flex items-center space-x-2">
          <Scan className="w-5 h-5 text-cyan-400" />
          <h2 className="text-sm font-semibold tracking-wide uppercase text-slate-200">
            Diagnostic Multi-View Viewport
          </h2>
        </div>

        {/* View Mode Buttons */}
        <div className="flex bg-radDark-900 p-0.5 rounded-lg border border-radDark-700 text-xs">
          {(["original", "enhanced", "bone", "mask", "caliper", "cam"] as ViewMode[]).map((mode) => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              disabled={!study}
              className={`px-2.5 py-1 rounded font-medium transition ${
                viewMode === mode
                  ? "bg-blue-600 text-white"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              {mode === "original"
                ? "Original"
                : mode === "enhanced"
                ? "CLAHE"
                : mode === "bone"
                ? "Bone/Edge"
                : mode === "mask"
                ? "Lung Field"
                : mode === "caliper"
                ? "CTR Caliper"
                : "XAI Attrib"}
            </button>
          ))}
        </div>
      </div>

      {/* Main Canvas Viewport Area */}
      <div className="relative flex-1 min-h-[460px] bg-black rounded-lg mt-3 overflow-hidden border border-radDark-700 flex items-center justify-center">
        {isLoading && (
          <div className="absolute inset-0 bg-radDark-950/80 backdrop-blur-sm flex flex-col items-center justify-center z-30">
            <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-xs text-blue-300 font-mono mt-4 animate-pulse">
              Running Full Multi-Stage Inference Pipeline (&lt; 2.5s)...
            </p>
          </div>
        )}

        {!study && !isLoading ? (
          <div className="flex flex-col items-center justify-center text-slate-500 space-y-3 p-8 text-center">
            <div className="w-16 h-16 rounded-full bg-radDark-800 flex items-center justify-center border border-radDark-700">
              <ImagePlus className="w-8 h-8 text-slate-400" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-300">No Radiograph Active</p>
              <p className="text-xs text-slate-500 mt-1">
                Upload a chest radiograph or click "Load Sample" to begin AI CDS analysis.
              </p>
            </div>
          </div>
        ) : study ? (
          <>
            {/* Primary Base Image */}
            <img
              src={getActiveImageSrc()}
              alt="Active Viewport Scan"
              className="max-h-[520px] max-w-full object-contain select-none transition-all duration-150"
              style={{ filter: isInverted ? "invert(1)" : "none" }}
            />

            {/* Continuous Grad-CAM++ Overlay */}
            {viewMode === "cam" && (
              <img
                src={study.image_assets.heatmap_overlay}
                alt="Grad-CAM++ Overlay"
                className="absolute max-h-[520px] max-w-full object-contain pointer-events-none mix-blend-screen transition-opacity duration-150"
                style={{ opacity: camOpacity / 100.0 }}
              />
            )}

            {/* Diagnostic HUD Overlay */}
            <div className="absolute top-3 left-3 flex flex-col space-y-1 z-10 pointer-events-none">
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-black/60 backdrop-blur border border-white/10 text-cyan-400">
                {getHudLabel()}
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-black/60 backdrop-blur border border-white/10 text-slate-300">
                IQA: {study.iqa.overall_score}/100
              </span>
            </div>
          </>
        ) : null}
      </div>

      {/* Viewport Opacity & Filter Controls */}
      <div className="mt-3 flex items-center justify-between text-xs pt-2 border-t border-radDark-700">
        <div className="flex items-center space-x-3 w-1/2">
          <span className="text-slate-400 font-medium">CAM Opacity:</span>
          <input
            type="range"
            min="0"
            max="100"
            value={camOpacity}
            onChange={(e) => setCamOpacity(Number(e.target.value))}
            disabled={!study || viewMode !== "cam"}
            className="w-32 h-1.5 bg-radDark-700 rounded-lg appearance-none cursor-pointer accent-blue-500 disabled:opacity-40"
          />
          <span className="font-mono text-blue-400 w-8">{camOpacity}%</span>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsInverted(!isInverted)}
            disabled={!study}
            className="p-1.5 rounded hover:bg-radDark-700 text-slate-400 hover:text-white disabled:opacity-40"
            title="Invert Grayscale"
          >
            <SunMoon className="w-4 h-4" />
          </button>
          <button
            onClick={() => {
              setIsInverted(false);
              setCamOpacity(70);
              setViewMode("cam");
            }}
            disabled={!study}
            className="p-1.5 rounded hover:bg-radDark-700 text-slate-400 hover:text-white disabled:opacity-40"
            title="Reset Viewport"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
