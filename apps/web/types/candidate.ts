export type Candidate = {
  id: number;
  full_name: string;
  email: string | null;
  phone: string | null;
  linkedin_url: string | null;
  current_position: string | null;
  current_company: string | null;
  country: string | null;
  created_at: string;
  updated_at: string;
};

export type CandidateInput = Omit<Candidate, "id" | "created_at" | "updated_at">;

export type CandidateDocument = {
  id: number;
  candidate_id: number;
  file_name: string;
  file_type: string;
  file_size: number;
  file_url: string | null;
  raw_text: string | null;
  text_extraction_status: string;
  uploaded_at: string;
};

export type CandidateProfile = {
  id: number;
  candidate_id: number;
  candidate_document_id: number | null;
  current_position: string | null;
  current_company: string | null;
  total_years_experience: number | null;
  industries: string[];
  roles: Array<Record<string, unknown>>;
  education: string[];
  certifications: string[];
  tools: string[];
  languages: string[];
  achievements: string[];
  inferred_seniority: string | null;
  missing_information: string[];
  evidence_snippets: string[];
  parsed_json: Record<string, unknown>;
  created_at: string;
};
