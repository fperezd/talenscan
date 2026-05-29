export const PIPELINE_STAGES = [
  "received",
  "analyzing",
  "evaluated",
  "preselected",
  "interview",
  "reserve",
  "discarded",
  "present_to_client",
] as const;

export type PipelineStage = (typeof PIPELINE_STAGES)[number];

export const PIPELINE_STAGE_LABELS: Record<PipelineStage, string> = {
  received: "CVs recibidos",
  analyzing: "En análisis",
  evaluated: "Evaluados",
  preselected: "Preseleccionados",
  interview: "Entrevista",
  reserve: "En reserva",
  discarded: "Descartados",
  present_to_client: "Presentar al cliente",
};

export const PIPELINE_STAGE_TONES: Record<PipelineStage, string> = {
  received: "border-slate-200 bg-slate-50",
  analyzing: "border-blue-100 bg-blue-50/40",
  evaluated: "border-violet-100 bg-violet-50/40",
  preselected: "border-emerald-100 bg-emerald-50/40",
  interview: "border-amber-100 bg-amber-50/40",
  reserve: "border-zinc-200 bg-zinc-50",
  discarded: "border-rose-100 bg-rose-50/40",
  present_to_client: "border-brand-blue/30 bg-brand-blue/5",
};

export type CandidatePipelineItem = {
  id: number;
  mandate_id: number;
  candidate_id: number;
  evaluation_id: number | null;
  stage: PipelineStage;
  stage_order: number;
  is_priority: boolean;
  is_shortlisted: boolean;
  consultant_notes: string;
  discard_reason: string;
  tags: string[];
  last_moved_at: string;
  created_at: string;
  updated_at: string;
};

export type PipelineReorderItem = {
  id: number;
  stage: PipelineStage;
  stage_order: number;
};
