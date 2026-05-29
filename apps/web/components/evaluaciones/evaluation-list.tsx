"use client";

import { AlertTriangle, ArrowRight, Search, Sparkles } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { SkeletonList } from "@/components/ui/skeleton";
import { apiFetch } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { CandidateEvaluation } from "@/types/evaluation";
import type { Candidate } from "@/types/candidate";

type EnrichedEvaluation = CandidateEvaluation & {
  candidate?: Candidate;
};

function scoreCategoryTone(category: string | undefined): string {
  const lower = (category || "").toLowerCase();
  if (lower.includes("muy alto")) return "bg-emerald-100 text-emerald-700";
  if (lower.includes("buen")) return "bg-blue-100 text-blue-700";
  if (lower.includes("parcial")) return "bg-amber-100 text-amber-700";
  if (lower.includes("bajo")) return "bg-zinc-200 text-brand-grayMid";
  return "bg-rose-100 text-rose-700";
}

function scoreRingTone(score: number): string {
  if (score >= 85) return "ring-emerald-300 text-emerald-700";
  if (score >= 70) return "ring-blue-300 text-blue-700";
  if (score >= 55) return "ring-amber-300 text-amber-700";
  if (score >= 40) return "ring-zinc-300 text-brand-grayMid";
  return "ring-rose-300 text-rose-700";
}

export function EvaluationList() {
  const [items, setItems] = useState<EnrichedEvaluation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>("Todas");

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase();
    return items.filter((evaluation) => {
      if (categoryFilter !== "Todas" && evaluation.score_category !== categoryFilter) return false;
      if (!term) return true;
      const haystack = [
        evaluation.candidate?.full_name,
        evaluation.candidate?.current_position,
        evaluation.candidate?.current_company,
        evaluation.score_category,
        evaluation.recommendation,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return haystack.includes(term);
    });
  }, [items, search, categoryFilter]);

  const categoryOptions = useMemo(() => {
    const set = new Set<string>();
    for (const e of items) if (e.score_category) set.add(e.score_category);
    return ["Todas", ...Array.from(set).sort()];
  }, [items]);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [evaluations, candidates] = await Promise.all([
          apiFetch<CandidateEvaluation[]>("/api/evaluaciones"),
          apiFetch<Candidate[]>("/api/candidatos"),
        ]);
        const candidateMap = new Map(candidates.map((c) => [c.id, c]));
        const enriched: EnrichedEvaluation[] = evaluations.map((evaluation) => ({
          ...evaluation,
          candidate: candidateMap.get(evaluation.candidate_id),
        }));
        setItems(enriched);
      } catch (requestError) {
        console.error(requestError);
        setError("No fue posible cargar evaluaciones.");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  if (loading) {
    return <SkeletonList rows={3} />;
  }

  if (error) {
    return (
      <p className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
        {error}
      </p>
    );
  }

  if (!items.length) {
    return (
      <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50/40 px-4 py-10 text-center">
        <Sparkles className="mx-auto h-7 w-7 text-brand-grayMid" />
        <p className="mt-3 text-sm font-semibold text-brand-black">
          Aún no hay evaluaciones 360 generadas
        </p>
        <p className="mt-1 text-xs text-brand-grayMid">
          Sube un CV desde un mandato para generar la primera evaluación.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[220px]">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-brand-grayMid" />
          <input
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Buscar por candidato, cargo o recomendación..."
            className="w-full rounded-lg border border-slate-200 bg-white py-2 pl-9 pr-3 text-sm text-brand-black placeholder:text-brand-grayMid focus:border-brand-blue focus:outline-none focus:ring-2 focus:ring-brand-blue/15"
          />
        </div>
        <select
          value={categoryFilter}
          onChange={(event) => setCategoryFilter(event.target.value)}
          className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-brand-grayMid focus:border-brand-blue focus:text-brand-black focus:outline-none"
        >
          {categoryOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </div>

      {filtered.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50/40 px-4 py-8 text-center text-sm text-brand-grayMid">
          Sin evaluaciones que coincidan con los filtros.
        </div>
      ) : null}

      {filtered.map((evaluation) => {
        const hasCriticalGaps = Array.isArray(evaluation.critical_gaps) && evaluation.critical_gaps.length > 0;
        return (
          <a
            key={evaluation.id}
            href={`/evaluaciones/${evaluation.id}`}
            className="group flex items-start gap-4 rounded-xl border border-slate-200 bg-white p-4 transition hover:border-brand-blue/40 hover:shadow-soft"
          >
            <div
              className={cn(
                "flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-white text-base font-semibold ring-2",
                scoreRingTone(evaluation.total_score)
              )}
            >
              {evaluation.total_score}
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <p className="text-sm font-semibold text-brand-black">
                  {evaluation.candidate?.full_name || `Candidato #${evaluation.candidate_id}`}
                </p>
                <span
                  className={cn(
                    "rounded-full px-2 py-0.5 text-[11px] font-medium",
                    scoreCategoryTone(evaluation.score_category)
                  )}
                >
                  {evaluation.score_category}
                </span>
                {hasCriticalGaps ? (
                  <span className="inline-flex items-center gap-1 rounded-full bg-rose-100 px-2 py-0.5 text-[11px] font-medium text-rose-700">
                    <AlertTriangle className="h-3 w-3" />
                    {(evaluation.critical_gaps as unknown[]).length} brecha
                    {(evaluation.critical_gaps as unknown[]).length === 1 ? "" : "s"}
                  </span>
                ) : null}
              </div>
              <p className="mt-1 line-clamp-2 text-xs text-brand-grayMid">
                {evaluation.executive_summary || evaluation.recommendation}
              </p>
              {evaluation.candidate?.current_position ? (
                <p className="mt-1 text-[11px] text-brand-grayMid">
                  {evaluation.candidate.current_position}
                  {evaluation.candidate.current_company
                    ? ` · ${evaluation.candidate.current_company}`
                    : ""}
                </p>
              ) : null}
            </div>
            <ArrowRight className="mt-3 h-4 w-4 shrink-0 text-brand-grayMid transition group-hover:translate-x-0.5 group-hover:text-brand-blue" />
          </a>
        );
      })}
    </div>
  );
}
