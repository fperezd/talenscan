"use client";

import {
  AlertTriangle,
  Award,
  CheckCircle2,
  ClipboardCheck,
  Compass,
  DoorOpen,
  Download,
  Eye,
  FileText,
  HelpCircle,
  Lightbulb,
  Loader2,
  Quote,
  Rocket,
  ShieldAlert,
  Sparkles,
  Target,
  TrendingUp,
  Trash2,
  Users,
  X,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { AddToRoomModal } from "@/components/decision-room/add-to-room-modal";
import { API_BASE_URL, apiFetch } from "@/lib/api";
import { useDynamicId } from "@/lib/use-dynamic-id";
import { cn } from "@/lib/utils";
import type { CandidateEvaluation } from "@/types/evaluation";
import type { PositionSpec } from "@/types/position-spec";

type EvaluationDetailClientProps = {
  evaluationId?: string;
};

type DimensionScore = {
  dimension?: string;
  score?: number;
  max_score?: number;
  status?: string;
  evidence_level?: string;
  rationale?: string;
  supporting_evidence?: string[];
};

type StrengthDetailed = { title?: string; detail?: string; evidence?: string };
type GapDetailed = {
  requirement?: string;
  reason?: string;
  impact?: string;
  evidence?: string;
  mitigation?: string;
};
type OpportunityDetailed = { title?: string; detail?: string; evidence?: string };
type RiskDetailed = { risk?: string; validation?: string };
type InterviewQuestionDetailed = {
  question?: string;
  objective?: string;
  priority?: string;
};
type CareerTrajectory = {
  tenure_stability?: string;
  progression?: string;
  current_phase?: string;
  narrative?: string;
};
type CulturalSignal = { signal?: string; indicator?: string };

type AiAssessment = {
  talent_thesis?: string;
  differentiation?: string;
  strengths_detailed?: StrengthDetailed[];
  critical_gaps_detailed?: GapDetailed[];
  opportunities?: OpportunityDetailed[];
  transferable_skills?: string[];
  weaknesses?: string[];
  risks_detailed?: RiskDetailed[];
  red_flags?: string[];
  career_trajectory?: CareerTrajectory;
  cultural_fit_signals?: CulturalSignal[];
  interview_questions_detailed?: InterviewQuestionDetailed[];
  reference_check_focus?: string[];
  onboarding_considerations?: string[];
  compensation_signals?: string;
  supporting_evidence?: string[];
};

function getString(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}
function getNumber(value: unknown, fallback = 0): number {
  return typeof value === "number" ? value : fallback;
}
function getStringArray(value: unknown): string[] {
  return Array.isArray(value) ? (value as unknown[]).map((v) => String(v)) : [];
}
function cleanEvidenceSnippet(raw: string): string {
  let cleaned = raw.replace(/^#{1,6}\s+/gm, "").trim();
  cleaned = cleaned.replace(/^["'`]+|["'`]+$/g, "").trim();
  return cleaned;
}

function scoreTone(score: number): {
  ring: string;
  bg: string;
  text: string;
  badge: string;
  label: string;
} {
  if (score >= 85)
    return {
      ring: "ring-emerald-300",
      bg: "bg-emerald-50",
      text: "text-emerald-700",
      badge: "bg-emerald-100 text-emerald-700",
      label: "Muy alto calce",
    };
  if (score >= 70)
    return {
      ring: "ring-blue-300",
      bg: "bg-blue-50",
      text: "text-blue-700",
      badge: "bg-blue-100 text-blue-700",
      label: "Buen calce",
    };
  if (score >= 55)
    return {
      ring: "ring-amber-300",
      bg: "bg-amber-50",
      text: "text-amber-700",
      badge: "bg-amber-100 text-amber-700",
      label: "Calce parcial",
    };
  if (score >= 40)
    return {
      ring: "ring-zinc-300",
      bg: "bg-zinc-50",
      text: "text-brand-grayMid",
      badge: "bg-zinc-200 text-brand-grayMid",
      label: "Bajo calce",
    };
  return {
    ring: "ring-rose-300",
    bg: "bg-rose-50",
    text: "text-rose-700",
    badge: "bg-rose-100 text-rose-700",
    label: "No recomendado",
  };
}

function evidenceTone(level: string | undefined): string {
  const lower = (level || "").toLowerCase();
  if (lower.includes("alta")) return "bg-emerald-100 text-emerald-700";
  if (lower.includes("media")) return "bg-amber-100 text-amber-700";
  if (lower.includes("baja")) return "bg-zinc-200 text-brand-grayMid";
  return "bg-slate-100 text-brand-grayMid";
}

function priorityTone(priority: string | undefined): string {
  const lower = (priority || "").toLowerCase();
  if (lower.includes("alta")) return "bg-rose-100 text-rose-700";
  if (lower.includes("media")) return "bg-amber-100 text-amber-700";
  return "bg-slate-100 text-brand-grayMid";
}

function indicatorTone(indicator: string | undefined): string {
  const lower = (indicator || "").toLowerCase();
  if (lower.includes("positive")) return "bg-emerald-100 text-emerald-700 border-emerald-200";
  if (lower.includes("risk")) return "bg-rose-100 text-rose-700 border-rose-200";
  return "bg-slate-100 text-brand-grayMid border-slate-200";
}

export function EvaluationDetailClient({ evaluationId: propId }: EvaluationDetailClientProps = {}) {
  const pathId = useDynamicId("evaluaciones");
  const evaluationId = pathId && pathId !== "demo" ? pathId : propId || pathId;

  const [item, setItem] = useState<CandidateEvaluation | null>(null);
  const [mandateId, setMandateId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<"word" | "pdf" | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [addToRoomOpen, setAddToRoomOpen] = useState(false);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        let detail: CandidateEvaluation | null = null;
        if (evaluationId === "demo") {
          const list = await apiFetch<CandidateEvaluation[]>("/api/evaluaciones");
          detail = list[0] || null;
        } else {
          detail = await apiFetch<CandidateEvaluation>(`/api/evaluaciones/${evaluationId}`);
        }
        setItem(detail);
        // Resolver mandate_id desde el position_spec para habilitar "Agregar a Decision Room"
        if (detail && detail.position_spec_id) {
          try {
            const spec = await apiFetch<PositionSpec>(
              `/api/perfiles-objetivo/${detail.position_spec_id}`
            );
            setMandateId(spec.search_mandate_id ?? null);
          } catch {
            setMandateId(null);
          }
        }
      } catch (requestError) {
        console.error(requestError);
        setError("No fue posible cargar esta evaluación.");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [evaluationId]);

  const ai: AiAssessment = useMemo(() => {
    if (!item || !item.evaluation_json) return {};
    const raw = (item.evaluation_json as Record<string, unknown>).ai_assessment;
    return (raw && typeof raw === "object" ? raw : {}) as AiAssessment;
  }, [item]);

  const dimensions = useMemo<DimensionScore[]>(() => {
    if (!item) return [];
    return Array.isArray(item.dimension_scores) ? (item.dimension_scores as DimensionScore[]) : [];
  }, [item]);

  const criticalGaps = useMemo<GapDetailed[]>(() => {
    if (ai.critical_gaps_detailed && ai.critical_gaps_detailed.length > 0) {
      return ai.critical_gaps_detailed;
    }
    if (!item) return [];
    return Array.isArray(item.critical_gaps) ? (item.critical_gaps as GapDetailed[]) : [];
  }, [item, ai]);

  const strengths = useMemo<StrengthDetailed[]>(() => {
    if (ai.strengths_detailed && ai.strengths_detailed.length > 0) {
      return ai.strengths_detailed;
    }
    return getStringArray(item?.strengths).map((title) => ({ title }));
  }, [item, ai]);

  const opportunities = ai.opportunities || [];
  const transferableSkills = ai.transferable_skills || [];
  const weaknesses = ai.weaknesses || getStringArray(item?.weaknesses);
  const risks = useMemo<RiskDetailed[]>(() => {
    if (ai.risks_detailed && ai.risks_detailed.length > 0) return ai.risks_detailed;
    return getStringArray(item?.risks).map((risk) => ({ risk }));
  }, [item, ai]);
  const redFlags = ai.red_flags || [];
  const trajectory = ai.career_trajectory || {};
  const culturalSignals = ai.cultural_fit_signals || [];
  const interviewQuestions = useMemo<InterviewQuestionDetailed[]>(() => {
    if (ai.interview_questions_detailed && ai.interview_questions_detailed.length > 0) {
      return ai.interview_questions_detailed;
    }
    return getStringArray(item?.interview_questions).map((question) => ({ question }));
  }, [item, ai]);
  const referenceCheck = ai.reference_check_focus || [];
  const onboarding = ai.onboarding_considerations || [];
  const compensationSignals = ai.compensation_signals || "";
  const supportingEvidence = ai.supporting_evidence?.length
    ? ai.supporting_evidence
    : getStringArray(item?.supporting_evidence);

  async function openPreview() {
    if (!item) return;
    setPreviewLoading(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/evaluaciones/${item.id}/reportes/pdf`,
        { method: "POST" }
      );
      if (!response.ok) throw new Error("Preview failed");
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      setPreviewUrl(url);
    } catch (previewError) {
      console.error(previewError);
      setError("No fue posible generar la vista previa.");
    } finally {
      setPreviewLoading(false);
    }
  }

  function closePreview() {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
  }

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  async function handleDownload(format: "word" | "pdf") {
    if (!item) return;
    setDownloading(format);
    try {
      const response = await fetch(`${API_BASE_URL}/api/evaluaciones/${item.id}/reportes/${format}`, {
        method: "POST",
      });
      if (!response.ok) throw new Error("Download failed");
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      const contentDisposition = response.headers.get("Content-Disposition") || "";
      const match = contentDisposition.match(/filename="([^"]+)"/);
      link.download = match ? match[1] : `evaluacion-${item.id}.${format === "word" ? "docx" : "pdf"}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (downloadError) {
      console.error(downloadError);
      setError(`No fue posible descargar el informe ${format === "word" ? "Word" : "PDF"}.`);
    } finally {
      setDownloading(null);
    }
  }

  async function handleDelete() {
    if (!item) return;
    const confirmed = window.confirm(
      "¿Eliminar esta evaluación? Esto también la quita del pipeline. Esta acción no se puede deshacer."
    );
    if (!confirmed) return;
    setDeleting(true);
    try {
      await apiFetch(`/api/evaluaciones/${item.id}`, { method: "DELETE" });
      window.location.href = "/evaluaciones";
    } catch (deleteError) {
      console.error(deleteError);
      setError("No fue posible eliminar la evaluación.");
      setDeleting(false);
    }
  }

  if (loading) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center text-sm text-brand-grayMid">
        Cargando evaluación...
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
        {error}
      </div>
    );
  }

  if (!item) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center">
        <p className="text-sm font-semibold text-brand-black">No hay evaluación disponible</p>
        <p className="mt-1 text-xs text-brand-grayMid">
          Genera una Evaluación 360 desde un mandato y vuelve aquí para ver el detalle.
        </p>
        <Link
          href="/mandatos"
          className="mt-4 inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-3.5 py-2 text-sm font-semibold text-white transition hover:bg-brand-blueDark"
        >
          Ir a mandatos
        </Link>
      </div>
    );
  }

  const tone = scoreTone(item.total_score);
  const isLinkedInOnly =
    supportingEvidence.length > 0 &&
    supportingEvidence.every((s) => s.toLowerCase().includes("linkedin"));
  const hasMinimalData = strengths.length === 0 && interviewQuestions.length === 0;

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-start justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
        <div className="flex items-start gap-5">
          <div
            className={cn(
              "flex h-24 w-24 shrink-0 items-center justify-center rounded-2xl ring-4",
              tone.ring,
              tone.bg
            )}
          >
            <div className="text-center">
              <p className={cn("text-3xl font-bold leading-none", tone.text)}>{item.total_score}</p>
              <p className="mt-0.5 text-[10px] uppercase tracking-wide text-brand-grayMid">/ 100</p>
            </div>
          </div>
          <div className="min-w-0">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-blue">
              Evaluación 360 TalentScan
            </p>
            <h2 className="mt-1 text-2xl font-semibold tracking-tight text-brand-black">
              {item.score_category}
            </h2>
            <p className="mt-2 max-w-lg text-sm text-brand-grayMid">{item.recommendation}</p>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <span className={cn("rounded-full px-2.5 py-0.5 text-[11px] font-medium", tone.badge)}>
                {tone.label}
              </span>
              {criticalGaps.length > 0 ? (
                <span className="inline-flex items-center gap-1 rounded-full bg-rose-100 px-2.5 py-0.5 text-[11px] font-medium text-rose-700">
                  <AlertTriangle className="h-3 w-3" />
                  {criticalGaps.length} brecha{criticalGaps.length === 1 ? "" : "s"} crítica{criticalGaps.length === 1 ? "" : "s"}
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2.5 py-0.5 text-[11px] font-medium text-emerald-700">
                  <CheckCircle2 className="h-3 w-3" />
                  Sin brechas críticas
                </span>
              )}
              {opportunities.length > 0 ? (
                <span className="inline-flex items-center gap-1 rounded-full bg-indigo-100 px-2.5 py-0.5 text-[11px] font-medium text-indigo-700">
                  <Lightbulb className="h-3 w-3" />
                  {opportunities.length} oportunidad{opportunities.length === 1 ? "" : "es"} transferible{opportunities.length === 1 ? "" : "s"}
                </span>
              ) : null}
            </div>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={handleDelete}
            disabled={deleting || downloading !== null || previewLoading}
            className="inline-flex items-center gap-1.5 rounded-lg border border-rose-200 bg-white px-3.5 py-2 text-sm font-medium text-rose-700 transition hover:bg-rose-50 disabled:opacity-50"
          >
            <Trash2 className="h-3.5 w-3.5" />
            {deleting ? "Eliminando..." : "Eliminar"}
          </button>
          {mandateId !== null ? (
            <button
              type="button"
              onClick={() => setAddToRoomOpen(true)}
              disabled={downloading !== null || deleting || previewLoading}
              className="inline-flex items-center gap-1.5 rounded-lg border border-brand-blue/40 bg-brand-blueSoft px-3.5 py-2 text-sm font-semibold text-brand-blue transition hover:bg-brand-blueSoft/80 disabled:opacity-50"
            >
              <DoorOpen className="h-3.5 w-3.5" />
              Agregar a Decision Room
            </button>
          ) : null}
          <button
            type="button"
            onClick={openPreview}
            disabled={previewLoading || downloading !== null || deleting}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-sm font-medium text-brand-grayMid transition hover:border-brand-blue/40 hover:text-brand-black disabled:opacity-50"
          >
            {previewLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Eye className="h-3.5 w-3.5" />}
            {previewLoading ? "Generando..." : "Vista previa PDF"}
          </button>
          <button
            type="button"
            onClick={() => handleDownload("word")}
            disabled={downloading !== null || deleting || previewLoading}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-sm font-medium text-brand-grayMid transition hover:border-brand-blue/40 hover:text-brand-black disabled:opacity-50"
          >
            <Download className="h-3.5 w-3.5" />
            {downloading === "word" ? "Descargando..." : "Descargar Word"}
          </button>
          <button
            type="button"
            onClick={() => handleDownload("pdf")}
            disabled={downloading !== null || deleting || previewLoading}
            className="inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-3.5 py-2 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-blueDark disabled:opacity-50"
          >
            <FileText className="h-3.5 w-3.5" />
            {downloading === "pdf" ? "Descargando..." : "Descargar PDF"}
          </button>
        </div>
      </header>

      {isLinkedInOnly && hasMinimalData ? (
        <article className="rounded-2xl border border-amber-200 bg-amber-50/40 p-5 shadow-soft">
          <div className="flex items-start gap-3">
            <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-700" />
            <div>
              <p className="text-sm font-semibold text-amber-800">
                Evaluación basada solo en URL de LinkedIn sin perfil estructurado
              </p>
              <p className="mt-1 text-xs text-amber-800">
                Verifica que el candidato tenga su perfil de LinkedIn enriquecido o un CV cargado para
                obtener una evaluación con evidencia completa.
              </p>
            </div>
          </div>
        </article>
      ) : null}

      {/* Talent thesis — la apuesta */}
      {ai.talent_thesis ? (
        <article className="rounded-2xl border border-brand-blue/30 bg-gradient-to-br from-brand-blueSoft/50 to-white p-6 shadow-soft">
          <div className="flex items-center gap-2">
            <Target className="h-4 w-4 text-brand-blue" />
            <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-blue">
              Tesis de talento
            </p>
          </div>
          <p className="mt-2 text-base font-medium leading-relaxed text-brand-black">
            {ai.talent_thesis}
          </p>
          {ai.differentiation ? (
            <div className="mt-4 rounded-xl border border-slate-200 bg-white/70 p-3">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-grayMid">
                Diferenciador
              </p>
              <p className="mt-1 text-sm text-brand-black">{ai.differentiation}</p>
            </div>
          ) : null}
        </article>
      ) : null}

      {/* Resumen ejecutivo + Veredicto */}
      <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
        <div className="flex items-center gap-2">
          <Compass className="h-4 w-4 text-brand-blue" />
          <h3 className="text-base font-semibold text-brand-black">Resumen ejecutivo</h3>
        </div>
        <p className="mt-2 text-sm leading-relaxed text-brand-grayMid">
          {item.executive_summary || "Sin resumen ejecutivo disponible."}
        </p>
        {item.final_verdict ? (
          <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-3">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-grayMid">
              Veredicto final
            </p>
            <p className="mt-1 text-sm font-medium text-brand-black">{item.final_verdict}</p>
          </div>
        ) : null}
      </article>

      {/* Fortalezas / Brechas / Oportunidades — 3 columnas */}
      <div className="grid gap-5 lg:grid-cols-3">
        {strengths.length > 0 ? (
          <article className="rounded-2xl border border-emerald-200 bg-emerald-50/30 p-5 shadow-soft">
            <div className="flex items-center gap-2 text-emerald-700">
              <CheckCircle2 className="h-4 w-4" />
              <h3 className="text-sm font-semibold">Fortalezas calzadas</h3>
              <span className="ml-auto rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-medium text-emerald-700">
                {strengths.length}
              </span>
            </div>
            <ul className="mt-3 space-y-3">
              {strengths.map((strength, index) => (
                <li key={index} className="rounded-lg border border-emerald-100 bg-white p-3">
                  <p className="text-sm font-semibold text-brand-black">
                    {getString(strength.title, "Fortaleza")}
                  </p>
                  {strength.detail ? (
                    <p className="mt-1 text-xs text-brand-grayMid">{strength.detail}</p>
                  ) : null}
                  {strength.evidence ? (
                    <p className="mt-1 text-[11px] italic text-emerald-700">
                      Evidencia: {strength.evidence}
                    </p>
                  ) : null}
                </li>
              ))}
            </ul>
          </article>
        ) : null}

        {opportunities.length > 0 ? (
          <article className="rounded-2xl border border-indigo-200 bg-indigo-50/30 p-5 shadow-soft">
            <div className="flex items-center gap-2 text-indigo-700">
              <Lightbulb className="h-4 w-4" />
              <h3 className="text-sm font-semibold">Oportunidades transferibles</h3>
              <span className="ml-auto rounded-full bg-indigo-100 px-2 py-0.5 text-[10px] font-medium text-indigo-700">
                {opportunities.length}
              </span>
            </div>
            <p className="mt-1 text-[11px] text-indigo-700/80">
              Fortalezas que el cliente puede no estar valorando inicialmente.
            </p>
            <ul className="mt-3 space-y-3">
              {opportunities.map((opp, index) => (
                <li key={index} className="rounded-lg border border-indigo-100 bg-white p-3">
                  <p className="text-sm font-semibold text-brand-black">
                    {getString(opp.title, "Oportunidad")}
                  </p>
                  {opp.detail ? (
                    <p className="mt-1 text-xs text-brand-grayMid">{opp.detail}</p>
                  ) : null}
                  {opp.evidence ? (
                    <p className="mt-1 text-[11px] italic text-indigo-700">
                      Evidencia: {opp.evidence}
                    </p>
                  ) : null}
                </li>
              ))}
            </ul>
            {transferableSkills.length > 0 ? (
              <div className="mt-3 border-t border-indigo-100 pt-3">
                <p className="text-[11px] font-semibold uppercase tracking-wider text-indigo-700">
                  Habilidades transferibles
                </p>
                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  {transferableSkills.map((skill) => (
                    <span
                      key={skill}
                      className="rounded-full bg-white px-2 py-0.5 text-[11px] font-medium text-indigo-700 ring-1 ring-indigo-200"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            ) : null}
          </article>
        ) : null}

        {criticalGaps.length > 0 ? (
          <article className="rounded-2xl border border-rose-200 bg-rose-50/30 p-5 shadow-soft">
            <div className="flex items-center gap-2 text-rose-700">
              <AlertTriangle className="h-4 w-4" />
              <h3 className="text-sm font-semibold">Brechas críticas</h3>
              <span className="ml-auto rounded-full bg-rose-100 px-2 py-0.5 text-[10px] font-medium text-rose-700">
                {criticalGaps.length}
              </span>
            </div>
            <ul className="mt-3 space-y-3">
              {criticalGaps.map((gap, index) => (
                <li key={index} className="rounded-lg border border-rose-100 bg-white p-3">
                  <p className="text-sm font-semibold text-brand-black">
                    {getString(gap.requirement, getString(gap.reason, "Brecha"))}
                  </p>
                  {gap.impact ? (
                    <p className="mt-1 text-xs text-rose-700">Impacto: {gap.impact}</p>
                  ) : null}
                  {gap.mitigation ? (
                    <p className="mt-1 text-xs text-brand-grayMid">
                      <span className="font-semibold text-brand-black">Mitigación: </span>
                      {gap.mitigation}
                    </p>
                  ) : null}
                  {gap.evidence ? (
                    <p className="mt-1 text-[11px] italic text-brand-grayMid">{gap.evidence}</p>
                  ) : null}
                </li>
              ))}
            </ul>
          </article>
        ) : null}
      </div>

      {/* Trayectoria de carrera */}
      {(trajectory.narrative || trajectory.progression || trajectory.tenure_stability) ? (
        <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
          <div className="flex items-center gap-2">
            <Rocket className="h-4 w-4 text-brand-blue" />
            <h3 className="text-base font-semibold text-brand-black">Trayectoria de carrera</h3>
          </div>
          <div className="mt-3 grid gap-3 md:grid-cols-3">
            {trajectory.tenure_stability ? (
              <InfoTile
                label="Estabilidad"
                value={trajectory.tenure_stability}
              />
            ) : null}
            {trajectory.current_phase ? (
              <InfoTile label="Fase actual" value={trajectory.current_phase} />
            ) : null}
            {trajectory.progression ? (
              <InfoTile label="Progresión" value={trajectory.progression} />
            ) : null}
          </div>
          {trajectory.narrative ? (
            <p className="mt-4 text-sm leading-relaxed text-brand-grayMid">{trajectory.narrative}</p>
          ) : null}
        </article>
      ) : null}

      {/* Score por dimensión */}
      {dimensions.length > 0 ? (
        <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-brand-blue" />
            <h3 className="text-base font-semibold text-brand-black">Score por dimensión</h3>
          </div>
          <div className="mt-4 overflow-hidden rounded-xl border border-slate-200">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-left text-[11px] font-semibold uppercase tracking-wider text-brand-grayMid">
                <tr>
                  <th className="px-3 py-2.5">Dimensión</th>
                  <th className="px-3 py-2.5 text-center">Score</th>
                  <th className="px-3 py-2.5">Evidencia</th>
                  <th className="px-3 py-2.5">Justificación</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {dimensions.map((dim, index) => {
                  const score = getNumber(dim.score);
                  const max = getNumber(dim.max_score, 10);
                  const ratio = max > 0 ? score / max : 0;
                  const barTone =
                    ratio >= 0.85
                      ? "bg-emerald-400"
                      : ratio >= 0.6
                        ? "bg-blue-400"
                        : ratio >= 0.4
                          ? "bg-amber-400"
                          : "bg-rose-400";
                  return (
                    <tr key={index} className="hover:bg-slate-50/60">
                      <td className="px-3 py-3 font-medium text-brand-black">
                        {getString(dim.dimension, `Dimensión ${index + 1}`)}
                      </td>
                      <td className="px-3 py-3 text-center">
                        <div className="inline-flex flex-col items-center">
                          <span className="text-sm font-semibold text-brand-black">
                            {score} / {max}
                          </span>
                          <div className="mt-1 h-1.5 w-20 overflow-hidden rounded-full bg-slate-200">
                            <div
                              className={cn("h-full rounded-full", barTone)}
                              style={{ width: `${Math.min(100, Math.round(ratio * 100))}%` }}
                            />
                          </div>
                        </div>
                      </td>
                      <td className="px-3 py-3">
                        <span
                          className={cn(
                            "rounded-full px-2 py-0.5 text-[11px] font-medium",
                            evidenceTone(dim.evidence_level)
                          )}
                        >
                          {getString(dim.evidence_level, "No evidenciado")}
                        </span>
                      </td>
                      <td className="px-3 py-3 text-xs text-brand-grayMid">
                        {getString(dim.rationale, "—")}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </article>
      ) : null}

      {/* Cultural fit + Debilidades + Riesgos + Red flags */}
      <div className="grid gap-5 lg:grid-cols-2">
        {culturalSignals.length > 0 ? (
          <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-brand-blue" />
              <h3 className="text-base font-semibold text-brand-black">Señales de cultural fit</h3>
            </div>
            <ul className="mt-3 space-y-2">
              {culturalSignals.map((signal, index) => (
                <li
                  key={index}
                  className={cn(
                    "flex items-start gap-2 rounded-xl border p-3 text-sm",
                    indicatorTone(signal.indicator)
                  )}
                >
                  <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-current" />
                  <span className="flex-1 text-brand-black">{getString(signal.signal)}</span>
                  <span className="shrink-0 rounded-full bg-white/70 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide">
                    {getString(signal.indicator, "Neutral")}
                  </span>
                </li>
              ))}
            </ul>
          </article>
        ) : null}

        {weaknesses.length > 0 ? (
          <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
            <div className="flex items-center gap-2">
              <Award className="h-4 w-4 text-brand-grayMid" />
              <h3 className="text-base font-semibold text-brand-black">Debilidades manejables</h3>
            </div>
            <ul className="mt-3 space-y-2 text-sm text-brand-black">
              {weaknesses.map((weakness, index) => (
                <li key={index} className="flex items-start gap-2">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-slate-400" />
                  <span>{weakness}</span>
                </li>
              ))}
            </ul>
          </article>
        ) : null}

        {risks.length > 0 ? (
          <article className="rounded-2xl border border-amber-200 bg-amber-50/30 p-6 shadow-soft">
            <div className="flex items-center gap-2 text-amber-700">
              <ShieldAlert className="h-4 w-4" />
              <h3 className="text-base font-semibold">Riesgos a validar</h3>
            </div>
            <ul className="mt-3 space-y-2">
              {risks.map((risk, index) => (
                <li
                  key={index}
                  className="rounded-lg border border-amber-100 bg-white p-3 text-sm text-brand-black"
                >
                  <p>{getString(risk.risk)}</p>
                  {risk.validation ? (
                    <p className="mt-1 text-xs text-amber-700">
                      <span className="font-semibold">Cómo validar: </span>
                      {risk.validation}
                    </p>
                  ) : null}
                </li>
              ))}
            </ul>
          </article>
        ) : null}

        {redFlags.length > 0 ? (
          <article className="rounded-2xl border border-rose-200 bg-rose-50/30 p-6 shadow-soft">
            <div className="flex items-center gap-2 text-rose-700">
              <AlertTriangle className="h-4 w-4" />
              <h3 className="text-base font-semibold">Red flags</h3>
            </div>
            <ul className="mt-3 space-y-2 text-sm text-brand-black">
              {redFlags.map((flag, index) => (
                <li key={index} className="flex items-start gap-2">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-rose-500" />
                  <span>{flag}</span>
                </li>
              ))}
            </ul>
          </article>
        ) : null}
      </div>

      {/* Preguntas para entrevista */}
      {interviewQuestions.length > 0 ? (
        <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
          <div className="flex items-center gap-2">
            <HelpCircle className="h-4 w-4 text-brand-blue" />
            <h3 className="text-base font-semibold text-brand-black">
              Preguntas sugeridas para entrevista
            </h3>
            <span className="ml-auto rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-brand-grayMid">
              {interviewQuestions.length}
            </span>
          </div>
          <ol className="mt-3 space-y-3">
            {interviewQuestions.map((q, index) => (
              <li
                key={index}
                className="flex items-start gap-3 rounded-xl border border-slate-100 bg-slate-50/40 p-3"
              >
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand-blueSoft text-xs font-semibold text-brand-blue">
                  {index + 1}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm text-brand-black">{getString(q.question)}</p>
                  <div className="mt-1.5 flex flex-wrap items-center gap-2">
                    {q.objective ? (
                      <span className="text-[11px] text-brand-grayMid">
                        <span className="font-semibold text-brand-black">Objetivo: </span>
                        {q.objective}
                      </span>
                    ) : null}
                    {q.priority ? (
                      <span
                        className={cn(
                          "rounded-full px-2 py-0.5 text-[10px] font-medium",
                          priorityTone(q.priority)
                        )}
                      >
                        Prioridad {q.priority}
                      </span>
                    ) : null}
                  </div>
                </div>
              </li>
            ))}
          </ol>
        </article>
      ) : null}

      {/* Reference check + Onboarding + Compensación */}
      <div className="grid gap-5 lg:grid-cols-3">
        {referenceCheck.length > 0 ? (
          <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
            <div className="flex items-center gap-2">
              <ClipboardCheck className="h-4 w-4 text-brand-blue" />
              <h3 className="text-sm font-semibold text-brand-black">Foco en referencias</h3>
            </div>
            <ul className="mt-3 space-y-2 text-sm text-brand-black">
              {referenceCheck.map((focus, index) => (
                <li key={index} className="flex items-start gap-2">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-blue" />
                  <span>{focus}</span>
                </li>
              ))}
            </ul>
          </article>
        ) : null}

        {onboarding.length > 0 ? (
          <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
            <div className="flex items-center gap-2">
              <Rocket className="h-4 w-4 text-brand-blue" />
              <h3 className="text-sm font-semibold text-brand-black">Consideraciones de onboarding</h3>
            </div>
            <ul className="mt-3 space-y-2 text-sm text-brand-black">
              {onboarding.map((item2, index) => (
                <li key={index} className="flex items-start gap-2">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-blue" />
                  <span>{item2}</span>
                </li>
              ))}
            </ul>
          </article>
        ) : null}

        {compensationSignals ? (
          <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-brand-blue" />
              <h3 className="text-sm font-semibold text-brand-black">Señales de compensación</h3>
            </div>
            <p className="mt-3 text-sm leading-relaxed text-brand-grayMid">
              {compensationSignals}
            </p>
          </article>
        ) : null}
      </div>

      {/* Evidencia utilizada */}
      {supportingEvidence.length > 0 ? (
        <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
          <div className="flex items-center gap-2">
            <Quote className="h-4 w-4 text-brand-blue" />
            <h3 className="text-base font-semibold text-brand-black">Evidencia citada del perfil</h3>
          </div>
          <ul className="mt-3 space-y-1.5 text-sm text-brand-grayMid">
            {supportingEvidence
              .map((raw) => cleanEvidenceSnippet(raw))
              .filter((cleaned) => cleaned.length > 0)
              .map((evidence, index) => (
                <li
                  key={index}
                  className="rounded-lg border border-slate-100 bg-slate-50/40 px-3 py-2 italic"
                >
                  &ldquo;{evidence}&rdquo;
                </li>
              ))}
          </ul>
        </article>
      ) : null}

      <footer className="rounded-2xl border border-slate-100 bg-slate-50/40 p-4 text-[11px] text-brand-grayMid">
        Informe generado por TalentScan a partir del perfil objetivo del cargo, el perfil del candidato y
        el modelo de evaluación configurado. La evaluación debe ser revisada por el consultor responsable
        antes de ser compartida con el cliente. Modelo: {item.model_version} · Prompt: {item.prompt_version}.
      </footer>

      {previewUrl ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
          <div className="flex h-[90vh] w-full max-w-5xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl">
            <header className="flex items-center justify-between border-b border-slate-200 px-5 py-3">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-brand-blue" />
                <h3 className="text-sm font-semibold text-brand-black">
                  Vista previa del informe PDF
                </h3>
                <span className="text-xs text-brand-grayMid">
                  · {item.score_category} · {item.total_score}/100
                </span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => handleDownload("pdf")}
                  disabled={downloading !== null}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-3 py-1.5 text-xs font-semibold text-white shadow-soft transition hover:bg-brand-blueDark disabled:opacity-50"
                >
                  <Download className="h-3 w-3" />
                  {downloading === "pdf" ? "Descargando..." : "Descargar"}
                </button>
                <button
                  type="button"
                  onClick={closePreview}
                  className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 bg-white text-brand-grayMid transition hover:border-rose-300 hover:text-rose-700"
                  aria-label="Cerrar vista previa"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </header>
            <iframe
              src={previewUrl}
              title="Vista previa PDF"
              className="h-full w-full flex-1 border-0"
            />
          </div>
        </div>
      ) : null}

      {addToRoomOpen && mandateId !== null ? (
        <AddToRoomModal
          open
          mandateId={mandateId}
          evaluationIds={[item.id]}
          selectionLabel={`Evaluación #${item.id} · score ${item.total_score}/100`}
          onClose={() => setAddToRoomOpen(false)}
          onSuccess={(room) => {
            window.alert(
              `Decision Room actualizado. Compártelo en: ${window.location.origin}/shortlist-cliente/${room.public_token}`
            );
          }}
        />
      ) : null}
    </div>
  );
}

function InfoTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50/40 p-3">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-brand-grayMid">
        {label}
      </p>
      <p className="mt-1 text-sm font-semibold text-brand-black">{value}</p>
    </div>
  );
}
