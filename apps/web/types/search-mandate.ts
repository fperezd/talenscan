export type MandateStatus =
  | "Borrador"
  | "Activo"
  | "Perfil objetivo generado"
  | "En evaluación de candidatos"
  | "Con shortlist"
  | "Cerrado"
  | "Archivado";

export type SearchMandate = {
  id: number;
  client_name: string;
  search_title: string;
  target_role: string;
  industry: string | null;
  country: string | null;
  city: string | null;
  work_mode: string | null;
  seniority_level: string | null;
  reports_to: string | null;
  business_context: string | null;
  role_objective: string | null;
  key_challenges: string | null;
  main_responsibilities: string[];
  expected_results: string[];
  must_have_requirements: string[];
  nice_to_have_requirements: string[];
  target_companies: string[];
  target_industries: string[];
  equivalent_roles: string[];
  compensation_context: string | null;
  urgency: string | null;
  target_hire_date: string | null;
  comments: string | null;
  status: MandateStatus;
  created_at: string;
  updated_at: string;
};

export type SearchMandateInput = Omit<SearchMandate, "id" | "created_at" | "updated_at">;
