"use client";

import {
  DndContext,
  DragOverlay,
  PointerSensor,
  closestCorners,
  useDroppable,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import {
  AlertCircle,
  Award,
  Briefcase,
  Calendar,
  CheckCircle2,
  ChevronDown,
  Clock,
  FileText,
  GraduationCap,
  GripVertical,
  Heart,
  HelpCircle,
  Info,
  Languages,
  Linkedin,
  Loader2,
  Lock,
  MapPin,
  MessageSquare,
  Minus,
  Pin,
  Quote,
  Send,
  ShieldCheck,
  Sparkles,
  Star,
  ThumbsDown,
  TrendingUp,
  Trophy,
  Wallet,
  Wrench,
  X,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { API_BASE_URL } from "@/lib/api";
import { cn } from "@/lib/utils";
import {
  CLIENT_DECISION_LABELS,
  EVIDENCE_LEVEL_LABELS,
  RECOMMENDATION_LABELS,
  isGate,
  type ClientFeedbackStatus,
  type PublicShortlistCandidate,
  type PublicShortlistResponse,
  type PublicShortlistView,
} from "@/types/shortlist";

type Props = {
  token: string;
};

type TabId = "shortlist" | "comparison" | "decisions" | "message";

const SESSION_STORAGE_KEY = (token: string) => `decision-room-session:${token}`;

// --- Helpers ---------------------------------------------------------------

function getStoredSession(token: string): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.sessionStorage.getItem(SESSION_STORAGE_KEY(token));
  } catch {
    return null;
  }
}

function storeSession(token: string, value: string | null) {
  if (typeof window === "undefined") return;
  try {
    if (value === null) {
      window.sessionStorage.removeItem(SESSION_STORAGE_KEY(token));
    } else {
      window.sessionStorage.setItem(SESSION_STORAGE_KEY(token), value);
    }
  } catch {
    /* sessionStorage no disponible → ignorar */
  }
}

function formatDate(value: string | null | undefined): string | null {
  if (!value) return null;
  try {
    return new Date(value).toLocaleDateString("es-ES", {
      day: "2-digit",
      month: "long",
      year: "numeric",
    });
  } catch {
    return value;
  }
}

function statusTone(status: ClientFeedbackStatus | null) {
  if (status === "favorite" || status === "interested")
    return { bg: "bg-emerald-50", border: "border-emerald-300", text: "text-emerald-700", label: CLIENT_DECISION_LABELS[status] };
  if (status === "interview_requested" || status === "want_interview")
    return { bg: "bg-brand-blueSoft", border: "border-brand-blue", text: "text-brand-blue", label: CLIENT_DECISION_LABELS[status] };
  if (status === "more_info_requested")
    return { bg: "bg-amber-50", border: "border-amber-300", text: "text-amber-700", label: CLIENT_DECISION_LABELS[status] };
  if (status === "keep_in_review")
    return { bg: "bg-slate-100", border: "border-slate-300", text: "text-slate-700", label: CLIENT_DECISION_LABELS[status] };
  if (status === "rejected" || status === "not_interested")
    return { bg: "bg-rose-50", border: "border-rose-300", text: "text-rose-700", label: CLIENT_DECISION_LABELS[status] };
  return { bg: "bg-slate-50", border: "border-slate-200", text: "text-brand-grayMid", label: "Sin decisión" };
}

function scoreTone(score: number | null | undefined): {
  ring: string;
  text: string;
  bg: string;
  badge: string;
} {
  if (score === null || score === undefined)
    return { ring: "ring-slate-200", text: "text-brand-grayMid", bg: "bg-slate-50", badge: "bg-slate-100 text-brand-grayMid" };
  if (score >= 85)
    return { ring: "ring-emerald-300", text: "text-emerald-700", bg: "bg-emerald-50", badge: "bg-emerald-100 text-emerald-700" };
  if (score >= 70)
    return { ring: "ring-brand-blue/40", text: "text-brand-blue", bg: "bg-brand-blueSoft/30", badge: "bg-brand-blueSoft text-brand-blue" };
  if (score >= 55)
    return { ring: "ring-amber-300", text: "text-amber-700", bg: "bg-amber-50", badge: "bg-amber-100 text-amber-700" };
  if (score >= 40)
    return { ring: "ring-zinc-300", text: "text-brand-grayMid", bg: "bg-slate-50", badge: "bg-zinc-100 text-brand-grayMid" };
  return { ring: "ring-rose-300", text: "text-rose-700", bg: "bg-rose-50", badge: "bg-rose-100 text-rose-700" };
}

// --- Access Gate ----------------------------------------------------------

function AccessGate({
  token,
  title,
  mandate,
  emailHint,
  expiresAt,
  onValidated,
}: {
  token: string;
  title: string;
  mandate: { client_name: string; target_role: string };
  emailHint: string | null;
  expiresAt: string | null;
  onValidated: (sessionToken: string) => void;
}) {
  const [code, setCode] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!/^[0-9]{6}$/.test(code)) {
      setError("Ingresa el código de 6 dígitos enviado a tu correo.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/public/shortlists/${token}/validate-code`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ code }),
        }
      );
      if (response.status === 401) {
        setError("Código incorrecto. Revisa el código enviado a tu correo o solicita uno nuevo.");
        return;
      }
      if (response.status === 410) {
        const body = await response.json().catch(() => ({}));
        setError(body?.detail || "Este acceso expiró. Solicita un nuevo link al consultor responsable.");
        return;
      }
      if (!response.ok) {
        setError(`Error ${response.status}. Intenta nuevamente.`);
        return;
      }
      const body = await response.json();
      onValidated(body.session_token as string);
    } catch (caught) {
      console.error(caught);
      setError("No fue posible conectar con TalentScan. Reintenta en unos minutos.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-10">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-soft">
        <div className="flex items-center gap-3 border-b border-slate-100 pb-5">
          <img src="/logo-talenscan.png" alt="TalentScan" className="h-9 w-auto" />
          <span className="text-xs text-brand-grayMid">·</span>
          <p className="text-[11px] uppercase tracking-wider text-brand-grayMid">
            Acceso privado
          </p>
        </div>
        <div className="mt-5">
          <div className="inline-flex items-center gap-1.5 rounded-full border border-brand-blue/20 bg-brand-blueSoft/40 px-2.5 py-0.5 text-[11px] font-semibold text-brand-blue">
            <Lock className="h-3 w-3" />
            Decision Room
          </div>
          <h1 className="mt-3 text-2xl font-semibold tracking-tight text-brand-black">
            Acceso al {title || "Decision Room"}
          </h1>
          <p className="mt-1.5 text-sm text-brand-grayMid">
            Ingresa el código de validación que enviamos a tu correo para revisar la shortlist
            de <strong className="text-brand-black">{mandate.target_role}</strong> ·{" "}
            {mandate.client_name}.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mt-6 space-y-3">
          <label htmlFor="access-code" className="block text-xs font-semibold uppercase tracking-wider text-brand-grayMid">
            Código de 6 dígitos
          </label>
          <input
            id="access-code"
            value={code}
            onChange={(event) => setCode(event.target.value.replace(/[^0-9]/g, "").slice(0, 6))}
            inputMode="numeric"
            autoComplete="one-time-code"
            placeholder="000000"
            maxLength={6}
            className="w-full rounded-lg border border-slate-200 bg-white px-4 py-3 text-center text-xl font-semibold tracking-[0.5em] text-brand-black placeholder:text-brand-grayMid/40 focus:border-brand-blue focus:outline-none focus:ring-2 focus:ring-brand-blue/20"
          />
          {error ? (
            <p className="flex items-start gap-1.5 text-xs text-rose-700">
              <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              {error}
            </p>
          ) : null}
          <button
            type="submit"
            disabled={submitting}
            className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-brand-blue px-4 py-2.5 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-blueDark disabled:opacity-60"
          >
            {submitting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <ShieldCheck className="h-4 w-4" />
            )}
            {submitting ? "Validando…" : "Ingresar al Decision Room"}
          </button>
        </form>

        <div className="mt-5 space-y-1 text-[11px] text-brand-grayMid">
          {emailHint ? (
            <p>El código fue enviado al correo autorizado ({emailHint}).</p>
          ) : (
            <p>El código fue enviado al correo autorizado.</p>
          )}
          {expiresAt ? (
            <p className="inline-flex items-center gap-1">
              <Clock className="h-3 w-3" />
              Acceso disponible hasta {formatDate(expiresAt)}.
            </p>
          ) : null}
        </div>
      </div>
    </main>
  );
}

// --- Section (acordeón premium) -------------------------------------------

function Section({
  title,
  icon: Icon,
  badge,
  count,
  children,
  defaultOpen = false,
  tone = "default",
}: {
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
  count?: number;
  children: React.ReactNode;
  defaultOpen?: boolean;
  tone?: "default" | "emerald" | "amber" | "blue";
}) {
  const [open, setOpen] = useState(defaultOpen);
  const palette: Record<string, string> = {
    default: "text-brand-grayMid",
    emerald: "text-emerald-700",
    amber: "text-amber-700",
    blue: "text-brand-blue",
  };
  return (
    <section className="overflow-hidden rounded-xl border border-slate-200 bg-white">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left transition hover:bg-slate-50"
      >
        <span className={cn("inline-flex items-center gap-2 text-sm font-semibold", palette[tone])}>
          <Icon className="h-4 w-4" />
          {title}
          {count !== undefined && count > 0 ? (
            <span className="rounded-full bg-slate-100 px-1.5 py-0.5 text-[11px] font-semibold text-brand-grayMid">
              {count}
            </span>
          ) : null}
          {badge ? (
            <span className="rounded-full bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-brand-grayMid">
              {badge}
            </span>
          ) : null}
        </span>
        <ChevronDown className={cn("h-4 w-4 text-brand-grayMid transition", open ? "rotate-180" : "")} />
      </button>
      {open ? <div className="border-t border-slate-100 px-4 py-4">{children}</div> : null}
    </section>
  );
}

// --- Score ring (visual) --------------------------------------------------

function ScoreRing({ score, category, size = "md" }: { score: number; category?: string | null; size?: "sm" | "md" | "lg" }) {
  const tone = scoreTone(score);
  const dim = size === "lg" ? "h-20 w-20 text-2xl" : size === "sm" ? "h-12 w-12 text-sm" : "h-16 w-16 text-xl";
  return (
    <div className="flex flex-col items-center gap-1">
      <div
        className={cn(
          "flex shrink-0 items-center justify-center rounded-full bg-white font-bold ring-4",
          dim,
          tone.ring,
          tone.text
        )}
      >
        {score}
      </div>
      {category ? <p className={cn("text-[10px] font-semibold uppercase tracking-wider", tone.text)}>{category}</p> : null}
    </div>
  );
}

// --- Dimension Bar --------------------------------------------------------

function DimensionBar({
  dimension,
  score,
  max,
  status,
  evidenceLevel,
  rationale,
}: {
  dimension: string;
  score: number | null;
  max: number | null;
  status: string | null;
  evidenceLevel: string | null;
  rationale: string | null;
}) {
  const total = max || 1;
  const value = score ?? 0;
  const pct = Math.max(0, Math.min(100, (value / total) * 100));
  const barTone =
    pct >= 80 ? "bg-emerald-500" : pct >= 60 ? "bg-brand-blue" : pct >= 40 ? "bg-amber-500" : pct > 0 ? "bg-rose-400" : "bg-slate-200";
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between gap-3 text-xs">
        <span className="font-medium text-brand-black">{dimension}</span>
        <span className="font-semibold text-brand-grayMid">
          {value}/{max ?? "?"}
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-100">
        <div className={cn("h-full rounded-full transition-all", barTone)} style={{ width: `${pct}%` }} />
      </div>
      {(status || evidenceLevel || rationale) ? (
        <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5 text-[11px] text-brand-grayMid">
          {status ? <span>{status}</span> : null}
          {evidenceLevel ? <span>· evidencia {evidenceLevel.toLowerCase()}</span> : null}
          {rationale ? <span className="block w-full italic">{rationale}</span> : null}
        </div>
      ) : null}
    </div>
  );
}

// --- Decision Drawer (feedback) -------------------------------------------

function DecisionDrawer({
  candidate,
  open,
  onClose,
  onSubmit,
  allowRating,
  allowComments,
  saving,
  initialDecision,
}: {
  candidate: PublicShortlistCandidate;
  open: boolean;
  onClose: () => void;
  onSubmit: (decision: ClientFeedbackStatus, comment: string, rating: number | null) => Promise<void>;
  allowRating: boolean;
  allowComments: boolean;
  saving: boolean;
  initialDecision: ClientFeedbackStatus | null;
}) {
  const [decision, setDecision] = useState<ClientFeedbackStatus | null>(initialDecision);
  const [comment, setComment] = useState(candidate.client_comment || "");
  const [rating, setRating] = useState<number | null>(candidate.rating);

  useEffect(() => {
    if (open) {
      setDecision(initialDecision);
      setComment(candidate.client_comment || "");
      setRating(candidate.rating);
    }
  }, [open, initialDecision, candidate.client_comment, candidate.rating]);

  if (!open) return null;

  const decisionTitle = decision
    ? `${CLIENT_DECISION_LABELS[decision]} · ${candidate.full_name}`
    : `Decisión sobre ${candidate.full_name}`;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-brand-black/40 px-4 py-6 sm:items-center" role="dialog" aria-modal="true">
      <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl">
        <div className="flex items-start justify-between gap-4 border-b border-slate-100 pb-4">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-blue">
              Registrar decisión
            </p>
            <h3 className="mt-0.5 text-lg font-semibold text-brand-black">{decisionTitle}</h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-brand-grayMid transition hover:bg-slate-100"
            aria-label="Cerrar"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="mt-4 space-y-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-brand-grayMid">
              ¿Qué decides para este candidato?
            </p>
            <div className="mt-2 grid grid-cols-1 gap-1.5 sm:grid-cols-2">
              {(
                [
                  ["interview_requested", Briefcase, "Solicitar entrevista"],
                  ["more_info_requested", HelpCircle, "Pedir más información"],
                  ["keep_in_review", Clock, "Mantener en revisión"],
                  ["favorite", Star, "Marcar como favorito"],
                  ["rejected", ThumbsDown, "Descartar"],
                ] as const
              ).map(([value, Icon, label]) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setDecision(value)}
                  className={cn(
                    "inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-sm transition",
                    decision === value
                      ? "border-brand-blue bg-brand-blueSoft text-brand-blue"
                      : "border-slate-200 bg-white text-brand-grayMid hover:border-brand-blue/40 hover:text-brand-blue"
                  )}
                >
                  <Icon className="h-3.5 w-3.5" />
                  {label}
                </button>
              ))}
            </div>
          </div>

          {allowRating ? (
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-brand-grayMid">
                Valoración (opcional)
              </p>
              <div className="mt-2 flex gap-1">
                {[1, 2, 3, 4, 5].map((value) => (
                  <button
                    key={value}
                    type="button"
                    onClick={() => setRating(value === rating ? null : value)}
                    className={cn(
                      "inline-flex h-9 w-9 items-center justify-center rounded-lg border text-sm font-medium transition",
                      rating !== null && rating >= value
                        ? "border-amber-300 bg-amber-50 text-amber-700"
                        : "border-slate-200 bg-white text-brand-grayMid hover:border-amber-200 hover:text-amber-600"
                    )}
                    aria-label={`${value} de 5`}
                  >
                    <Star className={cn("h-4 w-4", rating !== null && rating >= value ? "fill-current" : "")} />
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          {allowComments ? (
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-brand-grayMid">
                Comentario (opcional)
              </p>
              <textarea
                value={comment}
                onChange={(event) => setComment(event.target.value)}
                rows={3}
                placeholder="Comparte contexto que ayude al consultor: qué te llama la atención, qué dudas tienes, qué esperas validar en entrevista…"
                className="mt-2 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-brand-black placeholder:text-brand-grayMid focus:border-brand-blue focus:outline-none focus:ring-2 focus:ring-brand-blue/15"
              />
            </div>
          ) : null}
        </div>

        <div className="mt-5 flex items-center justify-end gap-2 border-t border-slate-100 pt-4">
          <button
            type="button"
            onClick={onClose}
            disabled={saving}
            className="inline-flex items-center rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-brand-grayMid transition hover:bg-slate-50 disabled:opacity-60"
          >
            Cancelar
          </button>
          <button
            type="button"
            disabled={saving || !decision}
            onClick={() => decision && onSubmit(decision, comment, rating)}
            className="inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-4 py-2 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-blueDark disabled:opacity-60"
          >
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            {saving ? "Guardando…" : "Guardar decisión"}
          </button>
        </div>
      </div>
    </div>
  );
}

// --- PDF Viewer (modal con iframe) ---------------------------------------

function PdfViewerModal({
  url,
  title,
  onClose,
}: {
  url: string;
  title: string;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-stretch justify-center bg-brand-black/60 p-3 sm:p-6" role="dialog" aria-modal="true">
      <div className="flex w-full max-w-5xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-3">
          <div className="flex items-center gap-2 text-sm font-semibold text-brand-black">
            <FileText className="h-4 w-4 text-brand-blue" />
            {title}
          </div>
          <div className="flex items-center gap-2">
            <a
              href={url}
              target="_blank"
              rel="noreferrer noopener"
              className="inline-flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-brand-grayMid hover:bg-slate-50"
            >
              Abrir en nueva pestaña
            </a>
            <button
              type="button"
              onClick={onClose}
              className="inline-flex h-8 w-8 items-center justify-center rounded-md text-brand-grayMid hover:bg-slate-100"
              aria-label="Cerrar"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
        <iframe src={url} title={title} className="h-full min-h-[600px] w-full flex-1 bg-slate-50" />
      </div>
    </div>
  );
}

// --- Candidate Card (premium con secciones colapsables) -------------------

function CandidateCard({
  candidate,
  rank,
  view,
  token,
  sessionToken,
  onOpenDrawer,
  onOpenPdf,
}: {
  candidate: PublicShortlistCandidate;
  rank: number;
  view: PublicShortlistView;
  token: string;
  sessionToken: string | null;
  onOpenDrawer: (candidate: PublicShortlistCandidate) => void;
  onOpenPdf: (url: string, title: string) => void;
}) {
  const tone = statusTone(candidate.client_status);
  const initials = useMemo(
    () =>
      candidate.full_name
        .split(/\s+/)
        .map((p) => p[0])
        .filter(Boolean)
        .slice(0, 2)
        .join("")
        .toUpperCase(),
    [candidate.full_name]
  );

  const summary = candidate.consultant_summary || candidate.professional_summary;

  function openReportPdf() {
    // PDF se sirve como respuesta autenticada con header X-Decision-Room-Session.
    // Como iframe no permite setear headers custom, descargamos como blob y
    // generamos un object URL que se renderiza en el modal.
    void (async () => {
      try {
        const headers: Record<string, string> = {};
        if (sessionToken) headers["X-Decision-Room-Session"] = sessionToken;
        const response = await fetch(
          `${API_BASE_URL}/api/public/shortlists/${token}/items/${candidate.item_id}/reporte/pdf`,
          { headers }
        );
        if (!response.ok) {
          window.alert("No fue posible cargar el informe. Reintenta más tarde.");
          return;
        }
        const blob = await response.blob();
        const blobUrl = URL.createObjectURL(blob);
        onOpenPdf(blobUrl, `Scan 360 · ${candidate.full_name}`);
      } catch (caught) {
        console.error(caught);
        window.alert("Error al cargar el informe.");
      }
    })();
  }

  return (
    <article
      className={cn(
        "overflow-hidden rounded-2xl border bg-white shadow-soft transition",
        tone.border,
        candidate.client_status ? "ring-1 ring-current/10" : ""
      )}
    >
      {/* Header ejecutivo siempre visible */}
      <header className={cn("border-b border-slate-100 p-5", scoreTone(candidate.score).bg)}>
        <div className="flex flex-wrap items-start gap-4">
          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-white text-xl font-semibold text-brand-blue shadow-soft">
            {initials || "—"}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="rounded-full bg-white px-2 py-0.5 text-[11px] font-semibold text-brand-grayMid shadow-sm">
                #{rank}
              </span>
              {candidate.is_pinned ? (
                <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-[11px] font-semibold text-amber-700">
                  <Pin className="h-3 w-3" />
                  Destacado por el consultor
                </span>
              ) : null}
              {candidate.recommendation ? (
                <span className="inline-flex items-center gap-1 rounded-full bg-brand-blueSoft px-2 py-0.5 text-[11px] font-semibold text-brand-blue">
                  <Sparkles className="h-3 w-3" />
                  {RECOMMENDATION_LABELS[candidate.recommendation]}
                </span>
              ) : null}
              {candidate.evidence_level ? (
                <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-semibold text-brand-grayMid">
                  <Info className="h-3 w-3" />
                  {EVIDENCE_LEVEL_LABELS[candidate.evidence_level]}
                </span>
              ) : null}
            </div>
            <h3 className="mt-2 text-xl font-semibold text-brand-black">{candidate.full_name}</h3>
            <p className="text-sm text-brand-grayMid">{candidate.headline}</p>
            <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-brand-grayMid">
              {candidate.total_years_experience ? (
                <span className="inline-flex items-center gap-1">
                  <Calendar className="h-3 w-3" />
                  {candidate.total_years_experience}+ años de experiencia
                </span>
              ) : null}
              {candidate.country ? (
                <span className="inline-flex items-center gap-1">
                  <MapPin className="h-3 w-3" />
                  {candidate.country}
                </span>
              ) : null}
              {view.show_availability && candidate.availability ? (
                <span className="inline-flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {candidate.availability}
                </span>
              ) : null}
              {view.show_salary && candidate.salary_expectation ? (
                <span className="inline-flex items-center gap-1">
                  <Wallet className="h-3 w-3" />
                  {candidate.salary_expectation}
                </span>
              ) : null}
              {candidate.linkedin_url ? (
                <a
                  href={candidate.linkedin_url}
                  target="_blank"
                  rel="noreferrer noopener"
                  className="inline-flex items-center gap-1 text-brand-blue hover:underline"
                >
                  <Linkedin className="h-3 w-3" />
                  Perfil LinkedIn
                </a>
              ) : null}
            </div>
          </div>
          {candidate.score !== null ? (
            <ScoreRing score={candidate.score} category={candidate.score_category} size="md" />
          ) : null}
          {candidate.client_status ? (
            <span className={cn("inline-flex shrink-0 items-center gap-1 self-start rounded-full px-3 py-1 text-xs font-semibold", tone.bg, tone.text)}>
              <CheckCircle2 className="h-3 w-3" />
              {tone.label}
            </span>
          ) : null}
        </div>
      </header>

      {/* Cuerpo con secciones colapsables */}
      <div className="space-y-2 p-4">
        {summary ? (
          <section className="rounded-xl border border-brand-blue/20 bg-brand-blueSoft/30 p-4">
            <p className="inline-flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-brand-blue">
              <Quote className="h-3 w-3" />
              Resumen del consultor
            </p>
            <p className="mt-1.5 text-sm leading-relaxed text-brand-black">{summary}</p>
          </section>
        ) : null}

        {candidate.why_fits.length > 0 ? (
          <Section title="Por qué calza" icon={CheckCircle2} count={candidate.why_fits.length} tone="emerald" defaultOpen>
            <ul className="space-y-1.5">
              {candidate.why_fits.map((item, idx) => (
                <li
                  key={idx}
                  className="flex items-start gap-2 rounded-lg border border-emerald-100 bg-emerald-50/40 px-3 py-2 text-sm text-brand-black"
                >
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </Section>
        ) : null}

        {view.show_risks && candidate.risks_or_validations.length > 0 ? (
          <Section title="Puntos a validar en entrevista" icon={AlertCircle} count={candidate.risks_or_validations.length} tone="amber" defaultOpen>
            <ul className="space-y-1.5">
              {candidate.risks_or_validations.map((item, idx) => (
                <li key={idx} className="flex items-start gap-2 rounded-lg border border-amber-100 bg-amber-50/40 px-3 py-2 text-sm text-amber-900">
                  <Minus className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </Section>
        ) : null}

        {candidate.experience.length > 0 ? (
          <Section title="Trayectoria profesional" icon={Briefcase} count={candidate.experience.length}>
            <ol className="relative space-y-3 border-l border-slate-200 pl-4">
              {candidate.experience.map((role, idx) => (
                <li key={idx} className="relative">
                  <span className="absolute -left-[21px] mt-1 h-2.5 w-2.5 rounded-full bg-brand-blue ring-4 ring-brand-blueSoft" />
                  <p className="text-sm font-semibold text-brand-black">{role.title || "Cargo"}</p>
                  {role.company ? <p className="text-xs text-brand-grayMid">{role.company}</p> : null}
                  {(role.start_date || role.end_date || role.duration_years) ? (
                    <p className="mt-0.5 text-[11px] text-brand-grayMid">
                      {[role.start_date, role.end_date].filter(Boolean).join(" — ")}
                      {role.duration_years ? ` · ${role.duration_years} años` : ""}
                    </p>
                  ) : null}
                  {role.responsibilities.length > 0 ? (
                    <ul className="mt-1.5 space-y-0.5">
                      {role.responsibilities.map((r, i) => (
                        <li key={i} className="flex items-start gap-1.5 text-xs text-brand-black">
                          <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-brand-grayMid" />
                          <span>{r}</span>
                        </li>
                      ))}
                    </ul>
                  ) : null}
                  {role.achievements.length > 0 ? (
                    <ul className="mt-1.5 space-y-0.5">
                      {role.achievements.map((a, i) => (
                        <li key={i} className="flex items-start gap-1.5 text-xs text-emerald-700">
                          <Trophy className="mt-0.5 h-3 w-3 shrink-0" />
                          <span>{a}</span>
                        </li>
                      ))}
                    </ul>
                  ) : null}
                  {role.tools_or_systems.length > 0 ? (
                    <div className="mt-1.5 flex flex-wrap gap-1">
                      {role.tools_or_systems.map((t) => (
                        <span key={t} className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-brand-grayMid">
                          {t}
                        </span>
                      ))}
                    </div>
                  ) : null}
                </li>
              ))}
            </ol>
          </Section>
        ) : null}

        {(candidate.education.length > 0 || candidate.certifications.length > 0) ? (
          <Section title="Formación y certificaciones" icon={GraduationCap} count={candidate.education.length + candidate.certifications.length}>
            <div className="grid gap-4 md:grid-cols-2">
              {candidate.education.length > 0 ? (
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-grayMid">Formación</p>
                  <ul className="mt-1.5 space-y-1 text-sm text-brand-black">
                    {candidate.education.slice(0, 8).map((edu, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-blue" />
                        <span>{edu}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
              {candidate.certifications.length > 0 ? (
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-grayMid">
                    <Award className="mr-1 inline-block h-3 w-3" /> Certificaciones
                  </p>
                  <ul className="mt-1.5 space-y-1 text-sm text-brand-black">
                    {candidate.certifications.slice(0, 8).map((cert, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500" />
                        <span>{cert}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
          </Section>
        ) : null}

        {candidate.achievements.length > 0 ? (
          <Section title="Logros destacados" icon={Trophy} count={candidate.achievements.length} tone="emerald">
            <ul className="space-y-2">
              {candidate.achievements.map((item, idx) => (
                <li key={idx} className="rounded-lg border border-emerald-100 bg-emerald-50/40 p-3 text-sm leading-relaxed text-brand-black">
                  {item}
                </li>
              ))}
            </ul>
          </Section>
        ) : null}

        {(candidate.tools.length > 0 || candidate.transferable_skills.length > 0) ? (
          <Section title="Herramientas y habilidades" icon={Wrench} count={candidate.tools.length + candidate.transferable_skills.length}>
            {candidate.tools.length > 0 ? (
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-grayMid">Stack y sistemas</p>
                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  {candidate.tools.slice(0, 20).map((tool) => (
                    <span key={tool} className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-brand-grayMid">
                      {tool}
                    </span>
                  ))}
                </div>
              </div>
            ) : null}
            {candidate.transferable_skills.length > 0 ? (
              <div className="mt-3">
                <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-grayMid">
                  <TrendingUp className="mr-1 inline-block h-3 w-3" /> Habilidades transferibles
                </p>
                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  {candidate.transferable_skills.map((skill) => (
                    <span key={skill} className="rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs font-medium text-indigo-700">
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            ) : null}
          </Section>
        ) : null}

        {candidate.languages.length > 0 ? (
          <Section title="Idiomas" icon={Languages} count={candidate.languages.length}>
            <div className="flex flex-wrap gap-1.5">
              {candidate.languages.map((lang) => (
                <span key={lang} className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-brand-grayMid">
                  {lang}
                </span>
              ))}
            </div>
          </Section>
        ) : null}

        {view.show_scores && candidate.dimension_scores.length > 0 ? (
          <Section title="Score 360 desglosado" icon={Sparkles} count={candidate.dimension_scores.length} tone="blue">
            <div className="space-y-3">
              {candidate.dimension_scores.map((ds, idx) => (
                <DimensionBar
                  key={idx}
                  dimension={ds.dimension}
                  score={ds.score}
                  max={ds.max_score}
                  status={ds.status}
                  evidenceLevel={ds.evidence_level}
                  rationale={ds.rationale}
                />
              ))}
              {candidate.final_verdict ? (
                <div className="mt-2 rounded-lg bg-slate-50 p-3 text-xs text-brand-grayMid">
                  <strong className="text-brand-black">Veredicto:</strong> {candidate.final_verdict}
                </div>
              ) : null}
            </div>
          </Section>
        ) : null}

        {view.show_risks && candidate.interview_questions.length > 0 ? (
          <Section title="Preguntas sugeridas para entrevista" icon={MessageSquare} count={candidate.interview_questions.length}>
            <ol className="space-y-1.5">
              {candidate.interview_questions.map((q, idx) => (
                <li key={idx} className="flex items-start gap-2 text-sm text-brand-black">
                  <span className="mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand-blueSoft text-[11px] font-semibold text-brand-blue">
                    {idx + 1}
                  </span>
                  <span>{q}</span>
                </li>
              ))}
            </ol>
          </Section>
        ) : null}

        {candidate.can_download_report ? (
          <Section title="Informe completo Scan 360" icon={FileText} tone="blue" badge="PDF">
            <p className="text-xs text-brand-grayMid">
              Informe ejecutivo completo con score por dimensión, evidencia y veredicto. Visualízalo aquí o ábrelo en una pestaña aparte.
            </p>
            <button
              type="button"
              onClick={openReportPdf}
              className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-3 py-2 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-blueDark"
            >
              <FileText className="h-4 w-4" />
              Abrir informe Scan 360
            </button>
          </Section>
        ) : null}

        {candidate.client_comment ? (
          <section className="rounded-xl border border-slate-200 bg-slate-50 p-3">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-grayMid">
              <MessageSquare className="mr-1 inline-block h-3 w-3" /> Tu último comentario
            </p>
            <p className="mt-1 text-sm text-brand-black">{candidate.client_comment}</p>
          </section>
        ) : null}

        <div className="flex items-center justify-end pt-2">
          <button
            type="button"
            onClick={() => onOpenDrawer(candidate)}
            className="inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-4 py-2 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-blueDark"
          >
            <Heart className="h-3.5 w-3.5" />
            {candidate.client_status ? "Actualizar decisión" : "Registrar decisión"}
          </button>
        </div>
      </div>
    </article>
  );
}

// --- Executive Comparison (pro, con barras visuales) ---------------------

function ExecutiveComparisonTable({ view, onOpenDrawer }: { view: PublicShortlistView; onOpenDrawer: (c: PublicShortlistCandidate) => void }) {
  const allDimensions = useMemo(() => {
    const set = new Map<string, number>();
    for (const c of view.candidates) {
      for (const ds of c.dimension_scores) {
        if (ds.dimension && !set.has(ds.dimension)) {
          set.set(ds.dimension, ds.max_score ?? 0);
        }
      }
    }
    return Array.from(set.entries()).map(([dimension, max]) => ({ dimension, max }));
  }, [view.candidates]);

  function getScore(c: PublicShortlistCandidate, dimension: string): number | null {
    return c.dimension_scores.find((d) => d.dimension === dimension)?.score ?? null;
  }

  return (
    <div className="space-y-5">
      {/* Hero: ranking visual */}
      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-soft">
        <div className="border-b border-slate-100 p-5">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-blue">
            Comparación ejecutiva
          </p>
          <p className="mt-1 text-sm text-brand-grayMid">
            Resumen visual para priorizar entrevistas y avanzar con los candidatos de mayor calce.
          </p>
        </div>
        <div className="grid gap-4 p-5 sm:grid-cols-2 lg:grid-cols-3">
          {view.candidates.map((c, idx) => {
            const tone = statusTone(c.client_status);
            return (
              <article
                key={c.item_id}
                className={cn(
                  "rounded-xl border bg-white p-4 transition hover:shadow-md",
                  tone.border
                )}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-semibold text-brand-grayMid">
                      #{idx + 1}
                    </span>
                    <p className="mt-1.5 truncate text-sm font-semibold text-brand-black">{c.full_name}</p>
                    <p className="truncate text-xs text-brand-grayMid">{c.headline}</p>
                  </div>
                  {c.score !== null ? <ScoreRing score={c.score} size="sm" /> : null}
                </div>
                <div className="mt-3 grid grid-cols-2 gap-2 text-[11px]">
                  {c.recommendation ? (
                    <div className="rounded-md bg-brand-blueSoft/40 px-2 py-1 text-brand-blue">
                      {RECOMMENDATION_LABELS[c.recommendation]}
                    </div>
                  ) : null}
                  {view.show_availability && c.availability ? (
                    <div className="rounded-md bg-slate-50 px-2 py-1 text-brand-grayMid">
                      <Clock className="mr-1 inline-block h-3 w-3" />
                      {c.availability}
                    </div>
                  ) : null}
                  {c.total_years_experience ? (
                    <div className="rounded-md bg-slate-50 px-2 py-1 text-brand-grayMid">
                      {c.total_years_experience}+ años
                    </div>
                  ) : null}
                  {c.industries[0] ? (
                    <div className="rounded-md bg-slate-50 px-2 py-1 text-brand-grayMid">
                      {c.industries[0]}
                    </div>
                  ) : null}
                </div>
                <div className="mt-3 flex items-center justify-between">
                  <span className={cn("inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold", tone.bg, tone.text)}>
                    {tone.label}
                  </span>
                  <button
                    type="button"
                    onClick={() => onOpenDrawer(c)}
                    className="inline-flex items-center gap-1 rounded-md border border-brand-blue/30 bg-white px-2 py-1 text-[11px] font-semibold text-brand-blue hover:bg-brand-blueSoft/40"
                  >
                    <Heart className="h-3 w-3" />
                    Decidir
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      </section>

      {/* Score por dimensión (si hay datos) */}
      {view.show_scores && allDimensions.length > 0 ? (
        <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-soft">
          <div className="border-b border-slate-100 p-5">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-blue">
              Score por dimensión
            </p>
            <p className="mt-1 text-sm text-brand-grayMid">
              Comparación dimensión por dimensión con barras proporcionales al máximo de cada criterio.
            </p>
          </div>
          <div className="overflow-x-auto p-5">
            <table className="min-w-full text-xs">
              <thead>
                <tr className="border-b border-slate-100 text-[10px] uppercase tracking-wider text-brand-grayMid">
                  <th className="px-2 py-2 text-left">Dimensión</th>
                  {view.candidates.map((c) => (
                    <th key={c.item_id} className="px-2 py-2 text-left">
                      {c.full_name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {allDimensions.map(({ dimension, max }) => (
                  <tr key={dimension} className="border-b border-slate-100 last:border-0">
                    <td className="px-2 py-3 align-top text-brand-black">
                      <p className="font-medium">{dimension}</p>
                      <p className="text-[10px] text-brand-grayMid">máx {max}</p>
                    </td>
                    {view.candidates.map((c) => {
                      const score = getScore(c, dimension);
                      const pct = score !== null && max > 0 ? Math.max(0, Math.min(100, (score / max) * 100)) : 0;
                      const barTone =
                        pct >= 80
                          ? "bg-emerald-500"
                          : pct >= 60
                          ? "bg-brand-blue"
                          : pct >= 40
                          ? "bg-amber-500"
                          : pct > 0
                          ? "bg-rose-400"
                          : "bg-slate-200";
                      return (
                        <td key={c.item_id} className="min-w-[140px] px-2 py-3 align-top">
                          <div className="flex items-center gap-2">
                            <div className="flex-1 overflow-hidden rounded-full bg-slate-100">
                              <div className="h-2 rounded-full" style={{ width: `${pct}%` }}>
                                <div className={cn("h-full rounded-full", barTone)} style={{ width: "100%" }} />
                              </div>
                            </div>
                            <span className="w-10 text-right text-[11px] font-semibold text-brand-black">
                              {score !== null ? `${score}` : "—"}
                            </span>
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      {/* Fortalezas vs Riesgos lado a lado */}
      <section className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-emerald-200 bg-white p-5 shadow-soft">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-emerald-700">
            Fortalezas por candidato
          </p>
          <div className="mt-3 space-y-3">
            {view.candidates.map((c) => (
              <div key={c.item_id} className="rounded-lg border border-emerald-100 bg-emerald-50/30 p-3">
                <p className="text-sm font-semibold text-brand-black">{c.full_name}</p>
                {c.why_fits.length > 0 ? (
                  <ul className="mt-1 space-y-0.5 text-xs text-brand-black">
                    {c.why_fits.slice(0, 3).map((w, i) => (
                      <li key={i} className="flex gap-1.5">
                        <CheckCircle2 className="mt-0.5 h-3 w-3 shrink-0 text-emerald-600" />
                        {w}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-1 text-xs italic text-brand-grayMid">Sin fortalezas registradas</p>
                )}
              </div>
            ))}
          </div>
        </div>
        {view.show_risks ? (
          <div className="rounded-2xl border border-amber-200 bg-white p-5 shadow-soft">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-amber-700">
              Puntos a validar por candidato
            </p>
            <div className="mt-3 space-y-3">
              {view.candidates.map((c) => (
                <div key={c.item_id} className="rounded-lg border border-amber-100 bg-amber-50/30 p-3">
                  <p className="text-sm font-semibold text-brand-black">{c.full_name}</p>
                  {c.risks_or_validations.length > 0 ? (
                    <ul className="mt-1 space-y-0.5 text-xs text-brand-black">
                      {c.risks_or_validations.slice(0, 3).map((w, i) => (
                        <li key={i} className="flex gap-1.5">
                          <Minus className="mt-0.5 h-3 w-3 shrink-0 text-amber-600" />
                          {w}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="mt-1 text-xs italic text-brand-grayMid">Sin puntos a validar</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </section>
    </div>
  );
}

// --- Decisiones interactivas (mini-Kanban con drag&drop) ------------------

const DECISION_BUCKETS: {
  id: ClientFeedbackStatus | "pending";
  label: string;
  description: string;
  tone: string;
}[] = [
  {
    id: "interview_requested",
    label: "Solicitar entrevista",
    description: "Avanzar al proceso de entrevista",
    tone: "border-brand-blue/40 bg-brand-blueSoft/30",
  },
  {
    id: "favorite",
    label: "Favoritos",
    description: "Candidatos preferidos",
    tone: "border-emerald-300 bg-emerald-50/40",
  },
  {
    id: "more_info_requested",
    label: "Más información",
    description: "Pedir validaciones adicionales",
    tone: "border-amber-300 bg-amber-50/40",
  },
  {
    id: "keep_in_review",
    label: "En revisión",
    description: "Decisión postergada",
    tone: "border-slate-300 bg-slate-100/60",
  },
  {
    id: "rejected",
    label: "Descartados",
    description: "No avanzan en este proceso",
    tone: "border-rose-300 bg-rose-50/40",
  },
  {
    id: "pending",
    label: "Sin decisión",
    description: "Pendientes de revisión",
    tone: "border-slate-200 bg-white",
  },
];

function bucketOf(status: ClientFeedbackStatus | null): ClientFeedbackStatus | "pending" {
  if (status === null) return "pending";
  if (status === "interested") return "favorite";
  if (status === "want_interview") return "interview_requested";
  if (status === "not_interested") return "rejected";
  return status;
}

function DecisionChip({ candidate, isDragging = false }: { candidate: PublicShortlistCandidate; isDragging?: boolean }) {
  const sortable = useSortable({ id: `c-${candidate.item_id}`, data: { candidate } });
  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(sortable.transform),
    transition: sortable.transition,
    opacity: sortable.isDragging ? 0.3 : 1,
  };
  const initials = candidate.full_name
    .split(/\s+/)
    .map((p) => p[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase();
  return (
    <article
      ref={sortable.setNodeRef}
      style={style}
      className={cn(
        "group rounded-lg border border-slate-200 bg-white p-2 shadow-soft transition hover:border-brand-blue/40",
        isDragging && "rotate-1 shadow-elevated"
      )}
    >
      <div className="flex items-start gap-2">
        <button
          type="button"
          aria-label="Mover"
          className="mt-0.5 cursor-grab text-slate-300 transition hover:text-brand-grayMid active:cursor-grabbing"
          {...sortable.attributes}
          {...sortable.listeners}
        >
          <GripVertical className="h-3.5 w-3.5" />
        </button>
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-brand-blueSoft text-[10px] font-semibold text-brand-blue">
          {initials || "—"}
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-xs font-semibold text-brand-black">{candidate.full_name}</p>
          <p className="truncate text-[11px] text-brand-grayMid">{candidate.headline}</p>
        </div>
        {candidate.score !== null ? (
          <span className={cn("ml-1 shrink-0 rounded-full px-1.5 py-0.5 text-[10px] font-semibold", scoreTone(candidate.score).badge)}>
            {candidate.score}
          </span>
        ) : null}
      </div>
    </article>
  );
}

function DecisionBucket({
  bucket,
  candidates,
}: {
  bucket: typeof DECISION_BUCKETS[number];
  candidates: PublicShortlistCandidate[];
}) {
  const { setNodeRef, isOver } = useDroppable({ id: `b-${bucket.id}`, data: { bucketId: bucket.id } });
  return (
    <section
      ref={setNodeRef}
      className={cn(
        "flex h-full min-h-[200px] flex-col rounded-2xl border p-3 transition",
        bucket.tone,
        isOver && "ring-2 ring-brand-blue/40"
      )}
    >
      <header className="flex items-center justify-between pb-2">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wider">{bucket.label}</p>
          <p className="text-[10px] text-brand-grayMid">{bucket.description}</p>
        </div>
        <span className="rounded-full bg-white px-2 py-0.5 text-[11px] font-semibold text-brand-black shadow-sm">
          {candidates.length}
        </span>
      </header>
      <SortableContext items={candidates.map((c) => `c-${c.item_id}`)} strategy={verticalListSortingStrategy}>
        <div className="flex flex-1 flex-col gap-1.5">
          {candidates.length === 0 ? (
            <p className="rounded-lg border border-dashed border-slate-300 px-2 py-6 text-center text-[11px] italic text-brand-grayMid">
              Arrastra candidatos aquí
            </p>
          ) : (
            candidates.map((c) => <DecisionChip key={c.item_id} candidate={c} />)
          )}
        </div>
      </SortableContext>
    </section>
  );
}

function DecisionsBoard({
  view,
  onMove,
}: {
  view: PublicShortlistView;
  onMove: (candidate: PublicShortlistCandidate, target: ClientFeedbackStatus | "pending") => Promise<void>;
}) {
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 4 } }));
  const [activeId, setActiveId] = useState<string | null>(null);

  const byBucket = useMemo(() => {
    const map = new Map<string, PublicShortlistCandidate[]>();
    for (const b of DECISION_BUCKETS) map.set(b.id, []);
    for (const c of view.candidates) {
      const b = bucketOf(c.client_status);
      map.get(b)?.push(c);
    }
    return map;
  }, [view.candidates]);

  const activeCandidate = useMemo(() => {
    if (!activeId) return null;
    const id = Number(activeId.replace("c-", ""));
    return view.candidates.find((c) => c.item_id === id) || null;
  }, [activeId, view.candidates]);

  function handleStart(event: DragStartEvent) {
    setActiveId(String(event.active.id));
  }

  async function handleEnd(event: DragEndEvent) {
    setActiveId(null);
    const { active, over } = event;
    if (!over) return;
    const overId = String(over.id);
    // Target: either bucket header (b-X) or another candidate (c-Y) → derive bucket from candidate
    let targetBucket: ClientFeedbackStatus | "pending" | null = null;
    if (overId.startsWith("b-")) {
      targetBucket = overId.slice(2) as ClientFeedbackStatus | "pending";
    } else if (overId.startsWith("c-")) {
      const id = Number(overId.slice(2));
      const target = view.candidates.find((c) => c.item_id === id);
      if (target) targetBucket = bucketOf(target.client_status);
    }
    if (!targetBucket) return;
    const draggedId = Number(String(active.id).replace("c-", ""));
    const dragged = view.candidates.find((c) => c.item_id === draggedId);
    if (!dragged) return;
    const currentBucket = bucketOf(dragged.client_status);
    if (currentBucket === targetBucket) return;
    await onMove(dragged, targetBucket);
  }

  return (
    <DndContext sensors={sensors} collisionDetection={closestCorners} onDragStart={handleStart} onDragEnd={handleEnd}>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {DECISION_BUCKETS.map((bucket) => (
          <DecisionBucket key={bucket.id} bucket={bucket} candidates={byBucket.get(bucket.id) || []} />
        ))}
      </div>
      <DragOverlay>
        {activeCandidate ? <DecisionChip candidate={activeCandidate} isDragging /> : null}
      </DragOverlay>
    </DndContext>
  );
}

// --- Decision Room Body ---------------------------------------------------

function DecisionRoomBody({
  token,
  initialData,
  sessionToken,
  onReloadRequest,
}: {
  token: string;
  initialData: PublicShortlistView;
  sessionToken: string | null;
  onReloadRequest: () => void;
}) {
  const [data, setData] = useState(initialData);
  const [activeTab, setActiveTab] = useState<TabId>("shortlist");
  const [drawerFor, setDrawerFor] = useState<PublicShortlistCandidate | null>(null);
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState<string | null>(null);
  const [pdfModal, setPdfModal] = useState<{ url: string; title: string } | null>(null);

  const submitFeedback = useCallback(
    async (item: PublicShortlistCandidate, decision: ClientFeedbackStatus | null, comment: string | null, rating: number | null) => {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (sessionToken) headers["X-Decision-Room-Session"] = sessionToken;
      const response = await fetch(
        `${API_BASE_URL}/api/public/shortlists/${token}/items/${item.item_id}/feedback`,
        {
          method: "POST",
          headers,
          body: JSON.stringify({
            client_status: decision,
            client_comment: comment,
            rating: rating,
          }),
        }
      );
      if (response.status === 401) {
        onReloadRequest();
        return null;
      }
      if (!response.ok) throw new Error(`Error ${response.status}`);
      return (await response.json()) as { client_status: ClientFeedbackStatus | null; client_comment: string | null; rating: number | null };
    },
    [token, sessionToken, onReloadRequest]
  );

  async function submitDecision(decision: ClientFeedbackStatus, comment: string, rating: number | null) {
    if (!drawerFor) return;
    setSaving(true);
    try {
      const body = await submitFeedback(drawerFor, decision, comment || null, rating);
      if (body) {
        setData((current) => ({
          ...current,
          candidates: current.candidates.map((c) =>
            c.item_id === drawerFor.item_id
              ? { ...c, client_status: body.client_status, client_comment: body.client_comment, rating: body.rating }
              : c
          ),
        }));
        setSavedAt(new Date().toLocaleTimeString("es-ES"));
        setDrawerFor(null);
      }
    } catch (caught) {
      console.error(caught);
    } finally {
      setSaving(false);
    }
  }

  async function quickMove(candidate: PublicShortlistCandidate, target: ClientFeedbackStatus | "pending") {
    const newStatus = target === "pending" ? null : target;
    // Optimistic update
    setData((current) => ({
      ...current,
      candidates: current.candidates.map((c) =>
        c.item_id === candidate.item_id ? { ...c, client_status: newStatus } : c
      ),
    }));
    try {
      await submitFeedback(candidate, newStatus, candidate.client_comment, candidate.rating);
      setSavedAt(new Date().toLocaleTimeString("es-ES"));
    } catch (caught) {
      console.error(caught);
      // Revert
      setData((current) => ({
        ...current,
        candidates: current.candidates.map((c) =>
          c.item_id === candidate.item_id ? { ...c, client_status: candidate.client_status } : c
        ),
      }));
    }
  }

  const counts = useMemo(
    () => ({
      total: data.candidates.length,
      interview: data.candidates.filter(
        (c) => c.client_status === "interview_requested" || c.client_status === "want_interview"
      ).length,
      favorite: data.candidates.filter(
        (c) => c.client_status === "favorite" || c.client_status === "interested"
      ).length,
      review: data.candidates.filter((c) => c.client_status === "keep_in_review").length,
      rejected: data.candidates.filter(
        (c) => c.client_status === "rejected" || c.client_status === "not_interested"
      ).length,
      pending: data.candidates.filter((c) => c.client_status === null).length,
    }),
    [data.candidates]
  );

  const tabs: { id: TabId; label: string; show: boolean }[] = [
    { id: "shortlist", label: "Shortlist", show: true },
    { id: "comparison", label: "Comparación ejecutiva", show: data.show_comparison },
    { id: "decisions", label: "Decisiones", show: true },
    {
      id: "message",
      label: "Mensaje del consultor",
      show: Boolean(data.intro_message || data.message_to_client),
    },
  ];

  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <img src="/logo-talenscan.png" alt="TalentScan" className="h-10 w-auto" />
            <span className="text-xs text-brand-grayMid">·</span>
            <p className="text-[11px] uppercase tracking-wider text-brand-grayMid">
              Decision Room confidencial
            </p>
          </div>
          <p className="text-[11px] text-brand-grayMid">
            Para uso exclusivo de{" "}
            <strong className="text-brand-black">{data.mandate.client_name}</strong>
          </p>
        </div>
      </header>

      <section className="border-b border-slate-200 bg-gradient-to-br from-brand-blueSoft/40 via-white to-white">
        <div className="mx-auto max-w-5xl px-6 py-10">
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-700">
              <ShieldCheck className="h-3 w-3" />
              Acceso validado
            </span>
            {data.expires_at ? (
              <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-2.5 py-0.5 text-[11px] font-semibold text-brand-grayMid">
                <Clock className="h-3 w-3" />
                Acceso hasta {formatDate(data.expires_at)}
              </span>
            ) : null}
          </div>
          <p className="mt-4 text-[11px] font-semibold uppercase tracking-wider text-brand-blue">
            Decision Room
          </p>
          <h1 className="mt-1 text-3xl font-semibold tracking-tight text-brand-black">
            {data.mandate.target_role}
          </h1>
          <p className="mt-1 text-sm text-brand-grayMid">
            {data.mandate.client_name}
            {data.mandate.industry ? ` · ${data.mandate.industry}` : ""}
            {data.mandate.city || data.mandate.country
              ? ` · ${[data.mandate.city, data.mandate.country].filter(Boolean).join(", ")}`
              : ""}
          </p>

          {data.intro_message || data.message_to_client ? (
            <div className="mt-5 rounded-xl border border-brand-blue/20 bg-white p-4 shadow-soft">
              <div className="flex items-start gap-2">
                <Quote className="mt-0.5 h-4 w-4 shrink-0 text-brand-blue" />
                <p className="text-sm leading-relaxed text-brand-black whitespace-pre-line">
                  {data.intro_message || data.message_to_client}
                </p>
              </div>
            </div>
          ) : null}

          <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            <SummaryStat label="Candidatos" value={counts.total} />
            <SummaryStat label="Pendientes" value={counts.pending} accent="slate" />
            <SummaryStat label="Entrevistas" value={counts.interview} accent="blue" />
            <SummaryStat label="Favoritos" value={counts.favorite} accent="emerald" />
            <SummaryStat label="Descartados" value={counts.rejected} accent="rose" />
          </div>
        </div>
      </section>

      <section className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl gap-1 overflow-x-auto px-6">
          {tabs
            .filter((t) => t.show)
            .map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "border-b-2 px-3 py-3 text-sm font-medium transition",
                  activeTab === tab.id
                    ? "border-brand-blue text-brand-blue"
                    : "border-transparent text-brand-grayMid hover:text-brand-black"
                )}
              >
                {tab.label}
              </button>
            ))}
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-6 py-8">
        {activeTab === "shortlist" ? (
          <div className="space-y-5">
            {data.candidates.map((candidate, index) => (
              <CandidateCard
                key={candidate.item_id}
                candidate={candidate}
                rank={index + 1}
                view={data}
                token={token}
                sessionToken={sessionToken}
                onOpenDrawer={(c) => setDrawerFor(c)}
                onOpenPdf={(url, title) => setPdfModal({ url, title })}
              />
            ))}
          </div>
        ) : null}
        {activeTab === "comparison" ? (
          <ExecutiveComparisonTable view={data} onOpenDrawer={(c) => setDrawerFor(c)} />
        ) : null}
        {activeTab === "decisions" ? <DecisionsBoard view={data} onMove={quickMove} /> : null}
        {activeTab === "message" ? (
          <div className="space-y-4">
            {data.intro_message ? (
              <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
                <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-blue">
                  Mensaje del consultor
                </p>
                <p className="mt-2 whitespace-pre-line text-sm leading-relaxed text-brand-black">
                  {data.intro_message}
                </p>
              </article>
            ) : null}
            {data.message_to_client ? (
              <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
                <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-grayMid">
                  Mensaje adicional
                </p>
                <p className="mt-2 whitespace-pre-line text-sm leading-relaxed text-brand-black">
                  {data.message_to_client}
                </p>
              </article>
            ) : null}
          </div>
        ) : null}
      </section>

      {savedAt ? (
        <div className="fixed bottom-4 right-4 z-40 rounded-lg border border-emerald-200 bg-white px-3 py-2 text-xs text-emerald-700 shadow-soft">
          Decisión guardada a las {savedAt}.
        </div>
      ) : null}

      {drawerFor ? (
        <DecisionDrawer
          candidate={drawerFor}
          open
          onClose={() => setDrawerFor(null)}
          onSubmit={submitDecision}
          allowRating={data.allow_rating}
          allowComments={data.allow_comments}
          saving={saving}
          initialDecision={drawerFor.client_status}
        />
      ) : null}

      {pdfModal ? (
        <PdfViewerModal
          url={pdfModal.url}
          title={pdfModal.title}
          onClose={() => {
            URL.revokeObjectURL(pdfModal.url);
            setPdfModal(null);
          }}
        />
      ) : null}

      <footer className="border-t border-slate-200 bg-white px-6 py-6 text-center text-xs text-brand-grayMid">
        <p>
          Decision Room preparado por <strong className="text-brand-black">TalentScan</strong>. Tus
          decisiones quedan registradas y disponibles para el consultor responsable. La información
          de los candidatos es confidencial.
        </p>
      </footer>
    </main>
  );
}

function SummaryStat({
  label,
  value,
  accent,
}: {
  label: string;
  value: number;
  accent?: "blue" | "emerald" | "rose" | "slate";
}) {
  const palette: Record<string, string> = {
    blue: "border-brand-blue/20 bg-brand-blueSoft/40 text-brand-blue",
    emerald: "border-emerald-100 bg-emerald-50/60 text-emerald-700",
    rose: "border-rose-100 bg-rose-50/60 text-rose-700",
    slate: "border-slate-200 bg-slate-50 text-slate-700",
    default: "border-slate-200 bg-white text-brand-grayMid",
  };
  const cls = palette[accent || "default"] || palette.default;
  return (
    <div className={cn("rounded-xl border px-4 py-3", cls)}>
      <p className="text-[10px] font-semibold uppercase tracking-wider">{label}</p>
      <p className="mt-0.5 text-xl font-semibold text-brand-black">{value}</p>
    </div>
  );
}

// --- Root component -------------------------------------------------------

export function ClientShortlistPublicView({ token }: Props) {
  const [resolvedToken, setResolvedToken] = useState(token);
  const [response, setResponse] = useState<PublicShortlistResponse | null>(null);
  const [sessionToken, setSessionToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorCode, setErrorCode] = useState<number | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const match = window.location.pathname.match(/\/shortlist-cliente\/([^/]+)/);
    if (match && match[1] && match[1] !== "demo") {
      setResolvedToken(decodeURIComponent(match[1]));
    }
  }, []);

  useEffect(() => {
    setSessionToken(getStoredSession(resolvedToken));
  }, [resolvedToken]);

  const load = useMemo(
    () => async (currentSession: string | null) => {
      if (resolvedToken === "demo") {
        setLoading(false);
        setError(
          "Esta es la vista de ejemplo del Decision Room. TalentScan te enviará un link único para acceder al room real."
        );
        setErrorCode(0);
        return;
      }
      setLoading(true);
      setError(null);
      setErrorCode(null);
      try {
        const headers: Record<string, string> = {};
        if (currentSession) headers["X-Decision-Room-Session"] = currentSession;
        const res = await fetch(`${API_BASE_URL}/api/public/shortlists/${resolvedToken}`, {
          cache: "no-store",
          headers,
        });
        if (!res.ok) {
          setErrorCode(res.status);
          if (res.status === 404) {
            setError("Este Decision Room no existe o el link es incorrecto.");
          } else if (res.status === 410) {
            const detail = (await res.json())?.detail || "El link expiró.";
            setError(detail);
          } else {
            setError(`Error ${res.status} al cargar el Decision Room.`);
          }
          return;
        }
        const body = (await res.json()) as PublicShortlistResponse;
        setResponse(body);
      } catch (caught) {
        console.error(caught);
        setError("No fue posible conectar con TalentScan. Reintenta en unos minutos.");
      } finally {
        setLoading(false);
      }
    },
    [resolvedToken]
  );

  useEffect(() => {
    void load(sessionToken);
  }, [load, sessionToken]);

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50">
        <Loader2 className="h-6 w-6 animate-spin text-brand-blue" />
      </main>
    );
  }

  if (error) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
        <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-soft">
          <AlertCircle className="mx-auto h-8 w-8 text-amber-500" />
          <h1 className="mt-3 text-lg font-semibold text-brand-black">
            {errorCode === 0 ? "Decision Room de ejemplo" : "Decision Room no disponible"}
          </h1>
          <p className="mt-1 text-sm text-brand-grayMid">{error}</p>
        </div>
      </main>
    );
  }

  if (!response) return null;

  if (isGate(response)) {
    return (
      <AccessGate
        token={resolvedToken}
        title={response.title}
        mandate={response.mandate}
        emailHint={response.client_contact_email_hint}
        expiresAt={response.expires_at}
        onValidated={(value) => {
          storeSession(resolvedToken, value);
          setSessionToken(value);
        }}
      />
    );
  }

  return (
    <DecisionRoomBody
      token={resolvedToken}
      initialData={response}
      sessionToken={sessionToken}
      onReloadRequest={() => {
        storeSession(resolvedToken, null);
        setSessionToken(null);
      }}
    />
  );
}
