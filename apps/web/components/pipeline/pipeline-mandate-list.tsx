"use client";

import { ArrowRight, KanbanSquare, Users } from "lucide-react";
import { useEffect, useState } from "react";

import { SkeletonList } from "@/components/ui/skeleton";
import { apiFetch } from "@/lib/api";
import type { CandidatePipelineItem } from "@/types/pipeline";
import type { SearchMandate } from "@/types/search-mandate";

type MandateWithCount = SearchMandate & {
  pipeline_count?: number;
};

export function PipelineMandateList() {
  const [items, setItems] = useState<MandateWithCount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const mandates = await apiFetch<SearchMandate[]>("/api/mandatos");
        const enriched = await Promise.all(
          mandates.map(async (mandate) => {
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
        setItems(enriched);
      } catch (requestError) {
        console.error(requestError);
        setError("No fue posible cargar mandatos para pipeline.");
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
        <KanbanSquare className="mx-auto h-7 w-7 text-brand-grayMid" />
        <p className="mt-3 text-sm font-semibold text-brand-black">No hay pipelines disponibles</p>
        <p className="mt-1 text-xs text-brand-grayMid">
          Crea un mandato y carga candidatos para que aparezca su pipeline.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <article
          key={item.id}
          className="group rounded-xl border border-slate-200 bg-white p-4 transition hover:border-brand-blue/40 hover:shadow-soft"
        >
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="min-w-0 flex-1">
              <h3 className="text-base font-semibold text-brand-black">{item.search_title}</h3>
              <p className="mt-1 text-sm text-brand-grayMid">
                {item.client_name} · {item.target_role}
              </p>
              <p className="mt-1 inline-flex items-center gap-1 text-xs text-brand-grayMid">
                <Users className="h-3 w-3" />
                {item.pipeline_count ?? 0} candidato
                {item.pipeline_count === 1 ? "" : "s"} en pipeline
              </p>
            </div>
            <a
              href={`/mandatos/${item.id}/pipeline`}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-brand-grayMid transition group-hover:border-brand-blue/40 group-hover:text-brand-blue"
            >
              Abrir pipeline
              <ArrowRight className="h-3.5 w-3.5" />
            </a>
          </div>
        </article>
      ))}
    </div>
  );
}
