import { StudyAnalysisResponse } from "@/types";

// Configured via NEXT_PUBLIC_API_URL in production (e.g. Modal.com URL or local backend)
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function analyzeRadiograph(
  file: File,
  patientId: string = "PT-RAD-9042",
  age: number = 62,
  gender: string = "M",
  viewPosition: string = "PA"
): Promise<StudyAnalysisResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("patient_id", patientId);
  formData.append("age", age.toString());
  formData.append("gender", gender);
  formData.append("view_position", viewPosition);

  const res = await fetch(`${API_BASE_URL}/api/v1/studies/analyze`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`API analysis failed (${res.status}): ${errorText}`);
  }

  return res.json();
}

export function getStudyPdfUrl(studyId: string): string {
  return `${API_BASE_URL}/api/v1/studies/pdf/${studyId}`;
}

export interface ChatMessageItem {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponseData {
  response: string;
  suggested_questions: string[];
  source: string;
  model_name?: string;
}

export async function sendChatMessage(
  message: string,
  history: ChatMessageItem[],
  studyContext: any,
  mode: "clinical" | "patient" = "clinical",
  preferredModel: "auto" | "gpt_oss_120b" | "gemini" | "gpt4o" | "cds" = "auto"
): Promise<ChatResponseData> {
  const res = await fetch(`${API_BASE_URL}/api/v1/studies/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message,
      history,
      study_context: studyContext,
      study_id: studyContext?.study_id,
      mode,
      preferred_model: preferredModel,
    }),
  });

  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`Chat request failed (${res.status}): ${errorText}`);
  }

  return res.json();
}

export async function getChatProviders(): Promise<{
  gemini: boolean;
  openai_oss: boolean;
  cds_offline: boolean;
}> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/studies/chat/providers`);
    if (res.ok) return res.json();
  } catch (e) {}
  return { gemini: false, openai_oss: false, cds_offline: true };
}


