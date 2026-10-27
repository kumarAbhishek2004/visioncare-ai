"use client";

import React, { useState } from "react";
import { Header } from "@/components/Header";
import { SafetyBanner } from "@/components/SafetyBanner";
import { ViewportSync } from "@/components/ViewportSync";
import { DifferentialsMatrix } from "@/components/DifferentialsMatrix";
import { ZoneDistribution } from "@/components/ZoneDistribution";
import { FindingsPanel } from "@/components/FindingsPanel";
import { DecisionTrace } from "@/components/DecisionTrace";
import { StudyAnalysisResponse } from "@/types";
import { analyzeRadiograph } from "@/lib/api";
import { Gauge } from "lucide-react";

export default function WorkstationPage() {
  const [study, setStudy] = useState<StudyAnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsLoading(true);
    setErrorMessage(null);
    try {
      const data = await analyzeRadiograph(
        file,
        `PT-NEW-${Math.floor(1000 + Math.random() * 9000)}`,
        58,
        "F",
        "PA"
      );
      setStudy(data);
    } catch (err: any) {
      setErrorMessage(err.message || "An unexpected error occurred during analysis.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoadSample = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      // Create synthetic frontal chest radiograph canvas
      const canvas = document.createElement("canvas");
      canvas.width = 512;
      canvas.height = 512;
      const ctx = canvas.getContext("2d");
      if (!ctx) throw new Error("Could not initialize 2D context");

      // Background
      ctx.fillStyle = "#191919";
      ctx.fillRect(0, 0, 512, 512);

      // Thorax ellipse
      ctx.fillStyle = "#6e6e6e";
      ctx.beginPath();
      ctx.ellipse(256, 256, 215, 230, 0, 0, Math.PI * 2);
      ctx.fill();

      // Lung parenchyma fields
      ctx.fillStyle = "#282828";
      ctx.beginPath();
      ctx.ellipse(160, 256, 80, 150, -0.08, 0, Math.PI * 2);
      ctx.fill();

      ctx.beginPath();
      ctx.ellipse(352, 256, 80, 150, 0.08, 0, Math.PI * 2);
      ctx.fill();

      // Focal focal Consolidation opacity in LLZ
      ctx.fillStyle = "#8c8c8c";
      ctx.beginPath();
      ctx.arc(150, 350, 32, 0, Math.PI * 2);
      ctx.fill();

      canvas.toBlob(async (blob) => {
        if (!blob) return;
        const sampleFile = new File([blob], "synthetic_sample_radiograph.png", {
          type: "image/png",
        });
        try {
          const data = await analyzeRadiograph(
            sampleFile,
            "PT-RAD-9042",
            62,
            "M",
            "PA"
          );
          setStudy(data);
        } catch (err: any) {
          setErrorMessage(err.message || "Failed to process sample radiograph.");
        } finally {
          setIsLoading(false);
        }
      }, "image/png");
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to construct sample image.");
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col font-sans selection:bg-blue-600 selection:text-white">
      {/* Top Clinical Header */}
      <Header
        study={study}
        onUpload={handleFileUpload}
        onLoadSample={handleLoadSample}
        isLoading={isLoading}
      />

      {/* Safety Triage Banner */}
      {study && (
        <SafetyBanner classification={study.classification} iqa={study.iqa} />
      )}

      {/* Error alert toast */}
      {errorMessage && (
        <div className="bg-red-950/90 border-b border-red-800 text-red-200 px-6 py-2 text-xs flex items-center justify-between">
          <span>{errorMessage}</span>
          <button
            onClick={() => setErrorMessage(null)}
            className="text-red-400 hover:text-white font-bold ml-4"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Main 3-Column Workstation Grid */}
      <main className="flex-1 grid grid-cols-1 xl:grid-cols-12 gap-4 p-4 min-h-0 overflow-y-auto">
        {/* Left Column: Viewport & IQA (Col 1-6) */}
        <div className="xl:col-span-6 flex flex-col space-y-4">
          <ViewportSync study={study} isLoading={isLoading} />

          {/* IQA Strip */}
          <div className="glass-panel rounded-xl p-4 shadow-xl">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5 mb-3">
              <Gauge className="w-4 h-4 text-emerald-400" />
              Image Quality Assessment (IQA) & Pre-Screening
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
              <div className="bg-radDark-900 p-2.5 rounded-lg border border-radDark-700">
                <p className="text-[10px] text-slate-400 uppercase">Composite Score</p>
                <p className="text-base font-bold text-slate-200 mt-0.5">
                  {study?.iqa?.overall_score != null ? `${study.iqa.overall_score} / 100` : "--"}
                </p>
              </div>
              <div className="bg-radDark-900 p-2.5 rounded-lg border border-radDark-700">
                <p className="text-[10px] text-slate-400 uppercase">
                  Laplacian Sharpness
                </p>
                <p className="text-base font-bold text-slate-200 mt-0.5">
                  {study?.iqa?.laplacian_variance != null
                    ? Number(study.iqa.laplacian_variance).toFixed(1)
                    : "--"}
                </p>
              </div>
              <div className="bg-radDark-900 p-2.5 rounded-lg border border-radDark-700">
                <p className="text-[10px] text-slate-400 uppercase">
                  Michelson Contrast
                </p>
                <p className="text-base font-bold text-slate-200 mt-0.5">
                  {study?.iqa?.michelson_contrast != null
                    ? `${(Number(study.iqa.michelson_contrast) * 100).toFixed(1)}%`
                    : "--"}
                </p>
              </div>
              <div className="bg-radDark-900 p-2.5 rounded-lg border border-radDark-700">
                <p className="text-[10px] text-slate-400 uppercase">Dynamic Range</p>
                <p className="text-base font-bold text-slate-200 mt-0.5">
                  {study?.iqa?.dynamic_range != null ? `${study.iqa.dynamic_range} Gy` : "--"}
                </p>
              </div>
            </div>
          </div>

          {/* CTR Biometrics & ED STAT Triage Strip */}
          {study && (
            <div className="glass-panel rounded-xl p-4 shadow-xl">
              <div className="flex items-center justify-between pb-2 border-b border-radDark-700 mb-3">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                  Cardiothoracic Ratio (CTR) & ED STAT Triage
                </h3>
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                    study.ctr?.is_cardiomegaly
                      ? "bg-red-950/60 text-red-400 border-red-800"
                      : "bg-emerald-950/60 text-emerald-400 border-emerald-800"
                  }`}
                >
                  CTR: {study.ctr ? `${study.ctr.ctr_percentage}% (${study.ctr.is_cardiomegaly ? "CARDIOMEGALY" : "NORMAL"})` : "--"}
                </span>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-xs">
                <div className="bg-radDark-900 p-2.5 rounded-lg border border-radDark-700">
                  <p className="text-[10px] text-slate-400 uppercase">CTR Percentage</p>
                  <p className="text-base font-bold text-slate-200 mt-0.5">
                    {study.ctr ? `${study.ctr.ctr_percentage}%` : "--"}
                  </p>
                </div>
                <div className="bg-radDark-900 p-2.5 rounded-lg border border-radDark-700">
                  <p className="text-[10px] text-slate-400 uppercase">Heart Diameter</p>
                  <p className="text-base font-bold text-slate-200 mt-0.5">
                    {study.ctr ? `${study.ctr.cardiac_diameter_cm} cm` : "--"}
                  </p>
                </div>
                <div className="bg-radDark-900 p-2.5 rounded-lg border border-radDark-700">
                  <p className="text-[10px] text-slate-400 uppercase">Thorax Diameter</p>
                  <p className="text-base font-bold text-slate-200 mt-0.5">
                    {study.ctr ? `${study.ctr.thoracic_diameter_cm} cm` : "--"}
                  </p>
                </div>
                <div className="bg-radDark-900 p-2.5 rounded-lg border border-radDark-700">
                  <p className="text-[10px] text-slate-400 uppercase">Lung Symmetry</p>
                  <p className="text-base font-bold text-cyan-400 mt-0.5">
                    {study.pulmonary_extraction.lung_symmetry_index !== undefined
                      ? `${(study.pulmonary_extraction.lung_symmetry_index * 100).toFixed(0)}%`
                      : "--"}
                  </p>
                </div>
                <div className="bg-radDark-900 p-2.5 rounded-lg border border-radDark-700">
                  <p className="text-[10px] text-slate-400 uppercase">ED STAT Priority</p>
                  <p
                    className={`text-base font-bold mt-0.5 ${
                      study.emergency_triage?.priority_tier === "STAT_CRITICAL"
                        ? "text-red-500 animate-pulse"
                        : study.emergency_triage?.priority_tier === "URGENT"
                        ? "text-amber-400"
                        : "text-emerald-400"
                    }`}
                  >
                    {study.emergency_triage?.priority_tier?.replace("_", " ") || "ROUTINE"}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Middle Column: 14-Disease Differentials & 5-Zone Localization (Col 7-9) */}
        <div className="xl:col-span-3 flex flex-col space-y-4">
          <DifferentialsMatrix
            findings={study?.classification.all_predictions || study?.classification.all_findings}
          />
          <ZoneDistribution explainability={study?.explainability} />
        </div>

        {/* Right Column: ACR Clinical Report & Decision Trace (Col 10-12) */}
        <div className="xl:col-span-3 flex flex-col space-y-4">
          <FindingsPanel report={study?.clinical_report} />
          <DecisionTrace trace={study?.decision_trace} />
        </div>
      </main>
    </div>
  );
}
