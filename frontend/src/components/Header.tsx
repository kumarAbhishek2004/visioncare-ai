"use client";

import React from "react";
import { Activity, UploadCloud, Sparkles, FileDown } from "lucide-react";
import { StudyAnalysisResponse } from "@/types";
import { getStudyPdfUrl } from "@/lib/api";

interface HeaderProps {
  study: StudyAnalysisResponse | null;
  onUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onLoadSample: () => void;
  isLoading: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  study,
  onUpload,
  onLoadSample,
  isLoading,
}) => {
  return (
    <header className="bg-radDark-900 border-b border-radDark-700 px-6 py-3 flex items-center justify-between sticky top-0 z-50 shadow-lg">
      <div className="flex items-center space-x-4">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-tr from-blue-700 to-cyan-500 flex items-center justify-center shadow-md shadow-blue-500/20">
          <Activity className="w-6 h-6 text-white" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
              VisionCare AI
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30">
                v1.0 SaMD CDS
              </span>
            </h1>
          </div>
          <p className="text-xs text-slate-400">
            Explainable AI-Assisted Radiology Workstation • Frontal CXR NIH-14
          </p>
        </div>
      </div>

      {study && (
        <div className="hidden md:flex items-center space-x-6 text-xs bg-radDark-850 px-4 py-2 rounded-lg border border-radDark-700">
          <div>
            <span className="text-slate-500 uppercase font-mono">Patient:</span>{" "}
            <span className="font-semibold text-slate-200">{study.patient_id}</span>
          </div>
          <div>
            <span className="text-slate-500 uppercase font-mono">Age/Sex:</span>{" "}
            <span className="font-semibold text-slate-200">
              {study.demographics.age}Y / {study.demographics.gender}
            </span>
          </div>
          <div>
            <span className="text-slate-500 uppercase font-mono">View:</span>{" "}
            <span className="font-semibold text-slate-200">
              {study.demographics.view_position} Frontal
            </span>
          </div>
          <div>
            <span className="text-slate-500 uppercase font-mono">Study ID:</span>{" "}
            <span className="font-mono text-cyan-400">{study.study_id}</span>
          </div>
        </div>
      )}

      <div className="flex items-center space-x-3">
        <label className="cursor-pointer inline-flex items-center space-x-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-4 py-2.5 rounded-lg shadow-sm transition">
          <UploadCloud className="w-4 h-4" />
          <span>Upload Radiograph</span>
          <input
            type="file"
            accept="image/*"
            className="hidden"
            onChange={onUpload}
            disabled={isLoading}
          />
        </label>

        <button
          onClick={onLoadSample}
          disabled={isLoading}
          className="inline-flex items-center space-x-2 bg-radDark-800 hover:bg-radDark-700 text-slate-300 text-xs font-semibold px-3 py-2.5 rounded-lg border border-radDark-700 transition disabled:opacity-50"
        >
          <Sparkles className="w-4 h-4 text-cyan-400" />
          <span>Load Sample</span>
        </button>

        <button
          onClick={() => {
            if (study) window.location.href = getStudyPdfUrl(study.study_id);
          }}
          disabled={!study || isLoading}
          className="disabled:opacity-40 disabled:cursor-not-allowed inline-flex items-center space-x-2 bg-emerald-700 hover:bg-emerald-600 text-white text-xs font-semibold px-4 py-2.5 rounded-lg shadow-sm transition"
        >
          <FileDown className="w-4 h-4" />
          <span>Export Clinical PDF</span>
        </button>
      </div>
    </header>
  );
};
