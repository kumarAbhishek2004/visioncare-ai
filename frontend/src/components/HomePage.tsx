"use client";

import React from "react";
import {
  ArrowRight,
  Play,
  Gauge,
  Activity,
  BarChart2,
  Eye,
  FileText,
  FileDown,
  ShieldCheck,
  Lock,
  Sparkles,
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
            <span className="w-2 h-2 rounded-full bg-blue-600 animate-pulse"></span>
            <span>AI-ASSISTED RADIOLOGY</span>
          </div>

          <h1 className="text-4xl sm:text-5xl xl:text-6xl font-extrabold text-slate-900 tracking-tight leading-tight">
            AI-Powered <br />
            <span className="text-blue-600">Chest X-ray</span> <br />
            Analysis
          </h1>

          <p className="text-lg sm:text-xl font-medium text-slate-700">
            Explainable. Transparent. Built for Clinicians.
          </p>

          <p className="text-slate-600 text-sm sm:text-base max-w-xl leading-relaxed">
            Upload a chest radiograph and get AI-assisted findings with clear visual
            explanations, clinical insights, and a structured report.
          </p>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <button
              onClick={onGetStarted}
              className="inline-flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm px-6 py-3 rounded-xl shadow-md shadow-blue-500/20 transition"
            >
              <span>Get Started</span>
              <ArrowRight className="w-4 h-4" />
            </button>

            <button
              onClick={onGetStarted}
              className="inline-flex items-center space-x-2 bg-white hover:bg-slate-50 text-slate-700 font-semibold text-sm px-5 py-3 rounded-xl border border-slate-200 shadow-sm transition"
            >
              <Play className="w-4 h-4 text-blue-600 fill-blue-600" />
              <span>Watch Demo</span>
            </button>
          </div>
        </div>

        {/* Right Hero Image Card (Atmospheric CXR glow) */}
        <div className="lg:col-span-5 flex justify-center">
          <div className="relative w-full max-w-md aspect-square rounded-3xl overflow-hidden card-surface shadow-2xl bg-gradient-to-tr from-blue-950 via-slate-900 to-blue-900 flex items-center justify-center p-3 border border-blue-200/50">
            {/* Glowing background blur effect */}
            <div className="absolute inset-0 bg-gradient-to-tr from-blue-500/20 via-cyan-400/10 to-transparent mix-blend-screen pointer-events-none"></div>

            {/* Simulated X-ray visual */}
            <div className="relative w-full h-full rounded-2xl overflow-hidden bg-black flex items-center justify-center">
              <img
                src="/api/placeholder/400/400"
                alt="Radiograph Illustration"
                onError={(e) => {
                  // Fallback SVG if placeholder is not available
                  e.currentTarget.style.display = "none";
                }}
                className="w-full h-full object-cover"
              />
              {/* Fallback stylized anatomical illustration */}
              <div className="absolute inset-0 flex flex-col items-center justify-center text-center p-6 text-slate-400 bg-radial from-slate-800 to-black">
                <Activity className="w-16 h-16 text-blue-400 mb-3 animate-pulse" />
                <span className="text-sm font-semibold text-white">Interactive Frontal Radiograph</span>
                <span className="text-xs text-blue-300 mt-1">Multi-Label DenseNet-121 Feature Attribution</span>
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
          <Sparkles className="w-4 h-4 text-amber-600" />
          <span>Explainable AI with Visual Evidence</span>
        </div>
        <div className="flex items-center space-x-2">
          <Stethoscope className="w-4 h-4 text-cyan-600" />
          <span>Clinician-Oriented Design</span>
        </div>
      </div>
    </div>
  );
};
