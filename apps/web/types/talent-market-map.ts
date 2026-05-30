// Tipos del Talent Market Map. Espejo de app/schemas/talent_market_map.py.

export type SegmentType = "primary" | "adjacent" | "exploratory";
export type PriorityLevel = "high" | "medium" | "low";
export type ClosenessLevel = "high" | "medium" | "low";
export type ImpactLevel = "high" | "medium" | "low";
export type ConfidenceLevel = "high" | "medium" | "low";
export type MapStatus = "draft" | "generated" | "updated" | "archived";
export type MarketAssessment = "broad" | "moderate" | "narrow" | "very_narrow";

export type SegmentCoverage =
  | "not_started"
  | "in_progress"
  | "partially_covered"
  | "covered"
  | "discarded";

export type CompanyCoverage =
  | "not_reviewed"
  | "in_review"
  | "partially_covered"
  | "covered"
  | "no_relevant_candidates"
  | "discarded";

export type RecommendationStatus = "suggested" | "accepted" | "rejected";

export type MarketSegment = {
  id: number;
  market_map_id: number;
  name: string;
  segment_type: SegmentType;
  description: string | null;
  priority: PriorityLevel;
  coverage_status: SegmentCoverage;
  rationale: string | null;
  sort_order: number;
  ai_suggested: boolean;
  created_at: string;
  updated_at: string;
  candidate_count: number;
};

export type TargetCompany = {
  id: number;
  market_map_id: number;
  segment_id: number | null;
  name: string;
  industry: string | null;
  priority: PriorityLevel;
  rationale: string | null;
  coverage_status: CompanyCoverage;
  notes: string | null;
  ai_suggested: boolean;
  created_at: string;
  updated_at: string;
  candidates_identified: number;
  candidates_evaluated: number;
  high_fit_candidates: number;
};

export type EquivalentRole = {
  id: number;
  market_map_id: number;
  title: string;
  seniority: string | null;
  closeness: ClosenessLevel;
  rationale: string | null;
  priority: PriorityLevel;
  industries: string[];
  ai_suggested: boolean;
  created_at: string;
  updated_at: string;
  candidate_count: number;
};

export type MarketGap = {
  id: number;
  market_map_id: number;
  title: string;
  frequency: number;
  total_evaluated: number;
  impact: ImpactLevel;
  evidence: string | null;
  recommendation: string | null;
  detected_at: string;
};

export type RecalibrationRecommendation = {
  id: number;
  market_map_id: number;
  title: string;
  reason: string;
  expected_impact: string | null;
  confidence: ConfidenceLevel;
  status: RecommendationStatus;
  generated_by: "rules" | "ai";
  acted_at: string | null;
  created_at: string;
};

export type CoverageStats = {
  candidates_identified: number;
  candidates_loaded: number;
  candidates_evaluated: number;
  high_fit: number;
  medium_fit: number;
  low_fit: number;
  discarded: number;
  shortlisted: number;
  target_companies_total: number;
  target_companies_reviewed: number;
  target_companies_pending: number;
  industries_covered: number;
  coverage_pct: number;
};

export type TalentMarketMap = {
  id: number;
  search_mandate_id: number;
  position_spec_id: number | null;
  status: MapStatus;
  executive_summary: string | null;
  executive_summary_for_client: string | null;
  market_assessment: MarketAssessment | null;
  generated_by_model: string | null;
  prompt_version: string | null;
  generated_at: string | null;
  created_at: string;
  updated_at: string;
  segments: MarketSegment[];
  companies: TargetCompany[];
  equivalent_roles: EquivalentRole[];
  gaps: MarketGap[];
  recommendations: RecalibrationRecommendation[];
  coverage: CoverageStats;
};

// --- Etiquetas en español -------------------------------------------------

export const MAP_STATUS_LABELS: Record<MapStatus, string> = {
  draft: "Borrador",
  generated: "Generado",
  updated: "Actualizado",
  archived: "Archivado",
};

export const MARKET_ASSESSMENT_LABELS: Record<MarketAssessment, string> = {
  broad: "Mercado amplio",
  moderate: "Mercado moderado",
  narrow: "Mercado estrecho",
  very_narrow: "Mercado muy estrecho",
};

export const SEGMENT_TYPE_LABELS: Record<SegmentType, string> = {
  primary: "Principal",
  adjacent: "Adyacente",
  exploratory: "Exploratorio",
};

export const PRIORITY_LABELS: Record<PriorityLevel, string> = {
  high: "Alta",
  medium: "Media",
  low: "Baja",
};

export const CLOSENESS_LABELS: Record<ClosenessLevel, string> = {
  high: "Cercanía alta",
  medium: "Cercanía media",
  low: "Cercanía baja",
};

export const IMPACT_LABELS: Record<ImpactLevel, string> = {
  high: "Impacto alto",
  medium: "Impacto medio",
  low: "Impacto bajo",
};

export const SEGMENT_COVERAGE_LABELS: Record<SegmentCoverage, string> = {
  not_started: "Sin iniciar",
  in_progress: "En progreso",
  partially_covered: "Parcialmente cubierto",
  covered: "Cubierto",
  discarded: "Descartado",
};

export const COMPANY_COVERAGE_LABELS: Record<CompanyCoverage, string> = {
  not_reviewed: "Sin revisar",
  in_review: "En revisión",
  partially_covered: "Parcialmente cubierta",
  covered: "Cubierta",
  no_relevant_candidates: "Sin candidatos relevantes",
  discarded: "Descartada",
};

export const RECOMMENDATION_STATUS_LABELS: Record<RecommendationStatus, string> = {
  suggested: "Sugerida",
  accepted: "Aceptada",
  rejected: "Descartada",
};
