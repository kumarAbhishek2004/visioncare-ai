"use client";

import React from "react";
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
  Stethoscope
} from "lucide-react";

interface HomePageProps {
  onGetStarted: () => void;
}

export const HomePage: React.FC<HomePageProps> = ({ onGetStarted }) => {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 space-y-12 animate-fade-in">
      {/* 1. Hero Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        {/* Left Content */}
        <div className="lg:col-span-7 space-y-6">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-xs font-semibold">
            <span className="w-2 h-2 rounded-full bg-blue-600"></span>
            <span>CLINICAL RADIOLOGY WORKSTATION</span>
          </div>

          <h1 className="text-4xl sm:text-5xl xl:text-6xl font-extrabold text-slate-900 tracking-tight leading-tight">
            Chest Radiograph <br />
            <span className="text-blue-600">Decision Support</span> <br />
            Platform
          </h1>

          <p className="text-lg sm:text-xl font-medium text-slate-700">
            Explainable. Transparent. Built for Clinicians.
          </p>

          <p className="text-slate-600 text-sm sm:text-base max-w-xl leading-relaxed">
            Upload a chest radiograph and get AI-assisted findings with clear visual
            explanations, clinical insights, and a structured report.
          </p>

          <div className="pt-2">
            <button
              onClick={onGetStarted}
              className="inline-flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm px-6 py-3 rounded-xl shadow-md shadow-blue-500/20 transition-all duration-200 hover:-translate-y-0.5"
            >
              <span>Launch Workstation</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Right Hero Image Card (Atmospheric CXR with real Frontal Radiograph) */}
        <div className="lg:col-span-5 flex justify-center">
          <div className="relative w-full max-w-md aspect-square rounded-3xl overflow-hidden card-surface shadow-2xl bg-gradient-to-tr from-blue-950 via-slate-900 to-blue-900 flex items-center justify-center p-3 border border-blue-200/50">
            {/* Glowing background blur effect */}
            <div className="absolute inset-0 bg-gradient-to-tr from-blue-500/20 via-cyan-400/10 to-transparent mix-blend-screen pointer-events-none"></div>

            {/* Real Chest X-ray visual */}
            <div className="relative w-full h-full rounded-2xl overflow-hidden bg-black flex items-center justify-center group">
              <img
                src="/hero-radiograph.jpg"
                alt="Clinical Frontal Chest Radiograph"
                className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
              />

              <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between p-2.5 rounded-xl bg-slate-900/85 backdrop-blur-md border border-white/10 text-white shadow-xl">
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

      {/* 2. Six Feature Cards Row */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
        <div className="card-surface card-surface-hover p-4 rounded-2xl text-center space-y-2 flex flex-col items-center justify-center">
          <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
            <Gauge className="w-5 h-5" />
          </div>
          <span className="text-xs font-bold text-slate-800">Image Quality Check</span>
        </div>

        <div className="card-surface card-surface-hover p-4 rounded-2xl text-center space-y-2 flex flex-col items-center justify-center">
          <div className="w-10 h-10 rounded-xl bg-cyan-50 text-cyan-600 flex items-center justify-center">
            <Activity className="w-5 h-5" />
          </div>
          <span className="text-xs font-bold text-slate-800">Lung Segmentation</span>
        </div>

        <div className="card-surface card-surface-hover p-4 rounded-2xl text-center space-y-2 flex flex-col items-center justify-center">
          <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
            <BarChart2 className="w-5 h-5" />
          </div>
          <span className="text-xs font-bold text-slate-800">Disease Detection</span>
        </div>

        <div className="card-surface card-surface-hover p-4 rounded-2xl text-center space-y-2 flex flex-col items-center justify-center">
          <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
            <Eye className="w-5 h-5" />
          </div>
          <span className="text-xs font-bold text-slate-800">Visual Explainability</span>
        </div>

        <div className="card-surface card-surface-hover p-4 rounded-2xl text-center space-y-2 flex flex-col items-center justify-center">
          <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <FileText className="w-5 h-5" />
          </div>
          <span className="text-xs font-bold text-slate-800">Clinical Report</span>
        </div>

        <div className="card-surface card-surface-hover p-4 rounded-2xl text-center space-y-2 flex flex-col items-center justify-center">
          <div className="w-10 h-10 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center">
            <FileDown className="w-5 h-5" />
          </div>
          <span className="text-xs font-bold text-slate-800">PDF Export</span>
        </div>
      </div>

      {/* 2.5 Clinical Examples & Reference Guide */}
      <div className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-sm space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-semibold border border-blue-200">
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
            className="inline-flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-5 py-2.5 rounded-xl transition-all shadow-sm hover:shadow-md shrink-0"
          >
            <span>Analyze a Radiograph</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Crisp, High-Contrast Image Container with Hover Elevation */}
        <div className="group rounded-2xl border border-slate-200 overflow-hidden bg-slate-50 p-2 sm:p-3 shadow-inner hover:shadow-md transition-all duration-300">
          <img
            src="/pathology-examples.png"
            alt="Thoracic Pathologies Clinical Example Guide: Normal, Pneumonia, Effusion, Cardiomegaly, Pneumothorax"
            className="w-full h-auto rounded-xl object-contain bg-white transition-transform duration-500 group-hover:scale-[1.008]"
          />
        </div>
      </div>

      {/* 3. Bottom Trust Bar */}
      <div className="pt-6 border-t border-slate-200 grid grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-medium text-slate-600">
        <div className="flex items-center space-x-2">
          <ShieldCheck className="w-4 h-4 text-blue-600" />
          <span>Built for Research & Education</span>
        </div>
        <div className="flex items-center space-x-2">
          <Lock className="w-4 h-4 text-emerald-600" />
          <span>Privacy Focused (De-identified data)</span>
        </div>
        <div className="flex items-center space-x-2">
          <Eye className="w-4 h-4 text-blue-600" />
          <span>Transparent Visual Evidence</span>
        </div>
        <div className="flex items-center space-x-2">
          <Stethoscope className="w-4 h-4 text-cyan-600" />
          <span>Clinician-Oriented Design</span>
        </div>
      </div>
    </div>
  );
};
