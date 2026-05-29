// Estados de feedback del cliente: 3 históricos + 5 nuevos de Decision Room.
export type ClientFeedbackStatus =
  | "interested"
  | "not_interested"
  | "want_interview"
  | "favorite"
  | "interview_requested"
  | "more_info_requested"
  | "keep_in_review"
  | "rejected";

export type DecisionRoomStatus =
  | "draft"
  | "ready_to_share"
  | "invitation_sent"
  | "viewed"
  | "in_review"
  | "feedback_received"
  | "closed"
  | "expired";

export type ConsultantRecommendation =
  | "highly_recommended"
  | "recommended"
  | "recommended_with_validations"
  | "reserve"
  | "not_recommended";

export type EvidenceLevel = "high" | "medium" | "low";

export type ShortlistItem = {
  id: number;
  shortlist_id: number;
  candidate_id: number;
  evaluation_id: number | null;
  order_index: number;
  is_pinned: boolean;
  recommendation: ConsultantRecommendation | null;
  consultant_summary: string | null;
  why_fits: string[];
  risks_or_validations: string[];
  evidence_level: EvidenceLevel | null;
  availability: string | null;
  salary_expectation: string | null;
  salary_share_authorized: boolean;
  rating: number | null;
  client_status: ClientFeedbackStatus | null;
  client_comment: string | null;
  status_updated_at: string | null;
  created_at: string;
  // Enriquecido por el backend para evitar N+1 en la UI consultor.
  candidate_name: string | null;
  candidate_current_position: string | null;
  candidate_current_company: string | null;
  candidate_linkedin_url: string | null;
  evaluation_score: number | null;
  evaluation_score_category: string | null;
};

export type ClientShortlist = {
  id: number;
  mandate_id: number;
  public_token: string;
  title: string;
  message_to_client: string;
  intro_message: string | null;
  show_scores: boolean;
  show_availability: boolean;
  show_salary: boolean;
  show_risks: boolean;
  show_comparison: boolean;
  allow_comments: boolean;
  allow_rating: boolean;
  allow_report_download: boolean;
  access_code_required: boolean;
  access_code_expires_at: string | null;
  expires_at: string | null;
  revoked: boolean;
  status: DecisionRoomStatus;
  client_contact_name: string | null;
  client_contact_email: string | null;
  client_contact_company: string | null;
  last_invitation_sent_at: string | null;
  viewed_at: string | null;
  viewed_count: number;
  closed_at: string | null;
  created_at: string;
  updated_at: string;
  items: ShortlistItem[];
};

export type PublicExperienceRole = {
  title: string;
  company: string;
  start_date: string | null;
  end_date: string | null;
  duration_years: number | null;
  responsibilities: string[];
  achievements: string[];
  tools_or_systems: string[];
};

export type PublicDimensionScore = {
  dimension: string;
  score: number | null;
  max_score: number | null;
  status: string | null;
  evidence_level: string | null;
  rationale: string | null;
};

export type PublicShortlistCandidate = {
  item_id: number;
  candidate_id: number;
  full_name: string;
  current_position: string | null;
  current_company: string | null;
  country: string | null;
  linkedin_url: string | null;
  total_years_experience: number | null;
  inferred_seniority: string | null;
  headline: string;
  professional_summary: string;
  strengths: string[];
  transferable_skills: string[];
  career_trajectory: {
    tenure_stability?: string;
    progression?: string;
    current_phase?: string;
    narrative?: string;
  };
  education: string[];
  certifications: string[];
  languages: string[];
  areas_to_validate: string[];
  why_fits: string[];
  risks_or_validations: string[];
  experience: PublicExperienceRole[];
  industries: string[];
  achievements: string[];
  tools: string[];
  dimension_scores: PublicDimensionScore[];
  interview_questions: string[];
  final_verdict: string | null;
  has_report: boolean;
  can_download_report: boolean;
  consultant_summary: string | null;
  recommendation: ConsultantRecommendation | null;
  evidence_level: EvidenceLevel | null;
  availability: string | null;
  salary_expectation: string | null;
  is_pinned: boolean;
  order_index: number;
  score: number | null;
  score_category: string | null;
  client_status: ClientFeedbackStatus | null;
  client_comment: string | null;
  rating: number | null;
};

export type PublicShortlistView = {
  title: string;
  message_to_client: string;
  intro_message: string | null;
  expires_at: string | null;
  revoked: boolean;
  status: DecisionRoomStatus;
  show_scores: boolean;
  show_availability: boolean;
  show_salary: boolean;
  show_risks: boolean;
  show_comparison: boolean;
  allow_comments: boolean;
  allow_rating: boolean;
  allow_report_download: boolean;
  mandate: {
    client_name: string;
    target_role: string;
    industry: string | null;
    city: string | null;
    country: string | null;
  };
  candidates: PublicShortlistCandidate[];
  created_at: string;
};

// Cuando el room requiere código y la sesión aún no se validó, el backend
// devuelve esta vista mínima en vez de los candidatos.
export type PublicShortlistGate = {
  requires_code: true;
  title: string;
  mandate: { client_name: string; target_role: string };
  expires_at: string | null;
  client_contact_email_hint: string | null;
};

export type PublicShortlistResponse = PublicShortlistView | PublicShortlistGate;

export function isGate(payload: PublicShortlistResponse): payload is PublicShortlistGate {
  return (payload as PublicShortlistGate).requires_code === true;
}

export const CLIENT_DECISION_LABELS: Record<ClientFeedbackStatus, string> = {
  interested: "Me interesa",
  not_interested: "No me sirve",
  want_interview: "Quiero entrevistar",
  favorite: "Favorito",
  interview_requested: "Solicitar entrevista",
  more_info_requested: "Pedir más información",
  keep_in_review: "Mantener en revisión",
  rejected: "Descartar",
};

export const RECOMMENDATION_LABELS: Record<ConsultantRecommendation, string> = {
  highly_recommended: "Altamente recomendado",
  recommended: "Recomendado",
  recommended_with_validations: "Recomendado con validaciones",
  reserve: "Reserva",
  not_recommended: "No recomendado",
};

export const EVIDENCE_LEVEL_LABELS: Record<EvidenceLevel, string> = {
  high: "Evidencia alta",
  medium: "Evidencia media",
  low: "Evidencia baja",
};
