"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Send,
  MessageSquare,
  User,
  RotateCcw,
  Activity,
  Copy,
  Check,
  X,
  ArrowLeft,
  ChevronDown
} from "lucide-react";
import { StudyAnalysisResponse } from "@/types";
import { sendChatMessage, getChatProviders, ChatMessageItem } from "@/lib/api";

interface ClinicalChatbotProps {
  study: StudyAnalysisResponse | null;
  isFloating?: boolean;
  onClose?: () => void;
  onBackToOverview?: () => void;
}

export const ClinicalChatbot: React.FC<ClinicalChatbotProps> = ({
  study,
  isFloating = false,
  onClose,
  onBackToOverview,
}) => {
  const [messages, setMessages] = useState<ChatMessageItem[]>([
    {
      role: "assistant",
      content: study
        ? `Hello! I am your **VisionCare Clinical Copilot**. I have reviewed the radiograph findings for **Patient ${study.patient_id}**:\n\n• **Primary Assessment:** **${study.classification.all_predictions?.[0]?.disease || "Clear"}** (${study.classification.all_predictions?.[0]?.probability_pct || 0}% confidence)\n• **Visual Localization:** Focus concentrated in the **${study.explainability.primary_zone_name || "Bilateral Lungs"}**\n• **Heart Size (CTR):** Transverse cardiothoracic ratio is **${study.ctr?.ctr_percentage || "--"}%** (${study.ctr?.is_cardiomegaly ? "Cardiomegaly" : "Normal"})\n• **Image Quality:** **${Math.round(study.iqa.overall_score)}/100** (${study.iqa.quality_tier})\n\nFeel free to ask any question about this patient's report, findings, heatmaps, or general clinical radiology concepts.`
        : "Hello! I am your **VisionCare Clinical Copilot**.\n\nYou can ask me any general questions about chest radiographs, pulmonary diseases, symptoms, or how AI diagnostic models work.\n\nOnce you upload or select a scan in the **Analyze** tab, I will also have full access to its specific findings, heatmaps, and diagnostic report.",
    },
  ]);

  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [mode, setMode] = useState<"clinical" | "patient">("clinical");
  const [preferredModel, setPreferredModel] = useState<"auto" | "gpt_oss_120b" | "gemini" | "gpt4o" | "cds">("auto");
  const [activeModelLabel, setActiveModelLabel] = useState<string>("GPT OSS 120B / CDS");
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [providers, setProviders] = useState<{ gemini: boolean; openai_oss: boolean; cds_offline: boolean }>({
    gemini: false,
    openai_oss: false,
    cds_offline: true,
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const previousStudyIdRef = useRef<string | null>(study?.study_id || null);

  // Auto-scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // When a study is analyzed and injected into an already-open chatbot context
  useEffect(() => {
    const currentId = study?.study_id || null;
    if (currentId && currentId !== previousStudyIdRef.current) {
      previousStudyIdRef.current = currentId;
      const topFinding = study?.classification?.all_predictions?.[0]?.disease || "Clear";
      const topProb = study?.classification?.all_predictions?.[0]?.probability_pct || 0;
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `📁 **Radiograph Analysis Loaded for Patient ${study.patient_id}**\n\n• **Primary Assessment:** **${topFinding}** (${topProb}% confidence)\n• **Visual Localization:** Focus in the **${study.explainability.primary_zone_name || "Bilateral Lungs"}**\n• **Heart Size (CTR):** **${study.ctr?.ctr_percentage || "--"}%** (${study.ctr?.is_cardiomegaly ? "Cardiomegaly" : "Normal"})\n• **Image Quality:** **${Math.round(study.iqa.overall_score)}/100**\n\nI now have full telemetry and report data for this radiograph. Feel free to ask about these specific findings, heatmaps, or clinical biometrics!`,
        },
      ]);
    }
  }, [study]);

  // Check available backend LLM providers on mount
  useEffect(() => {
    getChatProviders().then((res) => setProviders(res));
  }, []);

  // Keyboard shortcut: Escape closes the floating assistant
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (isFloating && onClose) onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isFloating, onClose]);

  // Persona-tailored suggestions (Doctor vs Patient)
  const clinicalSuggestions = study
    ? [
        "Review formal ACR Impression & Findings",
        "Why were other differentials ruled out ('Why Not?')",
        `Examine CTR biometrics (${study.ctr?.ctr_percentage || "--"}%) and calipers`,
        `Inspect Grad-CAM++ regional attribution in the ${study.explainability.primary_zone_name || "lungs"}`,
        "Review Level 5 counterfactual causal test",
      ]
    : [
        "What are the diagnostic thresholds for the 14 conditions?",
        "How is the Cardiothoracic Ratio (CTR) measured?",
        "What does Grad-CAM++ feature attribution signify in radiology?",
        "How do radiologists differentiate pneumonia from effusion?",
      ];

  const patientSuggestions = study
    ? [
        "Can you explain my X-ray results in simple everyday words?",
        "Do I have any signs of pneumonia, fluid, or lung problems?",
        `Is my heart size normal or should I be worried? (CTR: ${study.ctr?.ctr_percentage || "--"}%)`,
        "What important questions should I ask my doctor about this report?",
        "What does the colored heatmap mean on my chest scan?",
      ]
    : [
        "What is pneumonia and how does a chest X-ray detect it?",
        "What is an enlarged heart and what causes it?",
        "How safe is a chest X-ray and how does it work?",
        "What are common symptoms of fluid around the lungs (effusion)?",
      ];

  const [activeSuggestions, setActiveSuggestions] = useState<string[]>(
    mode === "patient" ? patientSuggestions : clinicalSuggestions
  );

  // Synchronize suggestions whenever mode or study context changes
  useEffect(() => {
    setActiveSuggestions(mode === "patient" ? patientSuggestions : clinicalSuggestions);
  }, [mode, study]);

  const handleModeChange = (newMode: "clinical" | "patient") => {
    if (newMode === mode) return;
    setMode(newMode);
    setActiveSuggestions(newMode === "patient" ? patientSuggestions : clinicalSuggestions);

    // Visible confirmation message in chat so the user immediately sees the change!
    setMessages((prev) => [
      ...prev,
      {
        role: "assistant",
        content:
          newMode === "patient"
            ? "👤 **Patient Mode Activated**\n\nI will now explain all findings in simple, easy-to-understand language with no complex medical jargon.\n\nClick any of the suggested questions below or ask anything about your scan!"
            : "🩺 **Doctor Mode Activated**\n\nClinical Decision Support active. I will now use formal ACR radiology terminology, calibrated multi-label probabilities, differential exclusions, and quantitative biometrics.",
      },
    ]);
  };

  const handleSendMessage = async (textToSend?: string) => {
    const text = textToSend || inputMessage;
    if (!text.trim() || isLoading) return;

    const userMsg: ChatMessageItem = { role: "user", content: text };
    const updatedHistory = [...messages, userMsg];
    setMessages(updatedHistory);
    setInputMessage("");
    setIsLoading(true);

    try {
      const res = await sendChatMessage(
        text,
        updatedHistory,
        study,
        mode,
        preferredModel
      );

      setActiveModelLabel(res.model_name || res.source);

      if (res.suggested_questions && res.suggested_questions.length > 0) {
        setActiveSuggestions(res.suggested_questions);
      }

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: res.response,
        },
      ]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Unable to connect to assistant: ${err.message || "Failed to process question."}\n\nPlease try again or switch to Clinical CDS mode.`,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const handleResetChat = () => {
    setMessages([
      {
        role: "assistant",
        content: study
          ? `Conversation reset. Ready to answer questions on **Patient ${study.patient_id}** and its diagnostic findings.`
          : "Conversation reset. Ready to answer questions on chest radiography, thoracic medicine, and AI explainability.",
      },
    ]);
  };

  /**
   * Parses markdown inline styling, converting **bold** to <strong> tags
   * and stripping any raw unrendered asterisks.
   */
  const renderFormattedLine = (lineText: string, isUser: boolean = false) => {
    // Regex splits by **bold text**
    const parts = lineText.split(/(\*\*[^*]+\*\*)/g);

    return parts.map((part, index) => {
      if (part.startsWith("**") && part.endsWith("**") && part.length > 4) {
        return (
          <strong key={index} className={`font-bold ${isUser ? "text-white" : "text-slate-900"}`}>
            {part.slice(2, -2)}
          </strong>
        );
      }

      // Check for *italic* if present
      if (part.startsWith("*") && part.endsWith("*") && part.length > 2) {
        return (
          <em key={index} className={`italic ${isUser ? "text-blue-100" : "text-slate-700"}`}>
            {part.slice(1, -1)}
          </em>
        );
      }

      // Strip any stray unclosed double asterisks
      const clean = part.replace(/\*\*/g, "");
      return <span key={index}>{clean}</span>;
    });
  };

  return (
    <>
      {/* Dimmed backdrop when in floating modal mode */}
      {isFloating && (
        <div
          onClick={onClose}
          className="fixed inset-0 bg-slate-900/30 backdrop-blur-[2px] z-40 transition-opacity animate-fade-in"
        />
      )}

      <div
        className={`card-surface flex flex-col overflow-hidden bg-white ${
          isFloating
            ? "fixed bottom-5 right-5 w-[94vw] sm:w-[490px] h-[670px] max-h-[88vh] rounded-3xl shadow-2xl z-50 border-2 border-blue-500/40 animate-scale-in"
            : "w-full rounded-3xl shadow-sm border border-slate-200 min-h-[660px]"
        }`}
      >
        {/* 1. Chat Header (Clean layout without overlapping telemetry pills) */}
        <div className="p-3.5 sm:p-4 bg-white border-b border-slate-200 flex flex-wrap items-center justify-between gap-3 shrink-0">
          <div className="flex items-center space-x-3 min-w-0">
            {/* If tabbed view, show Back Button */}
            {!isFloating && onBackToOverview && (
              <button
                onClick={onBackToOverview}
                className="p-2 rounded-xl text-slate-500 hover:text-slate-900 hover:bg-slate-100 border border-slate-200 transition shrink-0 cursor-pointer"
                title="Back to Overview"
              >
                <ArrowLeft className="w-4 h-4" />
              </button>
            )}

            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center shadow-md shadow-blue-500/25 shrink-0">
              <Activity className="w-5 h-5 text-white" />
            </div>

            <div className="min-w-0">
              <h3 className="text-sm font-bold text-slate-900 tracking-tight truncate">
                Clinical Copilot
              </h3>
              <p className="text-[11px] text-slate-500 truncate">
                {study ? `Patient ${study.patient_id} • ${activeModelLabel}` : "General Radiology & Medical Doubts"}
              </p>
            </div>
          </div>

          {/* Action Controls */}
          <div className="flex items-center space-x-2 shrink-0">
            {/* Model Selector Dropdown */}
            <div className="relative">
              <select
                value={preferredModel}
                onChange={(e) => setPreferredModel(e.target.value as any)}
                className="text-[10px] font-semibold bg-slate-100 hover:bg-slate-200/80 text-slate-700 py-1.5 pl-2.5 pr-6 rounded-xl border border-slate-200 appearance-none focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
                title="Select AI Model Engine"
              >
                <option value="auto">Auto (Best Available)</option>
                <option value="gpt_oss_120b">GPT OSS 120B (Open-Source)</option>
                <option value="gemini">Google Gemini 2.5</option>
                <option value="gpt4o">OpenAI GPT-4o</option>
                <option value="cds">Clinical CDS (Offline)</option>
              </select>
              <ChevronDown className="w-3 h-3 text-slate-400 absolute right-2 top-2.5 pointer-events-none" />
            </div>

            {/* Tone Toggle (Doctor vs Patient) */}
            <div className="bg-slate-100 p-0.5 rounded-xl border border-slate-200 flex items-center text-[10px] font-semibold">
              <button
                onClick={() => handleModeChange("clinical")}
                className={`px-2.5 py-1 rounded-lg transition cursor-pointer flex items-center gap-1 ${
                  mode === "clinical"
                    ? "bg-blue-600 text-white shadow-xs font-bold"
                    : "text-slate-600 hover:text-slate-900"
                }`}
                title="Doctor Mode: Clinical terminology, calibrated probabilities, and biometrics"
              >
                <span>🩺</span>
                <span>Doctor</span>
              </button>
              <button
                onClick={() => handleModeChange("patient")}
                className={`px-2.5 py-1 rounded-lg transition cursor-pointer flex items-center gap-1 ${
                  mode === "patient"
                    ? "bg-emerald-600 text-white shadow-xs font-bold"
                    : "text-slate-600 hover:text-slate-900"
                }`}
                title="Patient Mode: Clear, friendly, non-jargon explanations"
              >
                <span>👤</span>
                <span>Patient</span>
              </button>
            </div>

            {/* Reset Chat button */}
            <button
              onClick={handleResetChat}
              className="p-1.5 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 border border-slate-200 transition cursor-pointer"
              title="Reset conversation"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>

            {/* Prominent Close Button (Floating Mode) */}
            {isFloating && onClose && (
              <button
                onClick={onClose}
                className="w-8 h-8 rounded-xl bg-slate-100 hover:bg-rose-50 hover:text-rose-600 hover:border-rose-200 text-slate-600 flex items-center justify-center border border-slate-200 transition cursor-pointer shadow-xs group"
                title="Close Assistant (Esc)"
              >
                <X className="w-4 h-4 group-hover:scale-110 transition-transform" />
              </button>
            )}

            {/* Close Button (Tabbed Full-Page Mode) */}
            {!isFloating && onBackToOverview && (
              <button
                onClick={onBackToOverview}
                className="inline-flex items-center space-x-1 px-2.5 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-[11px] font-bold border border-slate-200 transition cursor-pointer"
                title="Return to Overview"
              >
                <X className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Close</span>
              </button>
            )}
          </div>
        </div>

        {/* Active Persona Notification Banner */}
        <div
          className={`px-4 py-2 text-xs flex items-center justify-between border-b transition-colors shrink-0 ${
            mode === "patient"
              ? "bg-emerald-50/80 border-emerald-200/70 text-emerald-900"
              : "bg-blue-50/80 border-blue-200/70 text-blue-900"
          }`}
        >
          <div className="flex items-center space-x-2">
            <span
              className={`w-2 h-2 rounded-full ${
                mode === "patient" ? "bg-emerald-500 animate-pulse" : "bg-blue-600"
              }`}
            />
            <span className="font-bold">
              {mode === "patient" ? "👤 Patient Mode Active" : "🩺 Doctor Mode Active"}
            </span>
            <span className="text-[11px] opacity-80 hidden sm:inline">
              {mode === "patient"
                ? "— Plain language, reassuring analogies & questions for your doctor"
                : "— ACR clinical terminology, calibrated probabilities & CTR biometrics"}
            </span>
          </div>
          <span
            className={`text-[10px] font-bold px-2 py-0.5 rounded-full border shadow-xs ${
              mode === "patient"
                ? "bg-white text-emerald-800 border-emerald-300"
                : "bg-white text-blue-800 border-blue-300"
            }`}
          >
            {mode === "patient" ? "Everyday Language" : "Clinical CDS"}
          </span>
        </div>

        {/* 2. Messages Stream */}
        <div className="flex-1 p-4 sm:p-5 overflow-y-auto space-y-4 bg-slate-50/60">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex items-start gap-3 ${
                msg.role === "user" ? "flex-row-reverse" : "flex-row"
              } animate-fade-in`}
            >
              {/* Avatar */}
              <div
                className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 shadow-xs ${
                  msg.role === "user"
                    ? "bg-slate-900 text-white"
                    : "bg-blue-600 text-white shadow-blue-500/20"
                }`}
              >
                {msg.role === "user" ? (
                  <User className="w-4 h-4" />
                ) : (
                  <Activity className="w-4 h-4" />
                )}
              </div>

              {/* Message Bubble */}
              <div
                className={`relative group max-w-[85%] rounded-2xl p-4 text-xs leading-relaxed space-y-2 shadow-xs ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white font-medium rounded-tr-none shadow-blue-500/10"
                    : "bg-white text-slate-800 border border-slate-200/90 rounded-tl-none shadow-xs"
                }`}
              >
                {/* Copy action */}
                {msg.role === "assistant" && (
                  <button
                    onClick={() => handleCopy(msg.content, idx)}
                    className="absolute top-2.5 right-2.5 opacity-0 group-hover:opacity-100 text-slate-400 hover:text-slate-700 p-1 rounded-lg hover:bg-slate-100 transition cursor-pointer"
                    title="Copy message"
                  >
                    {copiedIndex === idx ? (
                      <Check className="w-3.5 h-3.5 text-emerald-600" />
                    ) : (
                      <Copy className="w-3.5 h-3.5" />
                    )}
                  </button>
                )}

                {/* Render clean formatted message content without raw asterisks */}
                <div className="space-y-1.5 font-sans">
                  {msg.content.split("\n").map((line, i) => {
                    const trimmed = line.trim();

                    // Section Heading: ### Heading or ## Heading
                    if (trimmed.startsWith("### ") || trimmed.startsWith("## ")) {
                      const headingText = trimmed.replace(/^#+\s*/, "");
                      return (
                        <h4
                          key={i}
                          className="font-bold text-sm text-slate-900 pt-1.5 pb-0.5 border-b border-slate-100 mb-1"
                        >
                          {renderFormattedLine(headingText)}
                        </h4>
                      );
                    }

                    // Bullet item: • or - or *
                    if (trimmed.startsWith("• ") || trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
                      const bulletText = trimmed.replace(/^[•\-*]\s*/, "");
                      return (
                        <div key={i} className="flex items-start space-x-2 pl-0.5 py-0.5">
                          <span className={`w-1.5 h-1.5 rounded-full shrink-0 mt-1.5 ${
                            msg.role === "user" ? "bg-white" : "bg-blue-600"
                          }`}></span>
                          <div className={`leading-relaxed ${
                            msg.role === "user" ? "text-white" : "text-slate-700"
                          }`}>
                            {renderFormattedLine(bulletText, msg.role === "user")}
                          </div>
                        </div>
                      );
                    }

                    // Blank line spacing
                    if (trimmed === "") {
                      return <div key={i} className="h-1" />;
                    }

                    // Normal paragraph
                    return (
                      <p key={i} className={`leading-relaxed ${
                        msg.role === "user" ? "text-white font-medium" : "text-slate-700"
                      }`}>
                        {renderFormattedLine(line, msg.role === "user")}
                      </p>
                    );
                  })}
                </div>
              </div>
            </div>
          ))}

          {/* Loading indicator */}
          {isLoading && (
            <div className="flex items-start gap-3 animate-fade-in">
              <div className="w-8 h-8 rounded-xl bg-blue-600 text-white flex items-center justify-center shrink-0 shadow-xs shadow-blue-500/20">
                <Activity className="w-4 h-4" />
              </div>
              <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-none p-4 shadow-xs space-y-1.5">
                <div className="flex items-center space-x-1.5">
                  <span className="w-2 h-2 rounded-full bg-blue-600 animate-bounce"></span>
                  <span className="w-2 h-2 rounded-full bg-blue-400 animate-bounce [animation-delay:0.2s]"></span>
                  <span className="w-2 h-2 rounded-full bg-blue-200 animate-bounce [animation-delay:0.4s]"></span>
                </div>
                <span className="text-[10px] text-slate-400 font-medium block">
                  Reviewing radiograph findings and report...
                </span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* 3. Dynamic Quick Questions Bar */}
        <div className="px-4 py-2 bg-white border-t border-slate-100 flex items-center gap-1.5 overflow-x-auto no-scrollbar shrink-0">
          <MessageSquare className="w-3.5 h-3.5 text-blue-600 shrink-0" />
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider shrink-0 mr-1">
            Suggested:
          </span>
          {activeSuggestions.map((q, idx) => (
            <button
              key={idx}
              onClick={() => handleSendMessage(q)}
              disabled={isLoading}
              className="text-[11px] font-semibold text-slate-700 bg-slate-100 hover:bg-blue-50 hover:text-blue-700 hover:border-blue-200 px-3 py-1 rounded-full border border-slate-200 whitespace-nowrap transition shrink-0 cursor-pointer"
            >
              {q}
            </button>
          ))}
        </div>

        {/* 4. Input Bar */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="p-3 bg-white border-t border-slate-200 flex items-center gap-2 shrink-0"
        >
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder={
              mode === "clinical"
                ? "Ask about the report, findings, zones, CTR calipers, or general doubts..."
                : "Ask any question about this X-ray in plain language..."
            }
            disabled={isLoading}
            className="flex-1 bg-slate-50 border border-slate-200 rounded-2xl px-4 py-2.5 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition"
          />

          <button
            type="submit"
            disabled={!inputMessage.trim() || isLoading}
            className="w-10 h-10 rounded-2xl bg-blue-600 hover:bg-blue-700 disabled:bg-slate-200 text-white flex items-center justify-center transition shadow-md shadow-blue-500/20 shrink-0 cursor-pointer disabled:cursor-not-allowed"
            title="Send message"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </>
  );
};