"use client";

import {
  ArrowRight,
  Archive,
  Briefcase,
  Building2,
  CalendarClock,
  CheckCircle2,
  Search,
  Trash2,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { SkeletonList } from "@/components/ui/skeleton";
import { apiFetch } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { CandidatePipelineItem } from "@/types/pipeline";
import type { SearchMandate } from "@/types/search-mandate";

type EnrichedMandate = SearchMandate & {
  pipeline_count?: number;
};

function statusTone(status: string | undefined): string {
  if (!status) return "bg-slate-100 text-brand-grayMid";
  const lower = status.toLowerCase();
  if (lower.includes("borrador")) return "bg-slate-100 text-brand-grayMid";
  if (lower.includes("activo")) return "bg-emerald-100 text-emerald-700";
  if (lower.includes("perfil")) return "bg-blue-100 text-blue-700";
  if (lower.includes("evaluacion") || lower.includes("evaluación")) return "bg-violet-100 text-violet-700";
  if (lower.includes("shortlist")) return "bg-amber-100 text-amber-700";
  if (lower.includes("cerrado")) return "bg-zinc-200 text-brand-grayMid";
  if (lower.includes("archivado")) return "bg-zinc-100 text-brand-grayMid";
  return "bg-slate-100 text-brand-grayMid";
}

function formatTargetDate(value: string | null): { label: string; tone: string } | null {
  if (!value) return null;
  const target = new Date(`${value}T00:00:00`);
  if (Number.isNaN(target.getTime())) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const diffDays = Math.round((target.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
  const dd = String(target.getDate()).padStart(2, "0");
  const mm = String(target.getMonth() + 1).padStart(2, "0");
  const yyyy = target.getFullYear();
  const formatted = `${dd}-${mm}-${yyyy}`;
  if (diffDays < 0) {
    return { label: `Vencido · ${formatted}`, tone: "bg-rose-100 text-rose-700" };
  }
  if (diffDays === 0) {
    return { label: `Hoy · ${formatted}`, tone: "bg-amber-100 text-amber-700" };
  }
  if (diffDays <= 14) {
    return {
      label: `${diffDays} día${diffDays === 1 ? "" : "s"} · ${formatted}`,
      tone: "bg-amber-100 text-amber-700",
    };
  }
  return { label: formatted, tone: "bg-slate-100 text-brand-grayMid" };
}

export function MandatoList() {
  const [mandates, setMandates] = useState<EnrichedMandate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [processingId, setProcessingId] = useState<number | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("Todos");

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase();
    return mandates.filter((mandate) => {
      if (statusFilter !== "Todos" && mandate.status !== statusFilter) return false;
      if (!term) return true;
      const haystack = [
        mandate.search_title,
        mandate.client_name,
        mandate.target_role,
        mandate.industry,
        mandate.country,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return haystack.includes(term);
    });
  }, [mandates, search, statusFilter]);

  const statusOptions = useMemo(() => {
    const set = new Set<string>();
    for (const m of mandates) if (m.status) set.add(m.status);
    return ["Todos", ...Array.from(set).sort()];
  }, [mandates]);

  async function loadMandates() {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch<SearchMandate[]>("/api/mandatos");
      const enriched = await Promise.all(
        data.map(async (mandate) => {
          try {
            const pipeline = await apiFetch<CandidatePipelineItem[]>(
              `/api/mandatos/${mandate.id}/pipeline`
            );
            return { ...mandate, pipeline_count: pipeline.length };
          } catch {
            return { ...mandate, pipeline_count: 0 };
          }
        })
      );
      setMandates(enriched);
    } catch (fetchError) {
      console.error(fetchError);
      setError("No fue posible cargar los mandatos.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadMandates();
  }, []);

  async function handleDelete(mandate: EnrichedMandate) {
    const confirmed = window.confirm(
      `¿Eliminar el mandato "${mandate.search_title}"? Esta acción no se puede deshacer.`
    );
    if (!confirmed) return;
    setProcessingId(mandate.id);
    setError(null);
    try {
      await apiFetch(`/api/mandatos/${mandate.id}`, { method: "DELETE" });
      setMandates((prev) => prev.filter((m) => m.id !== mandate.id));
      setFeedback(`Mandato "${mandate.search_title}" eliminado.`);
    } catch (deleteError) {
      console.error(deleteError);
      setError(
        "No fue posible eliminar el mandato. Si tiene pipeline activo, archívalo en su lugar."
      );
    } finally {
      setProcessingId(null);
    }
  }

  async function handleArchive(mandate: EnrichedMandate) {
    const confirmed = window.confirm(
      `¿Archivar el mandato "${mandate.search_title}"? Se conserva el pipeline y los candidatos.`
    );
    if (!confirmed) return;
    setProcessingId(mandate.id);
    setError(null);
    try {
      const updated = await apiFetch<SearchMandate>(`/api/mandatos/${mandate.id}/archivar`, {
        method: "POST",
      });
      setMandates((prev) => prev.map((m) => (m.id === mandate.id ? { ...m, ...updated } : m)));
      setFeedback(`Mandato "${mandate.search_title}" archivado.`);
    } catch (archiveError) {
      console.error(archiveError);
      setError("No fue posible archivar el mandato.");
    } finally {
      setProcessingId(null);
    }
  }

  if (loading) {
    return <SkeletonList rows={4} />;
  }

  if (error && mandates.length === 0) {
    return (
      <p className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
        {error}
      </p>
    );
  }

  if (!mandates.length) {
    return (
      <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50/40 px-4 py-10 text-center">
        <p className="text-sm font-semibold text-brand-black">Aún no hay mandatos creados</p>
        <p className="mt-1 text-xs text-brand-grayMid">
          Inicia con un nuevo mandato de búsqueda para empezar a evaluar candidatos.
        </p>
        <a
          href="/mandatos/nuevo"
          className="mt-4 inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-3.5 py-2 text-sm font-semibold text-white transition hover:bg-brand-blueDark"
        >
          Crear mandato de búsqueda
        </a>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {feedback ? (
        <div className="flex items-start gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{feedback}</span>
        </div>
      ) : null}
      {error ? (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {error}
        </div>
      ) : null}

      <div className="flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[220px]">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-brand-grayMid" />
          <input
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Buscar mandato, cliente, cargo o industria..."
            className="w-full rounded-lg border border-slate-200 bg-white py-2 pl-9 pr-3 text-sm text-brand-black placeholder:text-brand-grayMid focus:border-brand-blue focus:outline-none focus:ring-2 focus:ring-brand-blue/15"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.target.value)}
          className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-brand-grayMid focus:border-brand-blue focus:text-brand-black focus:outline-none"
        >
          {statusOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </div>

      {filtered.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50/40 px-4 py-8 text-center text-sm text-brand-grayMid">
          {search || statusFilter !== "Todos"
            ? "Sin mandatos que coincidan con los filtros activos."
            : "Sin mandatos."}
        </div>
      ) : null}

      {filtered.map((mandate) => {
        const targetDate = formatTargetDate(mandate.target_hire_date);
        const hasPipeline = (mandate.pipeline_count || 0) > 0;
        const isArchived = mandate.status === "Archivado";
        const isProcessing = processingId === mandate.id;
        return (
          <article
            key={mandate.id}
            className={cn(
              "group rounded-xl border bg-white p-4 transition hover:shadow-soft",
              isArchived ? "border-slate-200 opacity-60" : "border-slate-200 hover:border-brand-blue/40"
            )}
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="text-base font-semibold text-brand-black">{mandate.search_title}</h3>
                  {mandate.status && (
                    <span
                      className={cn(
                        "rounded-full px-2 py-0.5 text-[11px] font-medium",
                        statusTone(mandate.status)
                      )}
                    >
                      {mandate.status}
                    </span>
                  )}
                  {targetDate ? (
                    <span
                      className={cn(
                        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium",
                        targetDate.tone
                      )}
                    >
                      <CalendarClock className="h-3 w-3" />
                      {targetDate.label}
                    </span>
                  ) : null}
                </div>
                <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-brand-grayMid">
                  <span className="inline-flex items-center gap-1">
                    <Building2 className="h-3 w-3" />
                    {mandate.client_name}
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <Briefcase className="h-3 w-3" />
                    {mandate.target_role}
                  </span>
                  {mandate.country && <span>{mandate.country}</span>}
                  <span className="inline-flex items-center gap-1">
                    {mandate.pipeline_count ?? 0} candidato
                    {mandate.pipeline_count === 1 ? "" : "s"} en pipeline
                  </span>
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <a
                  href={`/mandatos/${mandate.id}`}
                  className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-brand-grayMid transition hover:border-brand-blue/40 hover:text-brand-blue"
                >
                  Ver detalle
                  <ArrowRight className="h-3.5 w-3.5" />
                </a>
                {!isArchived && hasPipeline ? (
                  <button
                    type="button"
                    onClick={() => handleArchive(mandate)}
                    disabled={isProcessing}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-brand-grayMid transition hover:border-amber-300 hover:text-amber-700 disabled:opacity-50"
                    title="Archivar mandato (conserva pipeline)"
                  >
                    <Archive className="h-3.5 w-3.5" />
                    Archivar
                  </button>
                ) : null}
                {!hasPipeline ? (
                  <button
                    type="button"
                    onClick={() => handleDelete(mandate)}
                    disabled={isProcessing}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-rose-200 bg-white px-3 py-1.5 text-sm font-medium text-rose-700 transition hover:bg-rose-50 disabled:opacity-50"
                    title="Eliminar mandato"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    Eliminar
                  </button>
                ) : null}
              </div>
            </div>
          </article>
        );
      })}
    </div>
  );
}
