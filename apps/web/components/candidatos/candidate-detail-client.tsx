"use client";

import {
  AlertTriangle,
  ArrowRight,
  Award,
  Briefcase,
  CalendarClock,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Clock,
  Coins,
  Compass,
  ExternalLink,
  GraduationCap,
  Languages,
  Linkedin,
  Mail,
  MapPin,
  Pencil,
  Phone,
  ShieldAlert,
  Sparkles,
  Star,
  Trash2,
  Wrench,
  X,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { apiFetch } from "@/lib/api";
import { useDynamicId } from "@/lib/use-dynamic-id";
import { cn } from "@/lib/utils";
import type { Candidate, CandidateProfile } from "@/types/candidate";
import type { CandidateEvaluation } from "@/types/evaluation";

type CandidateDetailClientProps = {
  candidateId?: string;
};

type RoleData = {
  title?: unknown;
  company?: unknown;
  start_date?: unknown;
  end_date?: unknown;
  duration_years?: unknown;
  responsibilities?: unknown;
  achievements?: unknown;
  tools_or_systems?: unknown;
  evidence?: unknown;
};

function categoryTone(category: string | undefined): {
  badge: string;
  text: string;
  ring: string;
} {
  const lower = (category || "").toLowerCase();
  if (lower.includes("muy alto"))
    return { badge: "bg-emerald-100 text-emerald-700", text: "text-emerald-700", ring: "ring-emerald-300" };
  if (lower.includes("buen"))
    return { badge: "bg-blue-100 text-blue-700", text: "text-blue-700", ring: "ring-blue-300" };
  if (lower.includes("parcial"))
    return { badge: "bg-amber-100 text-amber-700", text: "text-amber-700", ring: "ring-amber-300" };
  if (lower.includes("bajo"))
    return { badge: "bg-zinc-200 text-brand-grayMid", text: "text-brand-grayMid", ring: "ring-zinc-300" };
  return { badge: "bg-rose-100 text-rose-700", text: "text-rose-700", ring: "ring-rose-300" };
}

function getString(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

function getStringArray(value: unknown): string[] {
  return Array.isArray(value) ? (value as unknown[]).map((v) => String(v)) : [];
}

function CollapsibleSection({
  title,
  icon: Icon,
  defaultOpen = true,
  forceOpen,
  children,
}: {
  title: string;
  icon?: React.ComponentType<{ className?: string }>;
  defaultOpen?: boolean;
  forceOpen?: boolean | null;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);

  useEffect(() => {
    if (forceOpen !== null && forceOpen !== undefined) {
      setOpen(forceOpen);
    }
  }, [forceOpen]);

  return (
    <section className="rounded-2xl border border-slate-200 bg-white shadow-soft">
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        className="flex w-full items-center justify-between gap-3 px-5 py-4 text-left"
      >
        <span className="inline-flex items-center gap-2 text-sm font-semibold text-brand-black">
          {Icon ? <Icon className="h-4 w-4 text-brand-blue" /> : null}
          {title}
        </span>
        {open ? (
          <ChevronUp className="h-4 w-4 text-brand-grayMid" />
        ) : (
          <ChevronDown className="h-4 w-4 text-brand-grayMid" />
        )}
      </button>
      {open ? <div className="border-t border-slate-100 px-5 py-4">{children}</div> : null}
    </section>
  );
}

export function CandidateDetailClient({ candidateId: propId }: CandidateDetailClientProps = {}) {
  const pathId = useDynamicId("candidatos");
  const candidateId = pathId && pathId !== "demo" ? pathId : propId || pathId;

  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [profiles, setProfiles] = useState<CandidateProfile[]>([]);
  const [evaluations, setEvaluations] = useState<CandidateEvaluation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [editValue, setEditValue] = useState<Partial<Candidate>>({});
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [expandAll, setExpandAll] = useState<boolean | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const candidateValue =
          candidateId === "demo"
            ? (await apiFetch<Candidate[]>("/api/candidatos"))[0] || null
            : await apiFetch<Candidate>(`/api/candidatos/${candidateId}`);

        if (!candidateValue) {
          setCandidate(null);
          return;
        }

        const [profileList, evaluationList] = await Promise.all([
          apiFetch<CandidateProfile[]>(`/api/candidatos/${candidateValue.id}/perfiles`),
          apiFetch<CandidateEvaluation[]>(`/api/candidatos/${candidateValue.id}/evaluaciones`),
        ]);

        setCandidate(candidateValue);
        setProfiles(profileList);
        setEvaluations(evaluationList);
      } catch (requestError) {
        console.error(requestError);
        setError("No fue posible cargar el detalle del candidato.");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [candidateId]);

  function startEdit() {
    if (!candidate) return;
    setEditValue({
      full_name: candidate.full_name,
      current_position: candidate.current_position,
      current_company: candidate.current_company,
      email: candidate.email,
      phone: candidate.phone,
      linkedin_url: candidate.linkedin_url,
      country: candidate.country,
    });
    setEditing(true);
    setFeedback(null);
  }

  async function saveEdit() {
    if (!candidate) return;
    setSaving(true);
    try {
      const payload = {
        full_name: editValue.full_name?.trim() || candidate.full_name,
        current_position: editValue.current_position?.trim() || null,
        current_company: editValue.current_company?.trim() || null,
        email: editValue.email?.trim() || null,
        phone: editValue.phone?.trim() || null,
        linkedin_url: editValue.linkedin_url?.trim() || null,
        country: editValue.country?.trim() || null,
      };
      const updated = await apiFetch<Candidate>(`/api/candidatos/${candidate.id}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      setCandidate(updated);
      setEditing(false);
      setFeedback("Datos del candidato actualizados.");
    } catch (saveError) {
      console.error(saveError);
      setError("No fue posible actualizar el candidato.");
    } finally {
      setSaving(false);
    }
  }

  async function deleteCandidate() {
    if (!candidate) return;
    const confirmed = window.confirm(
      `¿Eliminar a ${candidate.full_name}? Se borra el candidato, su CV, perfil y evaluaciones. Esta acción no se puede deshacer.`
    );
    if (!confirmed) return;
    setDeleting(true);
    try {
      await apiFetch(`/api/candidatos/${candidate.id}`, { method: "DELETE" });
      window.location.href = "/candidatos";
    } catch (deleteError) {
      console.error(deleteError);
      setError("No fue posible eliminar el candidato.");
      setDeleting(false);
    }
  }

  const profile = profiles[0];
  const latestEvaluation = evaluations[0];

  const strengths = useMemo(
    () => getStringArray(latestEvaluation?.strengths),
    [latestEvaluation]
  );
  const weaknesses = useMemo(
    () => getStringArray(latestEvaluation?.weaknesses),
    [latestEvaluation]
  );
  const risks = useMemo(() => getStringArray(latestEvaluation?.risks), [latestEvaluation]);
  const evidence = useMemo(
    () => getStringArray(latestEvaluation?.supporting_evidence),
    [latestEvaluation]
  );
  const interviewQs = useMemo(
    () => getStringArray(latestEvaluation?.interview_questions),
    [latestEvaluation]
  );
  const criticalGaps = useMemo(() => {
    if (!latestEvaluation) return [] as string[];
    const arr = Array.isArray(latestEvaluation.critical_gaps)
      ? (latestEvaluation.critical_gaps as Array<Record<string, unknown>>)
      : [];
    return arr.map(
      (item) => getString(item.requirement) || getString(item.reason) || "Brecha crítica"
    );
  }, [latestEvaluation]);

  const dimensions = useMemo(() => {
    if (!latestEvaluation) return [] as Array<Record<string, unknown>>;
    return Array.isArray(latestEvaluation.dimension_scores)
      ? (latestEvaluation.dimension_scores as Array<Record<string, unknown>>)
      : [];
  }, [latestEvaluation]);

  const roles = useMemo<RoleData[]>(() => {
    if (!profile) return [];
    return Array.isArray(profile.roles) ? (profile.roles as RoleData[]) : [];
  }, [profile]);

  if (loading) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center text-sm text-brand-grayMid">
        Cargando candidato...
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

  if (!candidate) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center">
        <p className="text-sm font-semibold text-brand-black">No hay candidato disponible</p>
        <p className="mt-1 text-xs text-brand-grayMid">
          Sube un CV o agrega una URL de LinkedIn desde un mandato.
        </p>
      </div>
    );
  }

  const initials = candidate.full_name
    .split(/\s+/)
    .map((p) => p[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase();

  const score = latestEvaluation?.total_score;
  const cat = categoryTone(latestEvaluation?.score_category);

  return (
    <div className="space-y-5">
      {feedback ? (
        <div className="flex items-start gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{feedback}</span>
        </div>
      ) : null}

      {/* Header card */}
      <header className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-brand-blueSoft text-xl font-semibold text-brand-blue">
              {initials || "—"}
            </div>
            <div className="min-w-0">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-blue">
                Candidato
              </p>
              <h2 className="mt-0.5 flex flex-wrap items-center gap-2 text-2xl font-semibold tracking-tight text-brand-black">
                {candidate.full_name}
                {profile?.inferred_seniority ? (
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-brand-grayMid">
                    {profile.inferred_seniority}
                  </span>
                ) : null}
                {latestEvaluation ? (
                  <span className={cn("rounded-full px-2 py-0.5 text-[11px] font-medium", cat.badge)}>
                    {latestEvaluation.score_category}
                  </span>
                ) : null}
              </h2>
              {candidate.current_position || candidate.current_company ? (
                <p className="mt-1 text-sm text-brand-grayMid">
                  {candidate.current_position}
                  {candidate.current_position && candidate.current_company ? " · " : ""}
                  {candidate.current_company}
                </p>
              ) : null}
              <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-brand-grayMid">
                {candidate.email ? (
                  <span className="inline-flex items-center gap-1.5">
                    <Mail className="h-3.5 w-3.5" />
                    {candidate.email}
                  </span>
                ) : null}
                {candidate.phone ? (
                  <span className="inline-flex items-center gap-1.5">
                    <Phone className="h-3.5 w-3.5" />
                    {candidate.phone}
                  </span>
                ) : null}
                {candidate.country ? (
                  <span className="inline-flex items-center gap-1.5">
                    <MapPin className="h-3.5 w-3.5" />
                    {candidate.country}
                  </span>
                ) : null}
                {candidate.linkedin_url ? (
                  <a
                    href={candidate.linkedin_url}
                    target="_blank"
                    rel="noreferrer noopener"
                    className="inline-flex items-center gap-1.5 text-brand-blue hover:underline"
                  >
                    <Linkedin className="h-3.5 w-3.5" />
                    LinkedIn
                    <ExternalLink className="h-3 w-3" />
                  </a>
                ) : null}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setExpandAll((prev) => (prev === true ? false : true))}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-brand-grayMid transition hover:border-brand-blue/40 hover:text-brand-blue"
            >
              {expandAll === false ? "Expandir todo" : "Contraer todo"}
            </button>
            <button
              type="button"
              onClick={startEdit}
              disabled={editing}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-brand-grayMid transition hover:border-brand-blue/40 hover:text-brand-black disabled:opacity-50"
            >
              <Pencil className="h-3.5 w-3.5" />
              Editar
            </button>
            <button
              type="button"
              onClick={deleteCandidate}
              disabled={deleting}
              className="inline-flex items-center gap-1.5 rounded-lg border border-rose-200 bg-white px-3 py-1.5 text-sm font-medium text-rose-700 transition hover:bg-rose-50 disabled:opacity-50"
            >
              <Trash2 className="h-3.5 w-3.5" />
              {deleting ? "Eliminando..." : "Eliminar"}
            </button>
          </div>
        </div>

        {/* KPIs */}
        <div className="mt-5 grid gap-3 md:grid-cols-4">
          <KpiTile
            label="Experiencia"
            value={
              profile?.total_years_experience !== null && profile?.total_years_experience !== undefined
                ? `${profile.total_years_experience}+ años`
                : "Pendiente"
            }
            icon={Clock}
          />
          <KpiTile
            label="Calce preliminar"
            value={latestEvaluation?.score_category || "Pendiente"}
            icon={Sparkles}
            tone={cat.text}
          />
          <KpiTile label="Disponibilidad" value="Pendiente" icon={CalendarClock} tone="text-amber-700" />
          <KpiTile label="Renta esperada" value="Pendiente" icon={Coins} tone="text-amber-700" />
        </div>

        {/* Edit form */}
        {editing ? (
          <div className="mt-5 grid gap-3 rounded-xl border border-slate-200 bg-slate-50/40 p-4 md:grid-cols-2">
            <EditField
              label="Nombre completo"
              value={editValue.full_name || ""}
              onChange={(v) => setEditValue({ ...editValue, full_name: v })}
            />
            <EditField
              label="Cargo actual"
              value={editValue.current_position || ""}
              onChange={(v) => setEditValue({ ...editValue, current_position: v })}
            />
            <EditField
              label="Empresa actual"
              value={editValue.current_company || ""}
              onChange={(v) => setEditValue({ ...editValue, current_company: v })}
            />
            <EditField
              label="País"
              value={editValue.country || ""}
              onChange={(v) => setEditValue({ ...editValue, country: v })}
            />
            <EditField
              label="Email"
              type="email"
              value={editValue.email || ""}
              onChange={(v) => setEditValue({ ...editValue, email: v })}
            />
            <EditField
              label="Teléfono"
              value={editValue.phone || ""}
              onChange={(v) => setEditValue({ ...editValue, phone: v })}
            />
            <div className="md:col-span-2">
              <EditField
                label="LinkedIn URL"
                placeholder="https://www.linkedin.com/in/..."
                value={editValue.linkedin_url || ""}
                onChange={(v) => setEditValue({ ...editValue, linkedin_url: v })}
              />
            </div>
            <div className="md:col-span-2 flex gap-2">
              <button
                type="button"
                onClick={saveEdit}
                disabled={saving}
                className="inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-3.5 py-2 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-blueDark disabled:opacity-50"
              >
                <CheckCircle2 className="h-3.5 w-3.5" />
                {saving ? "Guardando..." : "Guardar cambios"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setEditing(false);
                  setEditValue({});
                }}
                className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-sm font-medium text-brand-grayMid transition hover:border-brand-blue/40 hover:text-brand-black"
              >
                <X className="h-3.5 w-3.5" />
                Cancelar
              </button>
            </div>
          </div>
        ) : null}
      </header>

      {/* Recomendación + Calce */}
      {latestEvaluation ? (
        <div className="grid gap-5 lg:grid-cols-[1fr_2fr]">
          <article className="rounded-2xl border border-brand-blue/30 bg-brand-blueSoft/40 p-5 shadow-soft">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-blue">
              Recomendación TalentScan
            </p>
            <h3 className="mt-1 text-lg font-semibold text-brand-black">
              {latestEvaluation.recommendation || "Revisar evaluación"}
            </h3>
            <p className="mt-2 text-sm text-brand-grayMid">
              {latestEvaluation.final_verdict || "Sin veredicto registrado."}
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              <a
                href={`/evaluaciones/${latestEvaluation.id}`}
                className="inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-3.5 py-2 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-blueDark"
              >
                Ver evaluación completa
                <ArrowRight className="h-3.5 w-3.5" />
              </a>
            </div>
          </article>

          <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
            <p className="text-sm font-semibold text-brand-black">Calce con el perfil buscado</p>
            <div className="mt-4 grid gap-3 md:grid-cols-3">
              <CalceBlock
                title="Fortalezas"
                icon={Star}
                tone="emerald"
                items={strengths.length ? strengths : ["Sin fortalezas destacadas"]}
              />
              <CalceBlock
                title="Brechas"
                icon={AlertTriangle}
                tone="rose"
                items={criticalGaps.length ? criticalGaps : ["Sin brechas críticas"]}
              />
              <CalceBlock
                title="Evidencia"
                icon={Sparkles}
                tone="blue"
                items={evidence.length ? evidence : ["Sin evidencia textual del CV"]}
              />
            </div>

            {dimensions.length > 0 ? (
              <div className="mt-5 overflow-hidden rounded-xl border border-slate-200">
                <table className="w-full text-sm">
                  <thead className="bg-slate-50 text-left text-[11px] font-semibold uppercase tracking-wider text-brand-grayMid">
                    <tr>
                      <th className="px-3 py-2">Criterio</th>
                      <th className="px-3 py-2 text-center">Evaluación</th>
                      <th className="px-3 py-2">Evidencia</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {dimensions.map((dim, index) => {
                      const dimName = getString(dim.dimension, `Dimensión ${index + 1}`);
                      const evidenceLevel = getString(dim.evidence_level, "—");
                      const rationale = getString(dim.rationale, "—");
                      const dimScore = Number(dim.score || 0);
                      const dimMax = Number(dim.max_score || 0);
                      const ratio = dimMax > 0 ? dimScore / dimMax : 0;
                      const evalLabel =
                        ratio >= 0.85
                          ? "Alta"
                          : ratio >= 0.6
                            ? "Media-Alta"
                            : ratio >= 0.4
                              ? "Media"
                              : "Baja";
                      return (
                        <tr key={index} className="hover:bg-slate-50/40">
                          <td className="px-3 py-2 font-medium text-brand-black">{dimName}</td>
                          <td className="px-3 py-2 text-center text-xs text-brand-grayMid">
                            {evalLabel} · {dimScore}/{dimMax}
                          </td>
                          <td className="px-3 py-2 text-xs text-brand-grayMid">
                            {evidenceLevel} · {rationale}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : null}
          </article>
        </div>
      ) : null}

      {/* Resumen ejecutivo */}
      {latestEvaluation?.executive_summary ? (
        <CollapsibleSection title="Resumen ejecutivo" icon={Compass} forceOpen={expandAll}>
          <p className="text-sm leading-relaxed text-brand-grayMid">
            {latestEvaluation.executive_summary}
          </p>
        </CollapsibleSection>
      ) : null}

      {/* Experiencia profesional */}
      {roles.length > 0 ? (
        <CollapsibleSection
          title={`Experiencia profesional relevante (${roles.length})`}
          icon={Briefcase}
          forceOpen={expandAll}
        >
          <div className="space-y-3">
            {roles.map((role, index) => {
              const title = getString(role.title, "Rol");
              const company = getString(role.company);
              const start = getString(role.start_date);
              const end = getString(role.end_date) || "Actualidad";
              const responsibilities = getStringArray(role.responsibilities);
              const achievements = getStringArray(role.achievements);
              const tools = getStringArray(role.tools_or_systems);
              return (
                <details
                  key={index}
                  open={index === 0}
                  className="group rounded-xl border border-slate-200 bg-slate-50/40 p-4 open:bg-white"
                >
                  <summary className="flex cursor-pointer items-start justify-between gap-3 list-none">
                    <div>
                      <p className="text-sm font-semibold text-brand-black">{title}</p>
                      <p className="text-xs text-brand-grayMid">
                        {company}
                        {start ? ` · ${start} - ${end}` : ""}
                      </p>
                    </div>
                    <ChevronDown className="h-4 w-4 shrink-0 text-brand-grayMid transition group-open:rotate-180" />
                  </summary>
                  {responsibilities.length > 0 ? (
                    <div className="mt-3">
                      <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-grayMid">
                        Responsabilidades
                      </p>
                      <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-brand-black">
                        {responsibilities.map((item, idx) => (
                          <li key={idx}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                  {achievements.length > 0 ? (
                    <div className="mt-3">
                      <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-grayMid">
                        Logros
                      </p>
                      <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-brand-black">
                        {achievements.map((item, idx) => (
                          <li key={idx}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                  {tools.length > 0 ? (
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      {tools.map((tool) => (
                        <span
                          key={tool}
                          className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-brand-grayMid"
                        >
                          {tool}
                        </span>
                      ))}
                    </div>
                  ) : null}
                </details>
              );
            })}
          </div>
        </CollapsibleSection>
      ) : null}

      {/* Logros y Formación. Si Formación es chica, va en línea con Competencias.
          Si ambas tienen contenido, aparecen una al lado de otra. */}
      {profile && profile.achievements.length > 0 ? (
        <CollapsibleSection title="Logros evidenciados" icon={Award} forceOpen={expandAll}>
          <ul className="grid gap-2 text-sm text-brand-black sm:grid-cols-2">
            {profile.achievements.slice(0, 12).map((item, index) => (
              <li key={index} className="flex items-start gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </CollapsibleSection>
      ) : null}

      {/* Competencias / Formación / Validaciones / Próximo paso */}
      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
        {profile && profile.education.length > 0 ? (
          <CollapsibleSection title="Formación" icon={GraduationCap} forceOpen={expandAll}>
            <ul className="space-y-2 text-sm text-brand-black">
              {profile.education.slice(0, 10).map((item, index) => (
                <li key={index} className="flex items-start gap-2">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-blue" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </CollapsibleSection>
        ) : null}

        {profile && (profile.tools.length > 0 || profile.industries.length > 0 || profile.certifications.length > 0) ? (
          <CollapsibleSection title="Competencias y dominios" icon={Wrench} forceOpen={expandAll}>
            {profile.tools.length > 0 ? (
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-grayMid">
                  Herramientas
                </p>
                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  {profile.tools.map((tool) => (
                    <span
                      key={tool}
                      className="rounded-full bg-brand-blueSoft px-2 py-0.5 text-[11px] font-medium text-brand-blue"
                    >
                      {tool}
                    </span>
                  ))}
                </div>
              </div>
            ) : null}
            {profile.industries.length > 0 ? (
              <div className="mt-3">
                <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-grayMid">
                  Industrias
                </p>
                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  {profile.industries.map((ind) => (
                    <span
                      key={ind}
                      className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-brand-grayMid"
                    >
                      {ind}
                    </span>
                  ))}
                </div>
              </div>
            ) : null}
            {profile.languages.length > 0 ? (
              <div className="mt-3">
                <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-grayMid">
                  <Languages className="mr-1 inline-block h-3 w-3" />
                  Idiomas
                </p>
                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  {profile.languages.map((lang) => (
                    <span
                      key={lang}
                      className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-brand-grayMid"
                    >
                      {lang}
                    </span>
                  ))}
                </div>
              </div>
            ) : null}
            {profile.certifications.length > 0 ? (
              <div className="mt-3">
                <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-grayMid">
                  Certificaciones
                </p>
                <ul className="mt-1.5 list-disc space-y-0.5 pl-5 text-xs text-brand-black">
                  {profile.certifications.map((cert, i) => (
                    <li key={i}>{cert}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </CollapsibleSection>
        ) : null}

        {risks.length > 0 || criticalGaps.length > 0 ? (
          <CollapsibleSection title="Validaciones pendientes" icon={ShieldAlert} forceOpen={expandAll}>
            <ul className="space-y-2 text-sm text-brand-black">
              {[...risks, ...criticalGaps].slice(0, 10).map((item, index) => (
                <li
                  key={index}
                  className="flex items-start justify-between gap-2 rounded-lg border border-slate-100 bg-slate-50/40 px-2.5 py-2"
                >
                  <span>{item}</span>
                  <span className="shrink-0 rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-medium text-amber-700">
                    Alta
                  </span>
                </li>
              ))}
            </ul>
          </CollapsibleSection>
        ) : null}

        {latestEvaluation ? (
          <CollapsibleSection title="Próximo paso recomendado" icon={ArrowRight} forceOpen={expandAll}>
            <p className="text-sm font-semibold text-brand-black">
              {latestEvaluation.recommendation}
            </p>
            {interviewQs.length > 0 ? (
              <div className="mt-3">
                <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-grayMid">
                  Riesgos / Preguntas
                </p>
                <ul className="mt-1.5 list-disc space-y-1 pl-5 text-xs text-brand-black">
                  {interviewQs.slice(0, 5).map((q, i) => (
                    <li key={i}>{q}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            <a
              href={`/evaluaciones/${latestEvaluation.id}`}
              className="mt-4 inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-3.5 py-2 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-blueDark"
            >
              Ver evaluación 360 completa
              <ArrowRight className="h-3.5 w-3.5" />
            </a>
          </CollapsibleSection>
        ) : null}
      </div>

      {/* Evaluaciones list */}
      {evaluations.length > 0 ? (
        <CollapsibleSection
          title={`Evaluaciones 360 asociadas (${evaluations.length})`}
          icon={Sparkles}
          defaultOpen={false}
          forceOpen={expandAll}
        >
          <ul className="space-y-2">
            {evaluations.map((evaluation) => {
              const evCat = categoryTone(evaluation.score_category);
              return (
                <li
                  key={evaluation.id}
                  className="flex items-center justify-between gap-3 rounded-xl border border-slate-200 p-3 hover:border-brand-blue/40"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-slate-50 text-base font-semibold text-brand-black">
                      {evaluation.total_score}
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-brand-black">{evaluation.score_category}</p>
                      <p className="text-xs text-brand-grayMid">{evaluation.recommendation}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={cn(
                        "rounded-full px-2 py-0.5 text-[11px] font-medium",
                        evCat.badge
                      )}
                    >
                      {evaluation.score_category}
                    </span>
                    <a
                      href={`/evaluaciones/${evaluation.id}`}
                      className="text-xs font-medium text-brand-blue hover:underline"
                    >
                      Ver detalle →
                    </a>
                  </div>
                </li>
              );
            })}
          </ul>
        </CollapsibleSection>
      ) : null}

      {/* Información no evidenciada */}
      {profile && profile.missing_information.length > 0 ? (
        <CollapsibleSection
          title="Información no evidenciada en el CV"
          icon={AlertTriangle}
          defaultOpen={false}
          forceOpen={expandAll}
        >
          <ul className="list-disc space-y-1 pl-5 text-xs text-amber-800">
            {profile.missing_information.map((info, index) => (
              <li key={index}>{info}</li>
            ))}
          </ul>
        </CollapsibleSection>
      ) : null}
    </div>
  );
}

function KpiTile({
  label,
  value,
  icon: Icon,
  tone,
}: {
  label: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  tone?: string;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50/40 p-3">
      <div className="flex items-center gap-2">
        <Icon className="h-3.5 w-3.5 text-brand-grayMid" />
        <p className="text-[10px] font-semibold uppercase tracking-wider text-brand-grayMid">
          {label}
        </p>
      </div>
      <p className={cn("mt-1.5 text-base font-semibold text-brand-black", tone)}>{value}</p>
    </div>
  );
}

function CalceBlock({
  title,
  icon: Icon,
  items,
  tone,
}: {
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  items: string[];
  tone: "emerald" | "rose" | "blue";
}) {
  const styles = {
    emerald: {
      header: "text-emerald-700",
      bullet: "bg-emerald-500",
      bg: "bg-emerald-50/40 border-emerald-100",
    },
    rose: {
      header: "text-rose-700",
      bullet: "bg-rose-500",
      bg: "bg-rose-50/40 border-rose-100",
    },
    blue: {
      header: "text-brand-blue",
      bullet: "bg-brand-blue",
      bg: "bg-brand-blueSoft/40 border-brand-blue/20",
    },
  }[tone];

  return (
    <div className={cn("rounded-xl border p-3", styles.bg)}>
      <p className={cn("inline-flex items-center gap-1.5 text-xs font-semibold", styles.header)}>
        <Icon className="h-3.5 w-3.5" />
        {title}
      </p>
      <ul className="mt-2 space-y-1.5 text-xs text-brand-black">
        {items.slice(0, 5).map((item, index) => (
          <li key={index} className="flex items-start gap-1.5">
            <span className={cn("mt-1.5 h-1 w-1 shrink-0 rounded-full", styles.bullet)} />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function EditField({
  label,
  value,
  onChange,
  type = "text",
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  placeholder?: string;
}) {
  return (
    <div>
      <label className="block text-[11px] font-semibold uppercase tracking-wider text-brand-grayMid">
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-brand-black placeholder:text-brand-grayMid focus:border-brand-blue focus:outline-none focus:ring-2 focus:ring-brand-blue/15"
      />
    </div>
  );
}
