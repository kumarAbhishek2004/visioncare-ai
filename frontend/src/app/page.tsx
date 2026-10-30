"use client";

import React, { useState } from "react";
import { Navbar } from "@/components/Navbar";
import { HomePage } from "@/components/HomePage";
import { UploadView } from "@/components/UploadView";
import { ResultsOverview } from "@/components/ResultsOverview";
import { ExplainabilityView } from "@/components/ExplainabilityView";
import { DecisionTraceView } from "@/components/DecisionTraceView";
import { ClinicalReportView } from "@/components/ClinicalReportView";
import { ClinicalChatbot } from "@/components/ClinicalChatbot";
import { StudyAnalysisResponse, FindingItem } from "@/types";
import { analyzeRadiograph } from "@/lib/api";
import {
  Activity,
  Heart,
  Eye,
  FileText,
  Clock,
  Layers,
  RotateCcw,
  CheckCircle2,
  AlertCircle,
  FileDown,
  Info,
  ShieldCheck,
  Stethoscope,
  Scan,
  Gauge,
  MessageSquare
} from "lucide-react";

type MainNavTab = "home" | "analyze" | "reports" | "studies" | "about";
type ResultsTab = "overview" | "explainability" | "trace" | "chat" | "findings" | "technical";

export default function App() {
  const [activeNav, setActiveNav] = useState<MainNavTab>("home");
  const [activeResultsTab, setActiveResultsTab] = useState<ResultsTab>("overview");
  const [isFloatingChatOpen, setIsFloatingChatOpen] = useState<boolean>(false);
  const [study, setStudy] = useState<StudyAnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [loadingStep, setLoadingStep] = useState<string>("Analyzing radiograph...");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Archive of analyzed studies in this session
  const [studiesHistory, setStudiesHistory] = useState<
    Array<{ id: string; study: StudyAnalysisResponse; timestamp: string }>
  >([]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsLoading(true);
    setLoadingStep("Validating DICOM/PNG radiograph...");
    setErrorMessage(null);

    try {
      setTimeout(() => setLoadingStep("Segmenting pulmonary lung fields..."), 600);
      setTimeout(() => setLoadingStep("Running 14-disease DenseNet-121 inference..."), 1200);
      setTimeout(() => setLoadingStep("Synthesizing Grad-CAM++ attribution heatmaps..."), 1800);

      const patientId = `PT-${Math.floor(1000 + Math.random() * 9000)}`;
      const data = await analyzeRadiograph(file, patientId, 62, "M", "PA");

      setStudy(data);
      setActiveResultsTab("overview");

      // Add to session studies history
      setStudiesHistory((prev) => [
        {
          id: data.study_id,
          study: data,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
        ...prev.filter((item) => item.id !== data.study_id),
      ]);
    } catch (err: any) {
      setErrorMessage(err.message || "An unexpected error occurred during radiograph analysis.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectSample = async (
    sampleType: "normal" | "pneumonia" | "effusion" | "cardiomegaly" | "pneumothorax"
  ) => {
    setIsLoading(true);
    setLoadingStep(`Loading ${sampleType} example radiograph...`);
    setErrorMessage(null);

    const sampleFileMap: Record<string, string> = {
      normal: "/samples/sample_1_normal_chest.png",
      effusion: "/samples/sample_2_pleural_effusion.png",
      cardiomegaly: "/samples/sample_3_cardiomegaly.png",
      pneumonia: "/samples/sample_4_pneumonia_consolidation.png",
      pneumothorax: "/samples/sample_5_pneumothorax.png",
    };

    try {
      let fileToSend: File | null = null;
      try {
        const response = await fetch(sampleFileMap[sampleType]);
        if (response.ok) {
          const blob = await response.blob();
          fileToSend = new File([blob], `sample_${sampleType}.png`, { type: "image/png" });
        }
      } catch (fetchErr) {
        // Fallback to canvas generation
      }

      // If file was fetched successfully
      if (fileToSend) {
        setTimeout(() => setLoadingStep("Running DenseNet-121 multi-label inference..."), 700);
        setTimeout(() => setLoadingStep("Calculating Grad-CAM++ & anatomical zones..."), 1400);

        const data = await analyzeRadiograph(
          fileToSend,
          sampleType === "cardiomegaly" ? "PT-CARD-8812" : `PT-SAMPLE-${Math.floor(1000 + Math.random() * 9000)}`,
          sampleType === "cardiomegaly" ? 68 : 55,
          sampleType === "cardiomegaly" ? "M" : "F",
          "PA"
        );
        setStudy(data);
        setActiveResultsTab("overview");
        setStudiesHistory((prev) => [
          {
            id: data.study_id,
            study: data,
            timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          },
          ...prev.filter((item) => item.id !== data.study_id),
        ]);
        return;
      }

      // 2. Offscreen Canvas fallback
      const canvas = document.createElement("canvas");
      canvas.width = 512;
      canvas.height = 512;
      const ctx = canvas.getContext("2d");
      if (!ctx) throw new Error("Could not initialize 2D context");

      ctx.fillStyle = "#161616";
      ctx.fillRect(0, 0, 512, 512);

      // Thorax ellipse contour
      ctx.fillStyle = "#6e6e6e";
      ctx.beginPath();
      ctx.ellipse(256, 256, 215, 230, 0, 0, Math.PI * 2);
      ctx.fill();

      // Lung airfields
      ctx.fillStyle = "#282828";
      ctx.beginPath();
      ctx.ellipse(160, 256, 80, 150, -0.08, 0, Math.PI * 2);
      ctx.fill();

      ctx.beginPath();
      ctx.ellipse(352, 256, 80, 150, 0.08, 0, Math.PI * 2);
      ctx.fill();

      // Mediastinum & Spine
      ctx.fillStyle = "#737373";
      ctx.fillRect(235, 60, 42, 430);

      // Cardiac Silhouette
      const cardiacRadius = sampleType === "cardiomegaly" ? 135 : 85;
      ctx.fillStyle = "#8a8a8a";
      ctx.beginPath();
      ctx.ellipse(265, 310, cardiacRadius, 75, 0.2, 0, Math.PI * 2);
      ctx.fill();

      // Diaphragm domes
      ctx.fillStyle = "#787878";
      ctx.beginPath();
      ctx.ellipse(160, 410, 95, 45, 0, 0, Math.PI);
      ctx.fill();

      ctx.beginPath();
      ctx.ellipse(352, 415, 95, 45, 0, 0, Math.PI);
      ctx.fill();

      // Specific Pathologies
      if (sampleType === "effusion") {
        ctx.fillStyle = "#9c9c9c";
        ctx.beginPath();
        ctx.ellipse(125, 385, 60, 45, 0, 0, Math.PI * 2);
        ctx.fill();
      } else if (sampleType === "pneumonia") {
        ctx.fillStyle = "#969696";
        ctx.beginPath();
        ctx.arc(360, 320, 38, 0, Math.PI * 2);
        ctx.fill();
      }

      ctx.filter = "blur(6px)";
      ctx.drawImage(canvas, 0, 0);
      ctx.filter = "none";

      canvas.toBlob(async (blob) => {
        if (!blob) return;
        const sampleFile = new File([blob], `sample_${sampleType}.png`, { type: "image/png" });
        const data = await analyzeRadiograph(
          sampleFile,
          `PT-${sampleType.toUpperCase().slice(0, 4)}-${Math.floor(1000 + Math.random() * 9000)}`,
          55,
          "F",
          "PA"
        );
        setStudy(data);
        setActiveResultsTab("overview");
        setStudiesHistory((prev) => [
          {
            id: data.study_id,
            study: data,
            timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          },
          ...prev.filter((item) => item.id !== data.study_id),
        ]);
      }, "image/png");
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to load sample image.");
    } finally {
      setIsLoading(false);
    }
  };

  const allFindings: FindingItem[] =
    study ? study.classification.all_predictions || study.classification.all_findings || [] : [];

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-900 flex flex-col font-sans selection:bg-blue-600 selection:text-white relative overflow-x-hidden">
      {/* Precision Ambient Background Atmosphere */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0 bg-dots-subtle opacity-70"></div>
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute -top-36 left-1/2 -translate-x-1/2 w-[850px] h-[450px] bg-gradient-to-b from-blue-400/15 via-cyan-400/8 to-transparent blur-3xl rounded-full"></div>
        <div className="absolute top-1/3 -left-48 w-80 h-80 bg-blue-300/10 blur-3xl rounded-full animate-pulse-glow"></div>
        <div className="absolute top-2/3 -right-48 w-80 h-80 bg-cyan-300/10 blur-3xl rounded-full animate-pulse-glow"></div>
      </div>

      {/* 1. Global Navigation Bar */}
      <div className="relative z-50">
        <Navbar
          activeNav={activeNav}
          onNavChange={(nav) => setActiveNav(nav)}
          hasStudy={!!study}
        />
      </div>

      {/* 2. Global Error Banner */}
      {errorMessage && (
        <div className="bg-rose-50 border-b border-rose-200 text-rose-800 px-6 py-3 text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <button
            onClick={() => setErrorMessage(null)}
            className="text-rose-700 font-bold hover:underline ml-4"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* 3. Global Loading Overlay (When Processing Radiograph) */}
      {isLoading && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-8 max-w-sm w-full shadow-2xl border border-slate-200 text-center space-y-4 animate-scale-in">
            <div className="w-16 h-16 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto shadow-inner animate-pulse">
              <Activity className="w-8 h-8" />
            </div>
            <div className="space-y-1">
              <h3 className="text-base font-bold text-slate-900">Processing Radiograph</h3>
              <p className="text-xs text-slate-500">{loadingStep}</p>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
              <div className="bg-blue-600 h-2 rounded-full w-2/3 animate-pulse"></div>
            </div>
          </div>
        </div>
      )}

      {/* 4. Main View Routing */}
      <div className="flex-1 relative z-10">
        {/* Page 1: Landing / Home */}
        {activeNav === "home" && (
          <HomePage onGetStarted={() => setActiveNav("analyze")} />
        )}

        {/* Page 2: Analyze (Upload -> Results) */}
        {activeNav === "analyze" && (
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
            {!study ? (
              // Screen 2: Clean Upload View
              <UploadView
                onUpload={handleFileUpload}
                onSelectSample={handleSelectSample}
                isLoading={isLoading}
              />
            ) : (
              // Results Presentation with Sub-Tabs
              <div className="space-y-6">
                {/* Results Navigation Bar */}
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
                  <div className="flex items-center space-x-1 sm:space-x-2 overflow-x-auto w-full sm:w-auto">
                    <button
                      onClick={() => setActiveResultsTab("overview")}
                      className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-1.5 ${
                        activeResultsTab === "overview"
                          ? "bg-blue-600 text-white shadow-sm shadow-blue-500/20"
                          : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                      }`}
                    >
                      <Activity className="w-4 h-4" />
                      <span>Overview</span>
                    </button>

                    <button
                      onClick={() => setActiveResultsTab("explainability")}
                      className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-1.5 ${
                        activeResultsTab === "explainability"
                          ? "bg-blue-600 text-white shadow-sm shadow-blue-500/20"
                          : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                      }`}
                    >
                      <Eye className="w-4 h-4" />
                      <span>Explainability</span>
                    </button>

                    <button
                      onClick={() => setActiveResultsTab("trace")}
                      className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-1.5 ${
                        activeResultsTab === "trace"
                          ? "bg-blue-600 text-white shadow-sm shadow-blue-500/20"
                          : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                      }`}
                    >
                      <Clock className="w-4 h-4" />
                      <span>Decision Trace</span>
                    </button>

                    <button
                      onClick={() => setActiveResultsTab("chat")}
                      className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-1.5 ${
                        activeResultsTab === "chat"
                          ? "bg-blue-600 text-white shadow-sm shadow-blue-500/20"
                          : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                      }`}
                    >
                      <MessageSquare className="w-4 h-4" />
                      <span>AI Copilot Chat</span>
                    </button>

                    <button
                      onClick={() => setActiveResultsTab("findings")}
                      className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-1.5 ${
                        activeResultsTab === "findings"
                          ? "bg-blue-600 text-white shadow-sm shadow-blue-500/20"
                          : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                      }`}
                    >
                      <Layers className="w-4 h-4" />
                      <span>Detailed Findings</span>
                    </button>

                    <button
                      onClick={() => setActiveResultsTab("technical")}
                      className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-1.5 ${
                        activeResultsTab === "technical"
                          ? "bg-blue-600 text-white shadow-sm shadow-blue-500/20"
                          : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                      }`}
                    >
                      <Gauge className="w-4 h-4" />
                      <span>Technical Details</span>
                    </button>
                  </div>

                  {/* Actions Right */}
                  <div className="flex items-center space-x-2 self-end sm:self-auto">
                    <button
                      onClick={() => setActiveNav("reports")}
                      className="inline-flex items-center space-x-1.5 bg-white hover:bg-slate-50 text-slate-700 font-semibold text-xs px-3.5 py-2 rounded-xl border border-slate-200 shadow-sm transition"
                    >
                      <FileText className="w-3.5 h-3.5 text-blue-600" />
                      <span>View Full Report</span>
                    </button>

                    <button
                      onClick={() => setStudy(null)}
                      className="inline-flex items-center space-x-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs px-3.5 py-2 rounded-xl border border-slate-200 transition"
                    >
                      <RotateCcw className="w-3.5 h-3.5" />
                      <span>New Scan</span>
                    </button>
                  </div>
                </div>

                {/* Sub-Tab 1: Screen 3 — Results Overview */}
                {activeResultsTab === "overview" && (
                  <ResultsOverview
                    study={study}
                    onNewAnalysis={() => setStudy(null)}
                    onNavigateTab={(tab) => {
                      if (tab === "explainability") setActiveResultsTab("explainability");
                      else if (tab === "trace") setActiveResultsTab("trace");
                      else if (tab === "chat") setActiveResultsTab("chat");
                      else if (tab === "findings") setActiveResultsTab("findings");
                      else if (tab === "technical") setActiveResultsTab("technical");
                      else setActiveResultsTab("overview");
                    }}
                  />
                )}

                {/* Sub-Tab 2: Screen 4 — Visual Explainability */}
                {activeResultsTab === "explainability" && (
                  <ExplainabilityView study={study} />
                )}

                {/* Sub-Tab 3: Screen 5 — AI Decision Trace */}
                {activeResultsTab === "trace" && (
                  <DecisionTraceView study={study} />
                )}

                {/* Sub-Tab 4: Interactive AI Copilot Chatbot */}
                {activeResultsTab === "chat" && (
                  <ClinicalChatbot
                    study={study}
                    onBackToOverview={() => setActiveResultsTab("overview")}
                  />
                )}

                {/* Sub-Tab 4: Detailed 14-Disease Breakdown Table */}
                {activeResultsTab === "findings" && (
                  <div className="card-surface p-6 rounded-3xl shadow-sm space-y-6">
                    <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                      <div>
                        <h3 className="text-lg font-bold text-slate-900">
                          14-Disease Radiographic Evaluation
                        </h3>
                        <p className="text-xs text-slate-500">
                          DenseNet-121 calibrated probabilities for all NIH ChestX-ray14 thoracic pathologies.
                        </p>
                      </div>
                      <span className="text-xs font-semibold px-3 py-1 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                        Multi-Label Classification
                      </span>
                    </div>

                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead>
                          <tr className="border-b border-slate-200 text-slate-500 font-semibold">
                            <th className="pb-3 px-2">Pathology</th>
                            <th className="pb-3 px-2">Calibrated Probability</th>
                            <th className="pb-3 px-2">Confidence Level</th>
                            <th className="pb-3 px-2">Detection Threshold</th>
                            <th className="pb-3 px-2">Status</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {allFindings.map((finding) => (
                            <tr key={finding.disease} className="hover:bg-slate-50/80 transition">
                              <td className="py-3 px-2 font-bold text-slate-800">
                                {finding.disease}
                              </td>
                              <td className="py-3 px-2">
                                <div className="flex items-center space-x-2">
                                  <div className="w-24 bg-slate-100 rounded-full h-2 overflow-hidden">
                                    <div
                                      className={`h-2 rounded-full ${
                                        finding.is_detected ? "bg-rose-500" : "bg-blue-500"
                                      }`}
                                      style={{ width: `${Math.min(finding.probability_pct, 100)}%` }}
                                    ></div>
                                  </div>
                                  <span className="font-mono font-bold text-slate-700">
                                    {finding.probability_pct}%
                                  </span>
                                </div>
                              </td>
                              <td className="py-3 px-2">
                                <span
                                  className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                                    finding.confidence_tier === "HIGH"
                                      ? "bg-rose-50 text-rose-700 border-rose-200"
                                      : finding.confidence_tier === "MODERATE"
                                      ? "bg-amber-50 text-amber-700 border-amber-200"
                                      : "bg-slate-50 text-slate-600 border-slate-200"
                                  }`}
                                >
                                  {finding.confidence_tier}
                                </span>
                              </td>
                              <td className="py-3 px-2 font-mono text-slate-500">
                                {(finding.threshold * 100).toFixed(0)}%
                              </td>
                              <td className="py-3 px-2">
                                {finding.is_detected ? (
                                  <span className="text-rose-600 font-bold flex items-center gap-1">
                                    <AlertCircle className="w-3.5 h-3.5" /> Detected
                                  </span>
                                ) : (
                                  <span className="text-emerald-600 font-medium flex items-center gap-1">
                                    <CheckCircle2 className="w-3.5 h-3.5" /> Within Limits
                                  </span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Sub-Tab 5: Technical Details & CTR Biometrics */}
                {activeResultsTab === "technical" && (
                  <div className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* Card 1: Cardiothoracic Ratio (CTR) Caliper Biometrics */}
                      <div className="card-surface p-6 rounded-3xl shadow-sm space-y-4">
                        <div className="flex items-center space-x-2 text-rose-600 font-bold text-sm">
                          <Heart className="w-5 h-5" />
                          <span>Cardiothoracic Ratio (CTR) Biometrics</span>
                        </div>
                        <p className="text-xs text-slate-500">
                          Automated transverse cardiac diameter caliper measurement divided by internal thoracic diameter.
                        </p>
                        <div className="grid grid-cols-2 gap-3 text-xs pt-2">
                          <div className="p-3 rounded-2xl bg-slate-50 border border-slate-100">
                            <span className="text-slate-400 text-[10px] uppercase font-bold">CTR Ratio</span>
                            <p className="text-xl font-extrabold text-slate-900 mt-0.5">
                              {study.ctr?.ctr_percentage}%
                            </p>
                          </div>
                          <div className="p-3 rounded-2xl bg-slate-50 border border-slate-100">
                            <span className="text-slate-400 text-[10px] uppercase font-bold">Cardiac Diameter</span>
                            <p className="text-xl font-extrabold text-slate-900 mt-0.5">
                              {study.ctr?.cardiac_diameter_cm} cm
                            </p>
                          </div>
                          <div className="p-3 rounded-2xl bg-slate-50 border border-slate-100">
                            <span className="text-slate-400 text-[10px] uppercase font-bold">Thoracic Diameter</span>
                            <p className="text-xl font-extrabold text-slate-900 mt-0.5">
                              {study.ctr?.thoracic_diameter_cm} cm
                            </p>
                          </div>
                          <div className="p-3 rounded-2xl bg-slate-50 border border-slate-100">
                            <span className="text-slate-400 text-[10px] uppercase font-bold">Cardiomegaly Status</span>
                            <p className="text-xl font-extrabold text-slate-900 mt-0.5">
                              {study.ctr?.is_cardiomegaly ? "Positive (>50%)" : "Negative (≤50%)"}
                            </p>
                          </div>
                        </div>
                      </div>

                      {/* Card 2: Image Quality Assessment (IQA) */}
                      <div className="card-surface p-6 rounded-3xl shadow-sm space-y-4">
                        <div className="flex items-center space-x-2 text-emerald-600 font-bold text-sm">
                          <Gauge className="w-5 h-5" />
                          <span>Image Quality Assessment (IQA)</span>
                        </div>
                        <p className="text-xs text-slate-500">
                          Technical exposure, sharpness, and dynamic range evaluation.
                        </p>
                        <div className="grid grid-cols-2 gap-3 text-xs pt-2">
                          <div className="p-3 rounded-2xl bg-slate-50 border border-slate-100">
                            <span className="text-slate-400 text-[10px] uppercase font-bold">Overall Score</span>
                            <p className="text-xl font-extrabold text-slate-900 mt-0.5">
                              {Math.round(study.iqa.overall_score)} / 100
                            </p>
                          </div>
                          <div className="p-3 rounded-2xl bg-slate-50 border border-slate-100">
                            <span className="text-slate-400 text-[10px] uppercase font-bold">Quality Tier</span>
                            <p className="text-xl font-extrabold text-emerald-700 mt-0.5">
                              {study.iqa.quality_tier}
                            </p>
                          </div>
                          <div className="p-3 rounded-2xl bg-slate-50 border border-slate-100">
                            <span className="text-slate-400 text-[10px] uppercase font-bold">Laplacian Sharpness</span>
                            <p className="text-xl font-extrabold text-slate-900 mt-0.5">
                              {study.iqa.laplacian_variance != null ? Number(study.iqa.laplacian_variance).toFixed(1) : "--"}
                            </p>
                          </div>
                          <div className="p-3 rounded-2xl bg-slate-50 border border-slate-100">
                            <span className="text-slate-400 text-[10px] uppercase font-bold">Dynamic Range</span>
                            <p className="text-xl font-extrabold text-slate-900 mt-0.5">
                              {study.iqa.dynamic_range || 255} Gy
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Page 3: Screen 6 — Clinical Report */}
        {activeNav === "reports" && (
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {study ? (
              <ClinicalReportView study={study} />
            ) : (
              <div className="card-surface p-12 rounded-3xl max-w-xl mx-auto text-center space-y-4 shadow-sm border border-slate-200">
                <div className="w-16 h-16 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto">
                  <FileText className="w-8 h-8" />
                </div>
                <div className="space-y-1">
                  <h3 className="text-lg font-bold text-slate-900">No Active Report</h3>
                  <p className="text-xs text-slate-500 max-w-sm mx-auto">
                    Upload or select a chest X-ray in the Analyze section to generate an automated clinical impression and report.
                  </p>
                </div>
                <button
                  onClick={() => setActiveNav("analyze")}
                  className="inline-flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs px-5 py-2.5 rounded-xl shadow-sm transition"
                >
                  <Activity className="w-4 h-4" />
                  <span>Go to Analyze</span>
                </button>
              </div>
            )}
          </div>
        )}

        {/* Page 4: Studies Archive */}
        {activeNav === "studies" && (
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 animate-fade-in">
            <div className="space-y-1">
              <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                Studies Archive
              </h2>
              <p className="text-sm text-slate-500">
                Recent chest radiographs analyzed during this diagnostic session.
              </p>
            </div>

            {studiesHistory.length === 0 && !study ? (
              <div className="card-surface p-12 rounded-3xl text-center space-y-4 shadow-sm">
                <div className="w-16 h-16 rounded-2xl bg-slate-50 text-slate-400 flex items-center justify-center mx-auto">
                  <Scan className="w-8 h-8" />
                </div>
                <div className="space-y-1">
                  <h3 className="text-base font-bold text-slate-800">No Studies Found</h3>
                  <p className="text-xs text-slate-400">
                    Your analyzed radiographic studies will appear here.
                  </p>
                </div>
                <button
                  onClick={() => setActiveNav("analyze")}
                  className="inline-flex items-center space-x-2 bg-blue-600 text-white text-xs font-semibold px-4 py-2 rounded-xl"
                >
                  <span>Start New Analysis</span>
                </button>
              </div>
            ) : (
              <div className="card-surface rounded-3xl overflow-hidden shadow-sm border border-slate-200">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-500 font-semibold">
                        <th className="py-3 px-4">Patient ID</th>
                        <th className="py-3 px-4">View</th>
                        <th className="py-3 px-4">Time</th>
                        <th className="py-3 px-4">Primary Finding</th>
                        <th className="py-3 px-4">CTR</th>
                        <th className="py-3 px-4">Quality</th>
                        <th className="py-3 px-4 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {studiesHistory.map((item) => {
                        const topFinding =
                          item.study.classification.all_predictions?.find((f) => f.is_detected) ||
                          item.study.classification.all_predictions?.[0];
                        return (
                          <tr key={item.id} className="hover:bg-slate-50/50 transition">
                            <td className="py-3.5 px-4 font-mono font-bold text-slate-800">
                              {item.study.patient_id}
                            </td>
                            <td className="py-3.5 px-4 font-semibold text-slate-600">
                              {item.study.demographics.view_position || "PA"}
                            </td>
                            <td className="py-3.5 px-4 text-slate-500">{item.timestamp}</td>
                            <td className="py-3.5 px-4">
                              <span
                                className={`px-2 py-0.5 rounded-full font-semibold text-[10px] border ${
                                  topFinding?.is_detected
                                    ? "bg-rose-50 text-rose-700 border-rose-200"
                                    : "bg-emerald-50 text-emerald-700 border-emerald-200"
                                }`}
                              >
                                {topFinding?.is_detected ? topFinding.disease : "No Abnormality"}
                              </span>
                            </td>
                            <td className="py-3.5 px-4 font-mono font-bold text-slate-700">
                              {item.study.ctr?.ctr_percentage}%
                            </td>
                            <td className="py-3.5 px-4">
                              <span className="text-emerald-700 font-semibold">
                                {item.study.iqa.quality_tier}
                              </span>
                            </td>
                            <td className="py-3.5 px-4 text-right space-x-2">
                              <button
                                onClick={() => {
                                  setStudy(item.study);
                                  setActiveNav("analyze");
                                  setActiveResultsTab("overview");
                                }}
                                className="text-blue-600 hover:text-blue-700 font-bold hover:underline"
                              >
                                View
                              </button>
                              <button
                                onClick={() => {
                                  setStudy(item.study);
                                  setActiveNav("reports");
                                }}
                                className="text-slate-600 hover:text-slate-900 font-medium hover:underline"
                              >
                                Report
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Page 5: About VisionCare AI */}
        {activeNav === "about" && (
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
            <div className="space-y-1">
              <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                About VisionCare AI
              </h2>
              <p className="text-sm text-slate-500">
                Clinical Decision Support Architecture, Model Verification, and Regulatory Compliance.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="card-surface p-6 rounded-3xl shadow-sm space-y-3">
                <div className="w-10 h-10 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
                  <Activity className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-slate-900">DenseNet-121 Architecture</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Trained on the NIH ChestX-ray14 benchmark dataset spanning 112,120 frontal chest radiographs. Employs 14 independent sigmoid heads with temperature calibration (Platt scaling) for accurate clinical risk estimation.
                </p>
              </div>

              <div className="card-surface p-6 rounded-3xl shadow-sm space-y-3">
                <div className="w-10 h-10 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center font-bold">
                  <Eye className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-slate-900">Grad-CAM++ Explainability</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Second-order pixel-level gradient attribution highlights visual focal regions. Evaluates positive gradients across 5 anatomical zones (RUZ, RMZ, RLZ, LUZ, LLZ) to provide transparent visual evidence.
                </p>
              </div>

              <div className="card-surface p-6 rounded-3xl shadow-sm space-y-3">
                <div className="w-10 h-10 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
                  <Gauge className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-slate-900">Image Quality Assessment</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Pre-inference QA filters blur, underexposure, and non-radiographic artifacts using Laplacian variance, Michelson contrast, and dynamic range histogram evaluation.
                </p>
              </div>

              <div className="card-surface p-6 rounded-3xl shadow-sm space-y-3">
                <div className="w-10 h-10 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center font-bold">
                  <Heart className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-slate-900">CTR Biometrics & ED Triage</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Automated Cardiothoracic Ratio calculation segments maximal transverse cardiac width over thoracic width with caliper overlays, classifying cardiomegaly when CTR exceeds 50%.
                </p>
              </div>
            </div>

            <div className="card-surface p-6 rounded-3xl border border-blue-200 bg-blue-50/50 space-y-3 text-xs text-slate-700 leading-relaxed">
              <h4 className="font-bold text-slate-900 flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-blue-600" />
                Clinical Decision Support (CDS) Notice
              </h4>
              <p>
                VisionCare AI is developed as an assistive, educational, and research clinical decision-support tool. It does not replace a certified radiologist or qualified medical practitioner. All automated insights, bounding boxes, and probability estimates must be reviewed in conjunction with complete clinical history.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* 5. Minimal Clinical Footer */}
      <footer className="bg-white border-t border-slate-200 py-6 mt-12 text-center text-xs text-slate-400">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>VisionCare AI • NIH ChestX-ray14 Clinical Decision Support</span>
          <span>Designed for Research & Clinical Education</span>
        </div>
      </footer>

      {/* 6. Floating AI Copilot Trigger & Drawer */}
      {study && (
        <>
          {!isFloatingChatOpen && (
            <button
              onClick={() => setIsFloatingChatOpen(true)}
              className="fixed bottom-6 right-6 z-40 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-4 py-3 rounded-full shadow-lg shadow-blue-500/20 flex items-center space-x-2 transition hover:scale-105 active:scale-95 cursor-pointer border border-white/20 animate-fade-in"
            >
              <MessageSquare className="w-4 h-4" />
              <span>Radiology Copilot</span>
            </button>
          )}

          {isFloatingChatOpen && (
            <ClinicalChatbot
              study={study}
              isFloating={true}
              onClose={() => setIsFloatingChatOpen(false)}
            />
          )}
        </>
      )}
    </div>
  );
}
