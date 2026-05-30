// Tipos de la Bóveda de Talento. Espejo de app/schemas/talent_profile.py.

export type TalentStatus = "active" | "passive" | "placed" | "archived";
export type AvailabilityStatus =
  | "unknown"
  | "available"
  | "open_to_offers"
  | "not_available"
  | "placed";
export type NoteType =
  | "general"
  | "call"
  | "meeting"
  | "client_feedback"
  | "interview"
  | "alert";

export type TalentTag = { id: number; name: string; category: string | null };

export type TalentNote = {
  id: number;
  talent_profile_id: number;
  search_mandate_id: number | null;
  note_type: NoteType;
  note_text: string;
  created_by: string | null;
  created_at: string;
  updated_at: string;
};

export type TalentDocument = {
  id: number;
  talent_profile_id: number;
  candidate_document_id: number | null;
  document_type: string;
  file_name: string | null;
  file_url: string | null;
  source: string | null;
  uploaded_at: string | null;
  created_at: string;
};

export type TalentEvaluation = {
  id: number;
  talent_profile_id: number;
  candidate_evaluation_id: number | null;
  search_mandate_id: number | null;
  position_spec_id: number | null;
  client_name: string | null;
  target_role: string | null;
  total_score: number | null;
  score_category: string | null;
  recommendation: string | null;
  critical_gaps: unknown[];
  strengths: unknown[];
  weaknesses: unknown[];
  risks: unknown[];
  result_stage: string | null;
  created_at: string;
};

export type TalentProcessHistory = {
  id: number;
  talent_profile_id: number;
  search_mandate_id: number | null;
  client_name: string | null;
  target_role: string | null;
  pipeline_stage: string | null;
  final_result: string | null;
  discard_reason: string | null;
  client_feedback: string | null;
  consultant_notes: string | null;
  started_at: string | null;
  ended_at: string | null;
  updated_at: string;
};

export type TalentProfileVersion = {
  id: number;
  talent_profile_id: number;
  version_number: number;
  change_reason: string | null;
  source: string | null;
  created_by: string | null;
  created_at: string;
};

export type TalentSummary = {
  id: number;
  full_name: string;
  current_position: string | null;
  current_company: string | null;
  inferred_seniority: string | null;
  country: string | null;
  city: string | null;
  industries: string[];
  skills: string[];
  status: TalentStatus;
  availability_status: AvailabilityStatus;
  do_not_contact: boolean;
  last_score: number | null;
  last_evaluated_at: string | null;
  tags: TalentTag[];
  evaluations_count: number;
  updated_at: string;
};

export type TalentProfile = {
  id: number;
  origin_candidate_id: number | null;
  full_name: string;
  primary_email: string | null;
  primary_phone: string | null;
  linkedin_url: string | null;
  current_position: string | null;
  current_company: string | null;
  country: string | null;
  city: string | null;
  general_location: string | null;
  inferred_seniority: string | null;
  summary: string | null;
  industries: string[];
  skills: string[];
  tools: string[];
  languages: string[];
  certifications: string[];
  education: unknown[];
  career_history: unknown[];
  achievements: unknown[];
  status: TalentStatus;
  availability_status: AvailabilityStatus;
  expected_compensation: Record<string, unknown> | null;
  do_not_contact: boolean;
  last_contacted_at: string | null;
  last_evaluated_at: string | null;
  created_at: string;
  updated_at: string;
  tags: TalentTag[];
  documents: TalentDocument[];
  evaluations: TalentEvaluation[];
  process_history: TalentProcessHistory[];
  notes: TalentNote[];
  versions: TalentProfileVersion[];
};

export type TalentVaultMetrics = {
  total: number;
  evaluated: number;
  in_reserve: number;
  available: number;
  average_score: number | null;
  updated_last_30_days: number;
};

export type TalentListResponse = {
  items: TalentSummary[];
  total: number;
  page: number;
  page_size: number;
  metrics: TalentVaultMetrics;
};

export const TALENT_STATUS_LABELS: Record<TalentStatus, string> = {
  active: "Activo",
  passive: "En reserva",
  placed: "Colocado",
  archived: "Archivado",
};

export const AVAILABILITY_LABELS: Record<AvailabilityStatus, string> = {
  unknown: "Sin definir",
  available: "Disponible",
  open_to_offers: "Abierto a ofertas",
  not_available: "No disponible",
  placed: "Colocado",
};

export const NOTE_TYPE_LABELS: Record<NoteType, string> = {
  general: "General",
  call: "Llamada",
  meeting: "Reunión",
  client_feedback: "Feedback cliente",
  interview: "Entrevista",
  alert: "Alerta",
};
