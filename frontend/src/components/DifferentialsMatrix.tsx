"use client";

import React from "react";
import { BarChart2 } from "lucide-react";
import { FindingItem } from "@/types";

interface DifferentialsMatrixProps {
  findings: FindingItem[] | undefined;
}

export const DifferentialsMatrix: React.FC<DifferentialsMatrixProps> = ({ findings }) => {
  return (
    <div className="glass-panel rounded-xl p-4 flex flex-col flex-1 shadow-xl">
      <div className="flex items-center justify-between pb-3 border-b border-radDark-700">
        <div className="flex items-center space-x-2">
          <BarChart2 className="w-5 h-5 text-indigo-400" />
          <h2 className="text-sm font-semibold tracking-wide uppercase text-slate-200">
            14-Pathology Differentials
          </h2>
        </div>
        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
          Calibrated &sigma;(z/T)
        </span>
      </div>

      <p className="text-[11px] text-slate-400 mt-2 mb-3">
        Independent multi-label calibrated probabilities with Youden operating cutoffs.
      </p>

      {/* Disease Bars Container */}
      <div className="flex-1 space-y-2 overflow-y-auto pr-1 max-h-[460px]">
        {!findings || findings.length === 0 ? (
          <div className="text-center py-12 text-slate-500 text-xs">
            Run analysis to populate disease differentials.
          </div>
        ) : (
          findings.map((f) => {
            const isPositive = f.is_detected;
            const pct = f.probability_pct;
            const threshPct = (f.threshold * 100).toFixed(1);

            const barColor = isPositive
              ? "bg-gradient-to-r from-red-600 to-amber-500"
              : "bg-gradient-to-r from-slate-700 to-blue-600";

            const badgeColor = isPositive
              ? "bg-red-500/20 text-red-400 border border-red-500/30"
              : "bg-slate-800 text-slate-400";

            return (
              <div
                key={f.disease}
                className="bg-radDark-900/90 p-2 rounded-lg border border-radDark-700 flex flex-col space-y-1.5 transition hover:border-slate-500"
              >
                <div className="flex items-center justify-between text-xs">
                  <span
                    className={`font-medium ${
                      isPositive ? "font-bold text-white" : "text-slate-200"
                    }`}
                  >
                    {f.disease}
                  </span>
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-[10px] text-slate-400">
                      Cutoff: {threshPct}%
                    </span>
                    <span
                      className={`font-mono font-bold text-xs ${
                        isPositive ? "text-amber-400" : "text-slate-300"
                      }`}
                    >
                      {pct}%
                    </span>
                    <span
                      className={`text-[9px] px-1.5 py-0.2 rounded font-mono ${badgeColor}`}
                    >
                      {isPositive ? "DETECTED" : "UNREMARKABLE"}
                    </span>
                  </div>
                </div>

                <div className="w-full bg-radDark-800 rounded-full h-1.5 overflow-hidden">
                  <div
                    className={`${barColor} h-1.5 rounded-full transition-all duration-500`}
                    style={{ width: `${Math.min(pct, 100)}%` }}
                  ></div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
