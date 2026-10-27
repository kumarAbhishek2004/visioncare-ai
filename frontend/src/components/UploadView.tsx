"use client";

import React, { useState } from "react";
import {
  UploadCloud,
  CheckCircle2,
  FileText,
  Sparkles,
  ArrowRight,
  Info
} from "lucide-react";

interface UploadViewProps {
  onUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onSelectSample: (type: "normal" | "pneumonia" | "effusion" | "cardiomegaly" | "pneumothorax") => void;
  isLoading: boolean;
}

export const UploadView: React.FC<UploadViewProps> = ({
  onUpload,
  onSelectSample,
  isLoading,
}) => {
  const [isDragging, setIsDragging] = useState(false);

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      {/* 1. Step Progress Bar (1. Upload -> 2. Validate -> 3. Analyze -> 4. Results) */}
      <div className="flex items-center justify-center max-w-2xl mx-auto">
        <div className="flex items-center w-full justify-between relative">
          {/* Step 1 */}
          <div className="flex flex-col items-center z-10">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shadow-sm transition ${
              isLoading ? "bg-emerald-600 text-white" : "bg-blue-600 text-white shadow-blue-500/30"
            }`}>
              {isLoading ? <CheckCircle2 className="w-4 h-4 text-white" /> : "1"}
            </div>
            <span className={`text-xs mt-1.5 font-semibold ${isLoading ? "text-emerald-600" : "text-blue-600"}`}>Upload</span>
          </div>
          <div className={`flex-1 h-0.5 -mt-5 mx-2 transition-colors ${isLoading ? "bg-blue-500" : "bg-slate-200"}`}></div>

          {/* Step 2 */}
          <div className="flex flex-col items-center z-10">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition ${
              isLoading
                ? "bg-blue-600 text-white shadow-sm shadow-blue-500/30 animate-pulse"
                : "bg-slate-100 border border-slate-300 text-slate-500"
            }`}>
              2
            </div>
            <span className={`text-xs mt-1.5 font-medium ${isLoading ? "text-blue-600 font-semibold" : "text-slate-500"}`}>Validate</span>
          </div>
          <div className={`flex-1 h-0.5 -mt-5 mx-2 transition-colors ${isLoading ? "bg-blue-300" : "bg-slate-200"}`}></div>

          {/* Step 3 */}
          <div className="flex flex-col items-center z-10">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition ${
              isLoading
                ? "bg-blue-100 border-2 border-blue-600 text-blue-700 animate-pulse"
                : "bg-slate-100 border border-slate-300 text-slate-500"
            }`}>
              3
            </div>
            <span className={`text-xs mt-1.5 font-medium ${isLoading ? "text-blue-600 font-semibold" : "text-slate-500"}`}>Analyze</span>
          </div>
          <div className="flex-1 h-0.5 bg-slate-200 -mt-5 mx-2"></div>

          {/* Step 4 */}
          <div className="flex flex-col items-center z-10">
            <div className="w-8 h-8 rounded-full bg-slate-100 border border-slate-300 text-slate-500 flex items-center justify-center text-xs font-bold">
              4
            </div>
            <span className="text-xs font-medium text-slate-500 mt-1.5">Results</span>
          </div>
        </div>
      </div>

      {/* 2. Page Header */}
      <div className="space-y-1">
        <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          Upload Chest X-ray
        </h2>
        <p className="text-sm text-slate-500">
          Upload a frontal chest radiograph to get AI-assisted analysis.
        </p>
      </div>

      {/* 3. Main Upload Area & Tips Card */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left: Drag & Drop Card (lg:col-span-8) */}
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
          className={`lg:col-span-8 p-8 sm:p-12 rounded-3xl border-2 border-dashed transition-all duration-200 flex flex-col items-center justify-center text-center space-y-4 ${
            isDragging
              ? "border-blue-500 bg-blue-50/50"
              : "border-slate-300 bg-white hover:border-blue-400 hover:bg-slate-50/50 shadow-sm"
          }`}
        >
          <div className="w-16 h-16 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center shadow-inner">
            <UploadCloud className="w-8 h-8" />
          </div>

          <div className="space-y-1">
            <p className="text-base font-bold text-slate-800">
              Drag & drop your image here
            </p>
            <p className="text-xs text-slate-400">or</p>
          </div>

          <label className="cursor-pointer inline-flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs px-5 py-2.5 rounded-xl shadow-sm transition">
            <FileText className="w-4 h-4" />
            <span>Browse Files</span>
            <input
              type="file"
              accept="image/*,.dcm"
              className="hidden"
              onChange={onUpload}
              disabled={isLoading}
            />
          </label>

          <p className="text-[11px] text-slate-400 pt-2 border-t border-slate-100 max-w-md">
            Supported formats: <strong className="text-slate-600">PNG, JPEG, DICOM</strong> • Max size: <strong className="text-slate-600">20 MB</strong> • Best results with frontal chest X-ray
          </p>
        </div>

        {/* Right: Tips for Best Results Card (lg:col-span-4) */}
        <div className="lg:col-span-4 card-surface p-6 rounded-3xl space-y-4 shadow-sm bg-gradient-to-b from-blue-50/50 to-white">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-1.5">
            <Info className="w-4 h-4 text-blue-600" />
            Tips for best results
          </h3>

          <ul className="space-y-3.5 text-xs text-slate-600">
            <li className="flex items-start space-x-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
              <span>Use a clear frontal (PA/AP) chest X-ray</span>
            </li>
            <li className="flex items-start space-x-2.5">
              <CheckCircle2 className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
              <span>Ensure the entire thorax is visible</span>
            </li>
            <li className="flex items-start space-x-2.5">
              <CheckCircle2 className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
              <span>Avoid cropped or rotated images</span>
            </li>
            <li className="flex items-start space-x-2.5">
              <CheckCircle2 className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
              <span>Best quality images give more reliable results</span>
            </li>
          </ul>
        </div>
      </div>

      {/* 4. Example Images Section */}
      <div className="space-y-3.5 pt-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-blue-600" />
            Example Images
          </h3>
          <span className="text-xs text-blue-600 font-semibold cursor-pointer hover:underline flex items-center gap-1">
            View more examples <ArrowRight className="w-3.5 h-3.5" />
          </span>
        </div>

        {/* 5 Clickable Example Thumbnails */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3.5">
          <button
            onClick={() => onSelectSample("normal")}
            disabled={isLoading}
            className="card-surface card-surface-hover rounded-2xl p-2.5 text-center space-y-2 group flex flex-col items-center cursor-pointer transition hover:border-blue-500 hover:shadow-md"
          >
            <div className="w-full aspect-square rounded-xl bg-slate-950 overflow-hidden flex items-center justify-center border border-slate-200">
              <img
                src="/samples/sample_1_normal_chest.png"
                alt="Normal Chest"
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                onError={(e) => {
                  e.currentTarget.style.display = "none";
                }}
              />
            </div>
            <div className="space-y-0.5">
              <span className="text-xs font-bold text-slate-800 group-hover:text-blue-600 block">
                Normal
              </span>
              <span className="text-[10px] text-slate-400 block">Clear Lung Fields</span>
            </div>
          </button>

          <button
            onClick={() => onSelectSample("pneumonia")}
            disabled={isLoading}
            className="card-surface card-surface-hover rounded-2xl p-2.5 text-center space-y-2 group flex flex-col items-center cursor-pointer transition hover:border-blue-500 hover:shadow-md"
          >
            <div className="w-full aspect-square rounded-xl bg-slate-950 overflow-hidden flex items-center justify-center border border-slate-200">
              <img
                src="/samples/sample_4_pneumonia_consolidation.png"
                alt="Pneumonia"
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                onError={(e) => {
                  e.currentTarget.style.display = "none";
                }}
              />
            </div>
            <div className="space-y-0.5">
              <span className="text-xs font-bold text-slate-800 group-hover:text-blue-600 block">
                Pneumonia
              </span>
              <span className="text-[10px] text-slate-400 block">Focal Infiltrates</span>
            </div>
          </button>

          <button
            onClick={() => onSelectSample("effusion")}
            disabled={isLoading}
            className="card-surface card-surface-hover rounded-2xl p-2.5 text-center space-y-2 group flex flex-col items-center cursor-pointer transition hover:border-blue-500 hover:shadow-md"
          >
            <div className="w-full aspect-square rounded-xl bg-slate-950 overflow-hidden flex items-center justify-center border border-slate-200">
              <img
                src="/samples/sample_2_pleural_effusion.png"
                alt="Effusion"
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                onError={(e) => {
                  e.currentTarget.style.display = "none";
                }}
              />
            </div>
            <div className="space-y-0.5">
              <span className="text-xs font-bold text-slate-800 group-hover:text-blue-600 block">
                Effusion
              </span>
              <span className="text-[10px] text-slate-400 block">Blunted CP Angle</span>
            </div>
          </button>

          <button
            onClick={() => onSelectSample("cardiomegaly")}
            disabled={isLoading}
            className="card-surface card-surface-hover rounded-2xl p-2.5 text-center space-y-2 group flex flex-col items-center cursor-pointer transition hover:border-blue-500 hover:shadow-md"
          >
            <div className="w-full aspect-square rounded-xl bg-slate-950 overflow-hidden flex items-center justify-center border border-slate-200">
              <img
                src="/samples/sample_3_cardiomegaly.png"
                alt="Cardiomegaly"
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                onError={(e) => {
                  e.currentTarget.style.display = "none";
                }}
              />
            </div>
            <div className="space-y-0.5">
              <span className="text-xs font-bold text-slate-800 group-hover:text-blue-600 block">
                Cardiomegaly
              </span>
              <span className="text-[10px] text-slate-400 block">CTR &gt; 50%</span>
            </div>
          </button>

          <button
            onClick={() => onSelectSample("pneumothorax")}
            disabled={isLoading}
            className="card-surface card-surface-hover rounded-2xl p-2.5 text-center space-y-2 group flex flex-col items-center cursor-pointer transition hover:border-blue-500 hover:shadow-md"
          >
            <div className="w-full aspect-square rounded-xl bg-slate-950 overflow-hidden flex items-center justify-center border border-slate-200">
              <img
                src="/samples/sample_5_pneumothorax.png"
                alt="Pneumothorax"
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                onError={(e) => {
                  e.currentTarget.style.display = "none";
                }}
              />
            </div>
            <div className="space-y-0.5">
              <span className="text-xs font-bold text-slate-800 group-hover:text-blue-600 block">
                Pneumothorax
              </span>
              <span className="text-[10px] text-slate-400 block">Visceral Pleural Line</span>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
};
