"use client";

import { Loader2, Sparkles, Users, X } from "lucide-react";
import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/api";
import { cn } from "@/lib/utils";
import type {
  MapCandidate,
  TalentMarketMap as TalentMarketMapType,
} from "@/types/talent-market-map";

const selectClass =
  "w-full rounded-md border border-slate-200 bg-white px-2 py-1 text-xs text-brand-black focus:border-brand-blue focus:outline-none";

/**
 * Drawer lateral para asignar candidatos del mandato a un segmento, empresa
 * target o cargo equivalente del mapa. Las asignaciones se persisten como
 * overrides; el match automático por empresa se muestra como referencia.
 */
export function CandidatesSidePanel({
  map,
  onMap,
  onClose,
}: {
  map: TalentMarketMapType;
  onMap: (m: TalentMarketMapType) => void;
  onClose: () => void;
}) {
  const [candidates, setCandidates] = useState<MapCandidate[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await apiFetch<MapCandidate[]>(
          `/api/talent-market-maps/${map.id}/candidates`
        );
        setCandidates(data);
      } catch (caught) {
        console.error(caught);
        setError("No fue posible cargar los candidatos del mandato.");
      }
    }
    void load();
  }, [map.id]);

  async function assign(
    candidate: MapCandidate,
    patch: Partial<
      Pick<MapCandidate, "segment_id" | "target_company_id" | "equivalent_role_id">
    >
  ) {
    const next: MapCandidate = { ...candidate, ...patch };
    setBusyId(candidate.candidate_id);
    try {
      const hasAssignment =
        next.segment_id !== null ||
        next.target_company_id !== null ||
        next.equivalent_role_id !== null;
      const updatedMap = await apiFetch<TalentMarketMapType>(
        `/api/talent-market-maps/${map.id}/candidates/${candidate.candidate_id}/assign`,
        hasAssignment
          ? {
              method: "POST",
              body: JSON.stringify({
                segment_id: next.segment_id,
                target_company_id: next.target_company_id,
                equivalent_role_id: next.equivalent_role_id,
              }),
            }
          : { method: "DELETE" }
      );
      onMap(updatedMap);
      setCandidates((current) =>
        (current || []).map((c) => (c.candidate_id === candidate.candidate_id ? next : c))
      );
    } catch (caught) {
      console.error(caught);
      window.alert("No fue posible guardar la asignación.");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-brand-black/40">
      <div className="flex h-full w-full max-w-xl flex-col bg-white shadow-2xl">
        <div className="flex items-start justify-between gap-2 border-b border-slate-100 p-5">
          <div>
            <p className="inline-flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-brand-blue">
              <Users className="h-3.5 w-3.5" />
              Asignar candidatos
            </p>
            <h3 className="mt-0.5 text-lg font-semibold text-brand-black">
              Conecta candidatos al mapa de mercado
            </h3>
            <p className="mt-1 text-xs text-brand-grayMid">
              Asigna cada candidato del pipeline a un segmento, empresa o cargo equivalente.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="inline-flex h-8 w-8 items-center justify-center rounded-md text-brand-grayMid hover:bg-slate-100"
            aria-label="Cerrar"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-5">
          {error ? (
            <p className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {error}
            </p>
          ) : candidates === null ? (
            <div className="flex h-40 items-center justify-center">
              <Loader2 className="h-5 w-5 animate-spin text-brand-blue" />
            </div>
          ) : candidates.length === 0 ? (
            <p className="rounded-2xl border border-dashed border-slate-200 px-4 py-10 text-center text-sm text-brand-grayMid">
              No hay candidatos en el pipeline de este mandato todavía.
            </p>
          ) : (
            <ul className="space-y-3">
              {candidates.map((cand) => (
                <li
                  key={cand.candidate_id}
                  className="rounded-xl border border-slate-200 bg-white p-4 shadow-soft"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-brand-black">{cand.full_name}</p>
                      {cand.current_position || cand.current_company ? (
                        <p className="text-xs text-brand-grayMid">
                          {[cand.current_position, cand.current_company].filter(Boolean).join(" · ")}
                        </p>
                      ) : null}
                    </div>
                    <div className="flex items-center gap-2">
                      {cand.evaluation_score !== null ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-brand-blueSoft px-2 py-0.5 text-[10px] font-semibold text-brand-blue">
                          <Sparkles className="h-2.5 w-2.5" />
                          {cand.evaluation_score}
                        </span>
                      ) : null}
                      {busyId === cand.candidate_id ? (
                        <Loader2 className="h-4 w-4 animate-spin text-brand-blue" />
                      ) : null}
                    </div>
                  </div>

                  {cand.auto_company_id && cand.target_company_id === null ? (
                    <p className="mt-2 rounded-md bg-emerald-50 px-2 py-1 text-[11px] text-emerald-700">
                      Match automático con empresa target por su empresa actual.
                    </p>
                  ) : null}

                  <div className="mt-3 grid gap-2 sm:grid-cols-3">
                    <label className="block">
                      <span className="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-brand-grayMid">
                        Segmento
                      </span>
                      <select
                        value={cand.segment_id ?? ""}
                        onChange={(e) =>
                          assign(cand, { segment_id: e.target.value ? Number(e.target.value) : null })
                        }
                        className={selectClass}
                      >
                        <option value="">—</option>
                        {map.segments.map((s) => (
                          <option key={s.id} value={s.id}>
                            {s.name}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="block">
                      <span className="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-brand-grayMid">
                        Empresa
                      </span>
                      <select
                        value={cand.target_company_id ?? ""}
                        onChange={(e) =>
                          assign(cand, {
                            target_company_id: e.target.value ? Number(e.target.value) : null,
                          })
                        }
                        className={selectClass}
                      >
                        <option value="">—</option>
                        {map.companies.map((c) => (
                          <option key={c.id} value={c.id}>
                            {c.name}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="block">
                      <span className="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-brand-grayMid">
                        Cargo equivalente
                      </span>
                      <select
                        value={cand.equivalent_role_id ?? ""}
                        onChange={(e) =>
                          assign(cand, {
                            equivalent_role_id: e.target.value ? Number(e.target.value) : null,
                          })
                        }
                        className={selectClass}
                      >
                        <option value="">—</option>
                        {map.equivalent_roles.map((r) => (
                          <option key={r.id} value={r.id}>
                            {r.title}
                          </option>
                        ))}
                      </select>
                    </label>
                  </div>

                  {cand.segment_id || cand.target_company_id || cand.equivalent_role_id ? (
                    <button
                      type="button"
                      onClick={() =>
                        assign(cand, {
                          segment_id: null,
                          target_company_id: null,
                          equivalent_role_id: null,
                        })
                      }
                      className={cn(
                        "mt-2 text-[11px] font-medium text-brand-grayMid underline-offset-2 hover:text-rose-600 hover:underline"
                      )}
                    >
                      Quitar asignación
                    </button>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
