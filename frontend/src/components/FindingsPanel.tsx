"use client";

import React from "react";
import { ClipboardList } from "lucide-react";
import { ClinicalReport } from "@/types";

interface FindingsPanelProps {
  report: ClinicalReport | undefined;
}

export const FindingsPanel: React.FC<FindingsPanelProps> = ({ report }) => {
  return (
    <div className="glass-panel rounded-xl p-4 flex flex-col flex-1 shadow-xl">
      <div className="flex items-center justify-between pb-3 border-b border-radDark-700">
        <div className="flex items-center space-x-2">
          <ClipboardList className="w-5 h-5 text-cyan-400" />
          <h2 className="text-sm font-semibold tracking-wide uppercase text-slate-200">
            ACR Clinical Narrative
          </h2>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
          Gemini 2.5 CDS
        </span>
      </div>

      <div className="mt-3 space-y-3 overflow-y-auto pr-1 flex-1 text-xs">
        {!report ? (
          <div className="text-center py-12 text-slate-500">
            Structured narrative will be generated upon study execution.
          </div>
        ) : (
          <>
            <div className="bg-radDark-900 p-2.5 rounded-lg border border-radDark-700">
              <p className="text-[10px] font-mono uppercase text-slate-400">TECHNIQUE</p>
              <p className="text-slate-200 mt-1 leading-relaxed">{report.technique}</p>
            </div>

            <div className="bg-radDark-900 p-2.5 rounded-lg border border-radDark-700">
              <p className="text-[10px] font-mono uppercase text-slate-400">FINDINGS</p>
              <p className="text-slate-200 mt-1 leading-relaxed">{report.findings}</p>
            </div>

            <div className="bg-radDark-900 p-2.5 rounded-lg border border-cyan-800/40 bg-cyan-950/20">
              <p className="text-[10px] font-mono uppercase text-cyan-400 font-bold">
                IMPRESSION
              </p>
              <p className="text-cyan-100 mt-1 font-semibold leading-relaxed">
                {report.impression}
              </p>
            </div>

            <div className="bg-radDark-900 p-2.5 rounded-lg border border-radDark-700">
              <p className="text-[10px] font-mono uppercase text-slate-400">
                DIFFERENTIAL CONSIDERATIONS
              </p>
              <ul className="list-disc list-inside mt-1 text-slate-300 space-y-0.5">
                {report.differential_considerations.map((d, i) => (
                  <li key={i}>{d}</li>
                ))}
              </ul>
            </div>

            <div className="bg-radDark-900 p-2.5 rounded-lg border border-radDark-700">
              <p className="text-[10px] font-mono uppercase text-slate-400">
                RECOMMENDATIONS
              </p>
              <p className="text-slate-300 mt-1 leading-relaxed">
                {report.recommendations}
              </p>
            </div>

            <div className="p-2 rounded bg-red-950/20 border border-red-900/40 text-[10px] text-red-300/80 leading-normal">
              <span className="font-bold">REGULATORY DISCLAIMER:</span> {report.disclaimer}
            </div>
          </>
        )}
      </div>
    </div>
  );
};
