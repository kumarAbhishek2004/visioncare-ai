"use client";

import React from "react";
import { ShieldCheck } from "lucide-react";
import { DecisionTrace as TraceType } from "@/types";

interface DecisionTraceProps {
  trace: TraceType | undefined;
}

export const DecisionTrace: React.FC<DecisionTraceProps> = ({ trace }) => {
  return (
    <div className="glass-panel rounded-xl p-4 shadow-xl">
      <div className="flex items-center justify-between pb-2 border-b border-radDark-700">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          Auditable Decision Trace
        </h3>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300">
          {trace ? `${trace.total_steps} Steps` : "7 Steps"}
        </span>
      </div>

      <div className="mt-3 space-y-2 max-h-48 overflow-y-auto pr-1 text-xs">
        {!trace ? (
          <div className="text-slate-500 text-center py-4">
            Trace log records each inference stage.
          </div>
        ) : (
          trace.steps.map((s) => (
            <div
              key={s.step}
              className="flex items-start space-x-2 p-1.5 rounded bg-radDark-900/70 border border-radDark-700/60 text-[11px]"
            >
              <span className="font-mono text-cyan-400 font-bold text-[10px] mt-0.5">
                S{s.step}
              </span>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-200">{s.module}</span>
                  <span className="font-mono text-[9px] px-1 rounded bg-emerald-900/40 text-emerald-300">
                    {s.status}
                  </span>
                </div>
                <p className="text-slate-400 text-[10px] mt-0.5">{s.summary}</p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
