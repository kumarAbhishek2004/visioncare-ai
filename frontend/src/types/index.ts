export interface FindingItem {
  disease: string;
  probability: number;
  probability_pct: number;
  threshold: number;
  is_detected: boolean;
  confidence_tier: string;
  ci_lower?: number;
  ci_upper?: number;
  epistemic_uncertainty?: number;
  decision_margin?: number;
  boundary_stability?: "ROBUST" | "BORDERLINE" | "CLEAR_NEGATIVE";
}

export interface BBoxItem {
  bbox_pixels: [number, number, number, number];
  center: [number, number];
  area_pixels: number;
  mean_activation: number;
  dimensions_cm?: {
    width_cm: number;
    height_cm: number;
  };
}

export interface DecisionTraceStep {
  step: number;
  module: string;
  status: string;
  summary: string;
}

export interface DecisionTrace {
  trace_id: string;
  study_id: string;
  generated_at: string;
  total_steps: number;
  safety_status: string;
  steps: DecisionTraceStep[];
}

export interface ClinicalReport {
  technique: string;
  findings: string;
  impression: string;
  differential_considerations: string[];
  recommendations: string;
  disclaimer: string;
}

export interface IQAData {
  overall_score: number;
  quality_tier: string;
  recommendation: string;
  laplacian_variance: number;
  dynamic_range: number;
  michelson_contrast: number;
  under_exposed_pct: number;
  over_exposed_pct: number;
}

export interface PulmonaryExtractionData {
  validation_status: string;
  lung_area_ratio: number;
  right_lung_area_ratio?: number;
  left_lung_area_ratio?: number;
  lung_symmetry_index?: number;
  thoracic_box?: [number, number, number, number];
  thoracic_envelope?: [number, number, number, number];
  is_valid_frontal_chest?: boolean;
  is_valid_frontal?: boolean;
  status_message?: string;
  warning_flag?: string;
}

export interface ClassificationData {
  all_findings?: FindingItem[];
  all_predictions?: FindingItem[];
  primary_findings: FindingItem[];
  associated_findings: FindingItem[];
  prediction_reliability: "HIGH" | "MODERATE" | "LOW";
  safety_triage: "ASSISTED_REVIEW_READY" | "MANUAL_REVIEW_MANDATORY" | "NO_ACUTE_PATHOLOGY";
  triage_message?: string;
  temperature_scaling_applied?: boolean;
  calibrated?: boolean;
  max_probability?: number;
}

export interface ExplainabilityData {
  xai_method?: string;
  available_methods?: string[];
  target_pathology?: string;
  primary_zone_name: string;
  primary_zone_percentage: number;
  secondary_zone?: string;
  secondary_zone_percentage?: number;
  zone_breakdown_pct: Record<string, number>;
  clinical_summary: string;
  bounding_boxes: BBoxItem[];
}

export interface CTRData {
  ctr_percentage: number;
  cardiac_diameter_pixels: number;
  thoracic_diameter_pixels: number;
  cardiac_diameter_cm: number;
  thoracic_diameter_cm: number;
  category: "NORMAL" | "BORDERLINE_CARDIOMEGALY" | "OVERT_CARDIOMEGALY" | "SEVERE_CARDIOMEGALY";
  is_cardiomegaly: boolean;
  interpretation: string;
}

export interface EmergencyTriageData {
  priority_tier: "STAT_CRITICAL" | "URGENT" | "ROUTINE";
  urgency_score: number;
  sla_turnaround: string;
  action_pathway: string;
  triggered_criteria: string[];
}

export interface StudyAnalysisResponse {
  study_id: string;
  timestamp: string;
  patient_id: string;
  demographics: {
    age?: number;
    gender?: string;
    view_position?: string;
    pixel_spacing?: [number, number];
    is_dicom?: boolean;
  };
  iqa: IQAData;
  pulmonary_extraction: PulmonaryExtractionData;
  classification: ClassificationData;
  explainability: ExplainabilityData;
  ctr?: CTRData;
  emergency_triage?: EmergencyTriageData;
  clinical_report: ClinicalReport;
  decision_trace: DecisionTrace;
  image_assets: {
    original: string;
    enhanced: string;
    enhanced_bone?: string;
    enhanced_inverted?: string;
    lung_mask: string;
    overlay_mask: string;
    heatmap_overlay: string;
    caliper_overlay?: string;
  };
}
