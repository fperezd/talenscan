"use client";

import {
  AlertTriangle,
  Download,
  FileBarChart,
  FileText,
  Sparkles,
} from "lucide-react";
import { useEffect, useState } from "react";

import { SkeletonList } from "@/components/ui/skeleton";
import { API_BASE_URL, apiFetch } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { Candidate } from "@/types/candidate";
import type { CandidateEvaluation } from "@/types/evaluation";

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

export function ReportCenter() {
  const [items, setItems] = useState<EnrichedEvaluation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<string | null>(null);

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
        const enriched = evaluations.map((evaluation) => ({
          ...evaluation,
          candidate: candidateMap.get(evaluation.candidate_id),
        }));
        setItems(enriched);
      } catch (requestError) {
        console.error(requestError);
        setError("No fue posible cargar evaluaciones para reportes.");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  async function handleDownload(id: number, format: "word" | "pdf", candidateName: string) {
    const key = `${id}-${format}`;
    setDownloading(key);
    setError(null);
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/evaluaciones/${id}/reportes/${format}`,
        { method: "POST" }
      );
      if (!response.ok) throw new Error("Download failed");
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      const safeName = candidateName.replace(/[^a-zA-Z0-9-_ñÑáéíóúÁÉÍÓÚ ]/g, "").trim();
      const extension = format === "word" ? "docx" : "pdf";
      link.download = `TalentScan-${safeName || `evaluacion-${id}`}.${extension}`;
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

  if (loading) {
    return <SkeletonList rows={3} />;
  }

  if (error && items.length === 0) {
    return (
      <p className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
        {error}
      </p>
    );
  }

  if (!items.length) {
    return (
      <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50/40 px-4 py-10 text-center">
        <FileBarChart className="mx-auto h-7 w-7 text-brand-grayMid" />
        <p className="mt-3 text-sm font-semibold text-brand-black">
          Aún no hay evaluaciones para descargar
        </p>
        <p className="mt-1 text-xs text-brand-grayMid">
          Genera una Evaluación 360 desde un mandato y vuelve aquí para descargar Word/PDF.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {error ? (
        <p className="flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          {error}
        </p>
      ) : null}

      {items.map((item) => {
        const isDownloadingWord = downloading === `${item.id}-word`;
        const isDownloadingPdf = downloading === `${item.id}-pdf`;
        const candidateName = item.candidate?.full_name || `Candidato #${item.candidate_id}`;
        return (
          <article
            key={item.id}
            className="rounded-xl border border-slate-200 bg-white p-4 transition hover:border-brand-blue/40"
          >
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-start gap-3">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-brand-blueSoft text-brand-blue">
                  <Sparkles className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-brand-black">{candidateName}</p>
                  <div className="mt-0.5 flex flex-wrap items-center gap-2 text-xs text-brand-grayMid">
                    <span>Score {item.total_score}/100</span>
                    <span>·</span>
                    <span
                      className={cn(
                        "rounded-full px-2 py-0.5 text-[11px] font-medium",
                        scoreCategoryTone(item.score_category)
                      )}
                    >
                      {item.score_category}
                    </span>
                  </div>
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => handleDownload(item.id, "word", candidateName)}
                  disabled={downloading !== null}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-sm font-medium text-brand-grayMid transition hover:border-brand-blue/40 hover:text-brand-black disabled:opacity-50"
                >
                  <Download className="h-3.5 w-3.5" />
                  {isDownloadingWord ? "Descargando..." : "Word"}
                </button>
                <button
                  type="button"
                  onClick={() => handleDownload(item.id, "pdf", candidateName)}
                  disabled={downloading !== null}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-3.5 py-2 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-blueDark disabled:opacity-50"
                >
                  <FileText className="h-3.5 w-3.5" />
                  {isDownloadingPdf ? "Descargando..." : "PDF"}
                </button>
              </div>
            </div>
          </article>
        );
      })}
    </div>
  );
}
