import { StudyAnalysisResponse } from "@/types";

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
