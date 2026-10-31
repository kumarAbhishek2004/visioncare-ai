"use client";

import React from "react";
import { Activity, MessageSquare } from "lucide-react";

interface NavbarProps {
  activeNav: "home" | "analyze" | "chat" | "reports" | "studies" | "about";
  onNavChange: (nav: "home" | "analyze" | "chat" | "reports" | "studies" | "about") => void;
  hasStudy: boolean;
  onOpenChat?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeNav,
  onNavChange,
  hasStudy,
  onOpenChat,
}) => {
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Left: Brand Logo */}
        <button
          onClick={() => onNavChange("home")}
          className="flex items-center space-x-2.5 text-left focus:outline-none group"
        >
          <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-sm shadow-blue-500/30 group-hover:bg-blue-700 transition">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <div>
            <span className="text-lg font-bold tracking-tight text-slate-900">
              VisionCare <span className="text-blue-600">AI</span>
            </span>
          </div>
        </button>

        {/* Center: Navigation Links */}
        <nav className="hidden md:flex items-center space-x-1 lg:space-x-2">
          <button
            onClick={() => onNavChange("home")}
            className={`px-3.5 py-1.5 rounded-lg text-sm font-medium transition ${
              activeNav === "home"
                ? "text-blue-600 font-semibold border-b-2 border-blue-600 rounded-b-none pb-2"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
            }`}
          >
            Home
          </button>
          <button
            onClick={() => onNavChange("analyze")}
            className={`px-3.5 py-1.5 rounded-lg text-sm font-medium transition ${
              activeNav === "analyze"
                ? "text-blue-600 font-semibold border-b-2 border-blue-600 rounded-b-none pb-2"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
            }`}
          >
            Analyze
          </button>
          <button
            onClick={() => onNavChange("chat")}
            className={`px-3.5 py-1.5 rounded-lg text-sm font-medium transition flex items-center gap-1.5 ${
              activeNav === "chat"
                ? "text-blue-600 font-semibold border-b-2 border-blue-600 rounded-b-none pb-2"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
            }`}
          >
            <MessageSquare className="w-3.5 h-3.5 text-blue-600" />
            <span>AI Copilot</span>
          </button>
          <button
            onClick={() => onNavChange("reports")}
            className={`px-3.5 py-1.5 rounded-lg text-sm font-medium transition ${
              activeNav === "reports"
                ? "text-blue-600 font-semibold border-b-2 border-blue-600 rounded-b-none pb-2"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
            }`}
          >
            Reports
          </button>
          <button
            onClick={() => onNavChange("studies")}
            className={`px-3.5 py-1.5 rounded-lg text-sm font-medium transition ${
              activeNav === "studies"
                ? "text-blue-600 font-semibold border-b-2 border-blue-600 rounded-b-none pb-2"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
            }`}
          >
            Studies
          </button>
          <button
            onClick={() => onNavChange("about")}
            className={`px-3.5 py-1.5 rounded-lg text-sm font-medium transition ${
              activeNav === "about"
                ? "text-blue-600 font-semibold border-b-2 border-blue-600 rounded-b-none pb-2"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
            }`}
          >
            About
          </button>
        </nav>

        {/* Right: Quick Action Chatbot Trigger */}
        <div className="flex items-center space-x-2">
          <button
            onClick={onOpenChat}
            className="inline-flex items-center space-x-2 bg-gradient-to-r from-blue-50 to-indigo-50 hover:from-blue-100 hover:to-indigo-100 text-blue-700 font-semibold text-xs px-3.5 py-2 rounded-xl border border-blue-200 shadow-xs hover:shadow transition cursor-pointer"
            title="Ask AI Copilot anytime without uploading an X-ray"
          >
            <MessageSquare className="w-3.5 h-3.5 text-blue-600" />
            <span>Ask AI Copilot</span>
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          </button>
        </div>
      </div>
    </header>
  );
};
