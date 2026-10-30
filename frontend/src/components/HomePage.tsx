"use client";

import React, { useState } from "react";
import {
  ArrowRight,
  Gauge,
  Activity,
  BarChart2,
  Eye,
  FileText,
  FileDown,
  ShieldCheck,
  Lock,
  Stethoscope,
  Zap,
  CheckCircle2,
  ChevronRight,
  Layers
} from "lucide-react";

interface HomePageProps {
  onGetStarted: () => void;
}

export const HomePage: React.FC<HomePageProps> = ({ onGetStarted }) => {
  const [selectedCondition, setSelectedCondition] = useState<
    "normal" | "pneumonia" | "effusion" | "cardiomegaly" | "pneumothorax"
  >("pneumonia");

  const conditionDetails: Record<
    "normal" | "pneumonia" | "effusion" | "cardiomegaly" | "pneumothorax",
    {
      title: string;
      hallmark: string;
      keySigns: string[];
      prevalence: string;
    }
  > = {
    normal: {
      title: "Normal Chest Radiograph",
      hallmark: "Clear pulmonary parenchyma with preserved vascular markings and sharp costophrenic angles.",
      keySigns: ["Cardiothoracic ratio (CTR) < 50%", "Sharp bilateral diaphragmatic sulci", "No focal consolidation or effusion"],
      prevalence: "Baseline Screening",
    },
    pneumonia: {
      title: "Pneumonia / Consolidation",
      hallmark: "Focal or patchy air-space opacification with visible air bronchograms.",
      keySigns: ["Alveolar consolidation in dependent lung lobes", "Silhouette sign with adjacent cardiac/diaphragmatic border", "Positive Grad-CAM++ regional attribution"],
      prevalence: "Common Acute Finding",
    },
    effusion: {
      title: "Pleural Effusion",
      hallmark: "Fluid accumulation in the pleural cavity causing costophrenic angle blunting.",
      keySigns: ["Meniscus sign at lateral costophrenic sulcus", "Homogeneous basilar radiopacity", "Contralateral mediastinal shift in massive effusion"],
      prevalence: "Secondary Complication",
    },
    cardiomegaly: {
      title: "Cardiomegaly",
      hallmark: "Enlargement of the cardiac silhouette exceeding 50% of the maximum thoracic diameter.",
      keySigns: ["Transverse cardiac diameter > 15.5 cm", "Left ventricular prominence on PA projection", "Evaluated in conjunction with vascular pedicle width"],
      prevalence: "Chronic Cardiovascular",
    },
    pneumothorax: {
      title: "Pneumothorax",
      hallmark: "Air in the pleural space with distinct visceral pleural line separation.",
      keySigns: ["Thin radiopaque visceral pleural line", "Complete absence of peripheral pulmonary vascular markings", "Potential lung collapse toward the hilum"],
      prevalence: "Urgent Critical Finding",
    },
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 space-y-14 animate-fade-in">
      {/* 1. Hero Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
        {/* Left Content */}
        <div className="lg:col-span-7 space-y-6">
          <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-blue-50/90 backdrop-blur-sm border border-blue-200/80 text-blue-700 text-xs font-semibold shadow-xs hover:border-blue-300 transition">
            <span className="w-2 h-2 rounded-full bg-blue-600 animate-pulse"></span>
            <span>CLINICAL RADIOLOGY WORKSTATION</span>
          </div>

          <h1 className="text-4xl sm:text-5xl xl:text-6xl font-extrabold text-slate-900 tracking-tight leading-[1.12]">
            Chest Radiograph <br />
            <span className="bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
              Decision Support
            </span> <br />
            Platform
          </h1>

          <p className="text-lg sm:text-xl font-medium text-slate-700">
            Explainable. Transparent. Built for Clinicians.
          </p>

          <p className="text-slate-600 text-sm sm:text-base max-w-xl leading-relaxed">
            Upload a chest radiograph and get AI-assisted findings with visual
            attributions, epistemic uncertainty quantification, clinical reasoning, and automated reports.
          </p>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center gap-3.5 pt-1">
            <button
              onClick={onGetStarted}
              className="group inline-flex items-center space-x-2.5 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-semibold text-sm px-6 py-3.5 rounded-2xl shadow-lg shadow-blue-500/20 hover:shadow-blue-500/35 hover:-translate-y-0.5 transition-all duration-200 cursor-pointer"
            >
              <span>Launch Workstation</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </button>

            <button
              onClick={() => {
                document.getElementById("clinical-reference-guide")?.scrollIntoView({ behavior: "smooth" });
              }}
              className="inline-flex items-center space-x-2 bg-white hover:bg-slate-50 text-slate-700 font-semibold text-sm px-5 py-3.5 rounded-2xl border border-slate-200 shadow-xs hover:border-slate-300 hover:shadow-sm transition-all duration-200 cursor-pointer"
            >
              <Eye className="w-4 h-4 text-blue-600" />
              <span>Explore Reference Guide</span>
            </button>
          </div>

          {/* 4 Interactive Real-time Clinical Metric Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 border-t border-slate-200/80">
            <div className="card-surface card-surface-hover p-3 rounded-2xl group cursor-default">
              <div className="flex items-center justify-between text-slate-400 group-hover:text-blue-600 transition-colors">
                <span className="text-[10px] font-bold uppercase tracking-wider">Pathologies</span>
                <Activity className="w-3.5 h-3.5" />
              </div>
              <p className="text-lg font-extrabold text-slate-900 mt-1">14 Targets</p>
              <p className="text-[10px] text-slate-500">DenseNet-121 Multi-Label</p>
            </div>

            <div className="card-surface card-surface-hover p-3 rounded-2xl group cursor-default">
              <div className="flex items-center justify-between text-slate-400 group-hover:text-cyan-600 transition-colors">
                <span className="text-[10px] font-bold uppercase tracking-wider">Inference</span>
                <Zap className="w-3.5 h-3.5" />
              </div>
              <p className="text-lg font-extrabold text-slate-900 mt-1">&lt; 1.8s</p>
              <p className="text-[10px] text-slate-500">Real-Time Execution</p>
            </div>

            <div className="card-surface card-surface-hover p-3 rounded-2xl group cursor-default">
              <div className="flex items-center justify-between text-slate-400 group-hover:text-emerald-600 transition-colors">
                <span className="text-[10px] font-bold uppercase tracking-wider">Reliability</span>
                <ShieldCheck className="w-3.5 h-3.5" />
              </div>
              <p className="text-lg font-extrabold text-slate-900 mt-1">95% CI</p>
              <p className="text-[10px] text-slate-500">3-Pass TTA Uncertainty</p>
            </div>

            <div className="card-surface card-surface-hover p-3 rounded-2xl group cursor-default">
              <div className="flex items-center justify-between text-slate-400 group-hover:text-indigo-600 transition-colors">
                <span className="text-[10px] font-bold uppercase tracking-wider">Explainability</span>
                <Layers className="w-3.5 h-3.5" />
              </div>
              <p className="text-lg font-extrabold text-slate-900 mt-1">5 Levels</p>
              <p className="text-[10px] text-slate-500">Attribution to Causal</p>
            </div>
          </div>
        </div>

        {/* Right Hero Image Card (Atmospheric CXR with Moving Laser Scan & Floating Telemetry Badges) */}
        <div className="lg:col-span-5 flex justify-center">
          <div className="relative w-full max-w-md aspect-square rounded-3xl overflow-hidden card-surface shadow-2xl bg-gradient-to-tr from-blue-950 via-slate-900 to-blue-900 flex items-center justify-center p-3.5 border border-blue-200/60 animate-float-slow">
            {/* Glowing background blur effect */}
            <div className="absolute inset-0 bg-gradient-to-tr from-blue-500/20 via-cyan-400/10 to-transparent mix-blend-screen pointer-events-none"></div>

            {/* Real Chest X-ray visual with Laser Scanning Animation */}
            <div className="relative w-full h-full rounded-2xl overflow-hidden bg-black flex items-center justify-center group shadow-inner">
              {/* Medical Laser Scanning Line */}
              <div className="absolute left-0 right-0 h-1 bg-gradient-to-r from-transparent via-cyan-400 to-transparent shadow-[0_0_12px_#22d3ee] animate-scan-laser pointer-events-none z-20"></div>

              {/* Real Frontal Radiograph */}
              <img
                src="/hero-radiograph.jpg"
                alt="Clinical Frontal Chest Radiograph"
                className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
              />

              {/* Floating Live Telemetry Badge (Top-Left) */}
              <div className="absolute top-3 left-3 flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-slate-900/80 backdrop-blur-md border border-white/10 text-white text-[10px] font-medium shadow-lg z-10">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
                <span>Live Workstation</span>
              </div>

              {/* Floating Accuracy Metric Badge (Top-Right) */}
              <div className="absolute top-3 right-3 px-2.5 py-1 rounded-full bg-slate-900/80 backdrop-blur-md border border-white/10 text-cyan-300 text-[10px] font-mono font-semibold shadow-lg z-10">
                AUROC: 0.923
              </div>

              {/* Bottom Telemetry Overlay Bar */}
              <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between p-2.5 rounded-xl bg-slate-900/90 backdrop-blur-md border border-white/15 text-white shadow-xl z-10 transition-all duration-300 group-hover:bg-slate-900/95">
                <div className="flex items-center space-x-2">
                  <Activity className="w-4 h-4 text-blue-400 shrink-0" />
                  <div className="text-left">
                    <p className="text-[11px] font-semibold text-slate-100 leading-tight">DenseNet-121 Multi-Label</p>
                    <p className="text-[9px] text-slate-400">14 Thoracic Pathologies + TTA</p>
                  </div>
                </div>
                <span className="text-[10px] text-emerald-400 font-mono font-bold bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-500/30">
                  IQA: OPTIMAL
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Six Interactive Moving Feature Cards Row */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Workstation Capabilities
          </h2>
          <span className="text-xs text-blue-600 font-medium hover:underline cursor-pointer" onClick={onGetStarted}>
            Launch Workstation &rarr;
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
          <div
            onClick={onGetStarted}
            className="card-surface card-surface-hover p-4 rounded-2xl text-center space-y-2 flex flex-col items-center justify-center cursor-pointer group"
          >
            <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center group-hover:bg-blue-600 group-hover:text-white transition-all duration-300 shadow-xs">
              <Gauge className="w-5 h-5 group-hover:scale-110 transition-transform" />
            </div>
            <div>
              <span className="text-xs font-bold text-slate-800 block">Quality Check</span>
              <span className="text-[10px] text-slate-500">DICOM & Exposure</span>
            </div>
          </div>

          <div
            onClick={onGetStarted}
            className="card-surface card-surface-hover p-4 rounded-2xl text-center space-y-2 flex flex-col items-center justify-center cursor-pointer group"
          >
            <div className="w-10 h-10 rounded-xl bg-cyan-50 text-cyan-600 flex items-center justify-center group-hover:bg-cyan-600 group-hover:text-white transition-all duration-300 shadow-xs">
              <Activity className="w-5 h-5 group-hover:scale-110 transition-transform" />
            </div>
            <div>
              <span className="text-xs font-bold text-slate-800 block">Lung Isolation</span>
              <span className="text-[10px] text-slate-500">Anatomical ROI</span>
            </div>
          </div>

          <div
            onClick={onGetStarted}
            className="card-surface card-surface-hover p-4 rounded-2xl text-center space-y-2 flex flex-col items-center justify-center cursor-pointer group"
          >
            <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center group-hover:bg-indigo-600 group-hover:text-white transition-all duration-300 shadow-xs">
              <BarChart2 className="w-5 h-5 group-hover:scale-110 transition-transform" />
            </div>
            <div>
              <span className="text-xs font-bold text-slate-800 block">14 Diseases</span>
              <span className="text-[10px] text-slate-500">DenseNet-121</span>
            </div>
          </div>

          <div
            onClick={onGetStarted}
            className="card-surface card-surface-hover p-4 rounded-2xl text-center space-y-2 flex flex-col items-center justify-center cursor-pointer group"
          >
            <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center group-hover:bg-amber-600 group-hover:text-white transition-all duration-300 shadow-xs">
              <Eye className="w-5 h-5 group-hover:scale-110 transition-transform" />
            </div>
            <div>
              <span className="text-xs font-bold text-slate-800 block">Explainability</span>
              <span className="text-[10px] text-slate-500">Grad-CAM++ & Zones</span>
            </div>
          </div>

          <div
            onClick={onGetStarted}
            className="card-surface card-surface-hover p-4 rounded-2xl text-center space-y-2 flex flex-col items-center justify-center cursor-pointer group"
          >
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center group-hover:bg-emerald-600 group-hover:text-white transition-all duration-300 shadow-xs">
              <FileText className="w-5 h-5 group-hover:scale-110 transition-transform" />
            </div>
            <div>
              <span className="text-xs font-bold text-slate-800 block">Clinical Report</span>
              <span className="text-[10px] text-slate-500">Structured Findings</span>
            </div>
          </div>

          <div
            onClick={onGetStarted}
            className="card-surface card-surface-hover p-4 rounded-2xl text-center space-y-2 flex flex-col items-center justify-center cursor-pointer group"
          >
            <div className="w-10 h-10 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center group-hover:bg-rose-600 group-hover:text-white transition-all duration-300 shadow-xs">
              <FileDown className="w-5 h-5 group-hover:scale-110 transition-transform" />
            </div>
            <div>
              <span className="text-xs font-bold text-slate-800 block">PDF Export</span>
              <span className="text-[10px] text-slate-500">Archival Ready</span>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Clinical Examples & Interactive Reference Guide (Moving Condition Cards) */}
      <div id="clinical-reference-guide" className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200/90 shadow-sm space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-semibold border border-blue-200/80">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-600"></span>
              <span>CLINICAL REFERENCE GUIDE</span>
            </div>
            <h3 className="text-2xl font-bold text-slate-900 tracking-tight">
              Visual Reference Guide for Thoracic Pathologies
            </h3>
            <p className="text-sm text-slate-600 max-w-2xl leading-relaxed">
              Standardized radiological presentation for primary conditions evaluated by VisionCare AI:{" "}
              <strong className="text-slate-800">Normal, Pneumonia, Pleural Effusion, Cardiomegaly,</strong> and{" "}
              <strong className="text-slate-800">Pneumothorax</strong>.
            </p>
          </div>

          <button
            onClick={onGetStarted}
            className="inline-flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-5 py-2.5 rounded-xl transition-all shadow-sm hover:shadow-md shrink-0 cursor-pointer"
          >
            <span>Analyze a Radiograph</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Interactive Condition Switcher Tabs */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5">
          {(
            [
              { key: "normal", label: "Normal" },
              { key: "pneumonia", label: "Pneumonia" },
              { key: "effusion", label: "Pleural Effusion" },
              { key: "cardiomegaly", label: "Cardiomegaly" },
              { key: "pneumothorax", label: "Pneumothorax" },
            ] as const
          ).map((item) => {
            const isSelected = selectedCondition === item.key;
            return (
              <button
                key={item.key}
                onClick={() => setSelectedCondition(item.key)}
                className={`p-3 rounded-2xl text-left border transition-all duration-200 cursor-pointer ${
                  isSelected
                    ? "bg-blue-50/80 border-blue-500 shadow-sm shadow-blue-500/10 text-blue-900 ring-2 ring-blue-500/20"
                    : "bg-slate-50/70 border-slate-200 hover:border-slate-300 text-slate-700 hover:bg-slate-100"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold">{item.label}</span>
                  {isSelected && <CheckCircle2 className="w-3.5 h-3.5 text-blue-600" />}
                </div>
                <span className="text-[10px] text-slate-500 block mt-0.5 truncate">
                  {conditionDetails[item.key].prevalence}
                </span>
              </button>
            );
          })}
        </div>

        {/* Selected Condition Clinical Hallmark Card */}
        <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 flex flex-col md:flex-row md:items-center justify-between gap-4 animate-fade-in">
          <div className="space-y-1.5 max-w-2xl">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-bold text-slate-900">
                {conditionDetails[selectedCondition].title}
              </span>
              <span className="text-[10px] text-blue-700 bg-blue-100/70 px-2 py-0.5 rounded-full font-semibold">
                Radiological Criteria
              </span>
            </div>
            <p className="text-xs text-slate-600">
              {conditionDetails[selectedCondition].hallmark}
            </p>
            <div className="flex flex-wrap gap-2 pt-1">
              {conditionDetails[selectedCondition].keySigns.map((sign, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center text-[10px] bg-white border border-slate-200 px-2.5 py-0.5 rounded-lg text-slate-600"
                >
                  • {sign}
                </span>
              ))}
            </div>
          </div>

          <button
            onClick={onGetStarted}
            className="inline-flex items-center space-x-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-4 py-2 rounded-xl transition shadow-xs shrink-0 self-start md:self-auto cursor-pointer"
          >
            <span>Analyze {conditionDetails[selectedCondition].title.split(" ")[0]}</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Crisp, High-Contrast Image Container with Hover Elevation */}
        <div className="group rounded-2xl border border-slate-200 overflow-hidden bg-slate-50 p-2 sm:p-3 shadow-inner hover:shadow-lg hover:border-blue-300 transition-all duration-300">
          <img
            src="/pathology-examples.png"
            alt="Thoracic Pathologies Clinical Example Guide: Normal, Pneumonia, Effusion, Cardiomegaly, Pneumothorax"
            className="w-full h-auto rounded-xl object-contain bg-white transition-transform duration-500 group-hover:scale-[1.008]"
          />
        </div>
      </div>

      {/* 4. Bottom Trust Cards Row */}
      <div className="pt-2 grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card-surface card-surface-hover p-4 rounded-2xl flex items-center space-x-3 cursor-default">
          <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div>
            <span className="text-xs font-bold text-slate-800 block">Research & Education</span>
            <span className="text-[10px] text-slate-500">NIH CXR14 Validated</span>
          </div>
        </div>

        <div className="card-surface card-surface-hover p-4 rounded-2xl flex items-center space-x-3 cursor-default">
          <div className="w-9 h-9 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0">
            <Lock className="w-4 h-4" />
          </div>
          <div>
            <span className="text-xs font-bold text-slate-800 block">Privacy Focused</span>
            <span className="text-[10px] text-slate-500">De-identified Data</span>
          </div>
        </div>

        <div className="card-surface card-surface-hover p-4 rounded-2xl flex items-center space-x-3 cursor-default">
          <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
            <Eye className="w-4 h-4" />
          </div>
          <div>
            <span className="text-xs font-bold text-slate-800 block">Visual Attribution</span>
            <span className="text-[10px] text-slate-500">Grad-CAM++ & Zones</span>
          </div>
        </div>

        <div className="card-surface card-surface-hover p-4 rounded-2xl flex items-center space-x-3 cursor-default">
          <div className="w-9 h-9 rounded-xl bg-cyan-50 text-cyan-600 flex items-center justify-center shrink-0">
            <Stethoscope className="w-4 h-4" />
          </div>
          <div>
            <span className="text-xs font-bold text-slate-800 block">Clinician-Oriented</span>
            <span className="text-[10px] text-slate-500">SaMD Audit Trace</span>
          </div>
        </div>
      </div>
    </div>
  );
};