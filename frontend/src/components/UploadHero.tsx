"use client";

import React, { useState } from "react";
import {
  UploadCloud,
  FileText,
  Sparkles,
  ShieldCheck,
  Zap,
  CheckCircle,
  AlertCircle
} from "lucide-react";

interface UploadHeroProps {
  onUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onSelectSample: (type: "normal" | "cardiomegaly" | "effusion" | "consolidation") => void;
  isLoading: boolean;
}

export const UploadHero: React.FC<UploadHeroProps> = ({
  onUpload,
  onSelectSample,
  isLoading,
}) => {
  const [isDragging, setIsDragging] = useState(false);

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 flex flex-col items-center text-center space-y-8 animate-fade-in">
      {/* Badge & Title */}
      <div className="space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400 text-xs font-semibold">
          <Zap className="w-3.5 h-3.5" />
          <span>Next-Generation Chest Radiograph Analysis</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight leading-tight">
          Instant, Explainable AI for <br className="hidden sm:inline" />
          <span className="bg-gradient-to-r from-blue-400 via-cyan-300 to-emerald-400 bg-clip-text text-transparent">
            Chest X-Ray Insights
          </span>
        </h1>
        <p className="text-slate-400 text-sm sm:text-base max-w-xl mx-auto leading-relaxed">
          Upload any frontal chest radiograph (DICOM, PNG, or JPEG) to receive automated 
          cardiothoracic ratio biometrics, 14-disease detection, and visual AI heatmaps in seconds.
        </p>
      </div>

      {/* Main Drag & Drop Zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            const file = e.dataTransfer.files[0];
            const event = {
              target: { files: [file] },
            } as unknown as React.ChangeEvent<HTMLInputElement>;
            onUpload(event);
          }
        }}
        className={`w-full max-w-2xl p-8 sm:p-12 rounded-3xl border-2 border-dashed transition-all duration-200 cursor-pointer flex flex-col items-center justify-center space-y-4 shadow-2xl ${
          isDragging
            ? "border-blue-400 bg-blue-950/30 scale-[1.01]"
            : "border-radDark-700 bg-radDark-900/80 hover:border-blue-500/60 hover:bg-radDark-850"
        }`}
      >
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-blue-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
          <UploadCloud className="w-8 h-8 text-white" />
        </div>

        <div className="space-y-1">
          <p className="text-base font-bold text-white">
            Drag & drop your chest radiograph here
          </p>
          <p className="text-xs text-slate-400">
            Supports native DICOM (<span className="text-cyan-400 font-mono">.dcm</span>), PNG, and JPEG formats
          </p>
        </div>

        <label className="cursor-pointer inline-flex items-center space-x-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-5 py-2.5 rounded-xl shadow-md transition">
          <FileText className="w-4 h-4" />
          <span>Browse Files from Computer</span>
          <input
            type="file"
            accept="image/*,.dcm"
            className="hidden"
            onChange={onUpload}
            disabled={isLoading}
          />
        </label>
      </div>

      {/* Quick Try Samples Bar */}
      <div className="w-full max-w-2xl space-y-3">
        <div className="flex items-center justify-between text-xs text-slate-400 px-2">
          <span className="flex items-center gap-1.5 font-medium">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            No X-ray image handy? Try a preloaded clinical sample:
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
          <button
            onClick={() => onSelectSample("normal")}
            disabled={isLoading}
            className="p-3 rounded-xl bg-radDark-900 border border-radDark-700 hover:border-emerald-500/60 text-left transition group"
          >
            <div className="text-[10px] font-mono text-emerald-400 font-semibold uppercase">
              Normal
            </div>
            <div className="text-xs font-bold text-slate-200 mt-0.5 group-hover:text-emerald-300">
              Clear Lungs
            </div>
          </button>

          <button
            onClick={() => onSelectSample("cardiomegaly")}
            disabled={isLoading}
            className="p-3 rounded-xl bg-radDark-900 border border-radDark-700 hover:border-rose-500/60 text-left transition group"
          >
            <div className="text-[10px] font-mono text-rose-400 font-semibold uppercase">
              Cardiology
            </div>
            <div className="text-xs font-bold text-slate-200 mt-0.5 group-hover:text-rose-300">
              Cardiomegaly
            </div>
          </button>

          <button
            onClick={() => onSelectSample("effusion")}
            disabled={isLoading}
            className="p-3 rounded-xl bg-radDark-900 border border-radDark-700 hover:border-amber-500/60 text-left transition group"
          >
            <div className="text-[10px] font-mono text-amber-400 font-semibold uppercase">
              Pleural
            </div>
            <div className="text-xs font-bold text-slate-200 mt-0.5 group-hover:text-amber-300">
              Effusion
            </div>
          </button>

          <button
            onClick={() => onSelectSample("consolidation")}
            disabled={isLoading}
            className="p-3 rounded-xl bg-radDark-900 border border-radDark-700 hover:border-cyan-500/60 text-left transition group"
          >
            <div className="text-[10px] font-mono text-cyan-400 font-semibold uppercase">
              Infection
            </div>
            <div className="text-xs font-bold text-slate-200 mt-0.5 group-hover:text-cyan-300">
              Consolidation
            </div>
          </button>
        </div>
      </div>

      {/* Feature Highlights Footer */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 w-full max-w-2xl pt-4 border-t border-radDark-700 text-xs text-slate-400">
        <div className="flex items-center justify-center space-x-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>FDA SaMD Class II Auditable</span>
        </div>
        <div className="flex items-center justify-center space-x-2">
          <CheckCircle className="w-4 h-4 text-cyan-400 shrink-0" />
          <span>Full In-Memory Privacy</span>
        </div>
        <div className="flex items-center justify-center space-x-2">
          <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
          <span>Assistive Decision Support</span>
        </div>
      </div>
    </div>
  );
};
