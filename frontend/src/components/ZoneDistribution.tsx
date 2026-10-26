"use client";

import React from "react";
import { Crosshair } from "lucide-react";
import { ExplainabilityData } from "@/types";

interface ZoneDistributionProps {
  explainability: ExplainabilityData | undefined;
}

export const ZoneDistribution: React.FC<ZoneDistributionProps> = ({ explainability }) => {
  return (
    <div className="glass-panel rounded-xl p-4 shadow-xl">
      <div className="flex items-center justify-between pb-2 border-b border-radDark-700">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
          <Crosshair className="w-4 h-4 text-amber-400" />
          5-Zone Anatomical Distribution
        </h3>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
          {explainability
            ? `${explainability.primary_zone_name} (${explainability.primary_zone_percentage}%)`
            : "--"}
        </span>
      </div>

      <div className="mt-3 space-y-2 text-xs">
        {!explainability ? (
          <div className="text-slate-500 text-center py-4 text-xs">
            Zone mapping active after inference.
          </div>
        ) : (
          Object.entries(explainability.zone_breakdown_pct).map(([zone, zPct]) => {
            const isPrimary = zone === explainability.primary_zone_name;

            return (
              <div key={zone} className="flex items-center justify-between text-xs">
                <span
                  className={`truncate w-32 ${
                    isPrimary ? "font-bold text-amber-300" : "text-slate-400"
                  }`}
                >
                  {zone}
                </span>
                <div className="flex-1 mx-2 bg-radDark-800 rounded-full h-1.5 overflow-hidden">
                  <div
                    className={`${
                      isPrimary ? "bg-amber-400" : "bg-slate-600"
                    } h-1.5 rounded-full`}
                    style={{ width: `${zPct}%` }}
                  ></div>
                </div>
                <span
                  className={`font-mono w-10 text-right ${
                    isPrimary ? "font-bold text-amber-300" : "text-slate-400"
                  }`}
                >
                  {zPct}%
                </span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
