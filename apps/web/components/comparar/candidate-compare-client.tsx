"use client";

import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useDroppable,
  useDraggable,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import {
  AlertTriangle,
  Briefcase,
  CheckCircle2,
  Copy,
  DoorOpen,
  Download,
  ExternalLink,
  Eye,
  FileText,
  GripVertical,
  Lightbulb,
  Link2,
  Loader2,
  Plus,
  Target,
  Trash2,
  TrendingUp,
  Users2,
  X,
} from "lucide-react";

import { AddToRoomModal } from "@/components/decision-room/add-to-room-modal";
import { useEffect, useMemo, useState } from "react";

import { API_BASE_URL, apiFetch } from "@/lib/api";
import { useDynamicId } from "@/lib/use-dynamic-id";
import { cn } from "@/lib/utils";
import type { Candidate } from "@/types/candidate";
import type { CandidateEvaluation } from "@/types/evaluation";
import {
  PIPELINE_STAGE_LABELS,
  type CandidatePipelineItem,
  type PipelineStage,
} from "@/types/pipeline";
import type { ClientShortlist } from "@/types/shortlist";

type CandidateCompareClientProps = {
  mandateId?: string;
};

type EnrichedItem = CandidatePipelineItem & {
  candidate?: Candidate;
  evaluation?: CandidateEvaluation;
};

type AiAssessment = {
  talent_thesis?: string;
  differentiation?: string;
  strengths_detailed?: Array<{ title?: string; detail?: string }>;
  critical_gaps_detailed?: Array<{ requirement?: string }>;
  opportunities?: Array<{ title?: string; detail?: string }>;
  transferable_skills?: string[];
  career_trajectory?: {
    tenure_stability?: string;
    progression?: string;
    current_phase?: string;
  };
};

const MAX_COMPARE = 5;

function categoryTone(category: string | undefined) {
  const lower = (category || "").toLowerCase();
  if (lower.includes("muy alto"))
    return { badge: "bg-emerald-100 text-emerald-700", text: "text-emerald-700", ring: "ring-emerald-300", bar: "bg-emerald-400" };
  if (lower.includes("buen"))
    return { badge: "bg-blue-100 text-blue-700", text: "text-blue-700", ring: "ring-blue-300", bar: "bg-blue-400" };
  if (lower.includes("parcial"))
    return { badge: "bg-amber-100 text-amber-700", text: "text-amber-700", ring: "ring-amber-300", bar: "bg-amber-400" };
  if (lower.includes("bajo"))
    return { badge: "bg-zinc-200 text-brand-grayMid", text: "text-brand-grayMid", ring: "ring-zinc-300", bar: "bg-zinc-400" };
  if (lower.includes("no recomendado") || lower.includes("descart"))
    return { badge: "bg-rose-100 text-rose-700", text: "text-rose-700", ring: "ring-rose-300", bar: "bg-rose-400" };
  return { badge: "bg-slate-100 text-brand-grayMid", text: "text-brand-grayMid", ring: "ring-slate-300", bar: "bg-slate-300" };
}

function aiOf(evaluation: CandidateEvaluation | undefined): AiAssessment {
  if (!evaluation || !evaluation.evaluation_json) return {};
  const raw = (evaluation.evaluation_json as Record<string, unknown>).ai_assessment;
  return (raw && typeof raw === "object" ? raw : {}) as AiAssessment;
}

function dimensionsOf(evaluation: CandidateEvaluation | undefined): Array<Record<string, unknown>> {
  if (!evaluation) return [];
  return Array.isArray(evaluation.dimension_scores)
    ? (evaluation.dimension_scores as Array<Record<string, unknown>>)
    : [];
}

function PoolCandidateCard({ item }: { item: EnrichedItem }) {
  const sortable = useDraggable({ id: `pool-${item.id}`, data: { itemId: item.id, source: "pool" } });
  const { attributes, listeners, setNodeRef, transform, isDragging } = sortable;
  const score = item.evaluation?.total_score;
  const category = item.evaluation?.score_category;
  const tone = categoryTone(category);
  const name = item.candidate?.full_name || `Candidato #${item.candidate_id}`;
  const role = item.candidate?.current_position || "Cargo no informado";
  const company = item.candidate?.current_company || "Empresa no informada";

  const style: React.CSSProperties = transform
    ? {
        transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
        opacity: isDragging ? 0.3 : 1,
      }
    : { opacity: isDragging ? 0.3 : 1 };

  return (
    <article
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className={cn(
        "flex cursor-grab items-start gap-2 rounded-xl border border-slate-200 bg-white p-3 shadow-soft transition hover:border-brand-blue/40 hover:shadow-md active:cursor-grabbing",
        item.is_priority && "ring-1 ring-amber-300"
      )}
    >
      <GripVertical className="mt-0.5 h-4 w-4 shrink-0 text-slate-300" />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-semibold text-brand-black">{name}</p>
        <p className="mt-0.5 flex items-center gap-1 truncate text-xs text-brand-grayMid">
          <Briefcase className="h-3 w-3 shrink-0" />
          <span className="truncate">{role}</span>
        </p>
        <p className="mt-0.5 truncate text-xs text-brand-grayMid">{company}</p>
        <div className="mt-1.5 flex items-center gap-1.5">
          <span className="rounded-full bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-brand-grayMid">
            {PIPELINE_STAGE_LABELS[item.stage as PipelineStage] || item.stage}
          </span>
          {category ? (
            <span className={cn("rounded-full px-1.5 py-0.5 text-[10px] font-medium", tone.badge)}>
              {category}
            </span>
          ) : null}
        </div>
      </div>
      <div
        className={cn(
          "flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-white text-sm font-semibold ring-2",
          tone.ring,
          tone.text
        )}
        title={category || "Sin evaluación"}
      >
        {score ?? "—"}
      </div>
    </article>
  );
}

function CompareDropZone({
  children,
  hasItems,
}: {
  children: React.ReactNode;
  hasItems: boolean;
}) {
  const { isOver, setNodeRef } = useDroppable({ id: "compare-zone" });
  return (
    <div
      ref={setNodeRef}
      className={cn(
        "rounded-2xl border-2 border-dashed p-4 transition",
        isOver
          ? "border-brand-blue/60 bg-brand-blue/5"
          : hasItems
            ? "border-slate-200 bg-white"
            : "border-slate-300 bg-slate-50/50"
      )}
    >
      {children}
    </div>
  );
}

export function CandidateCompareClient({ mandateId: propId }: CandidateCompareClientProps = {}) {
  const pathId = useDynamicId("mandatos");
  const mandateId = pathId && pathId !== "demo" ? pathId : propId || pathId;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [items, setItems] = useState<EnrichedItem[]>([]);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [search, setSearch] = useState("");
  const [previewLoading, setPreviewLoading] = useState(false);
  const [downloadLoading, setDownloadLoading] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [shareModalOpen, setShareModalOpen] = useState(false);
  const [addToRoomOpen, setAddToRoomOpen] = useState(false);
  const [shareTitle, setShareTitle] = useState("Shortlist Talenscan");
  const [shareMessage, setShareMessage] = useState(
    "Hola, te comparto el shortlist de candidatos para esta posición. Por favor revisa cada perfil y márcalo según tu interés. Quedo atento a tu feedback."
  );
  const [shareShowScores, setShareShowScores] = useState(false);
  const [shareExpiresAt, setShareExpiresAt] = useState("");
  const [shareLoading, setShareLoading] = useState(false);
  const [shareResult, setShareResult] = useState<ClientShortlist | null>(null);
  const [shareCopied, setShareCopied] = useState(false);

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 4 } }));

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [pipelineItems, candidates, evaluations] = await Promise.all([
          apiFetch<CandidatePipelineItem[]>(`/api/mandatos/${mandateId}/pipeline`),
          apiFetch<Candidate[]>("/api/candidatos"),
          apiFetch<CandidateEvaluation[]>("/api/evaluaciones"),
        ]);
        const candidateMap = new Map(candidates.map((c) => [c.id, c]));
        const evaluationMap = new Map(evaluations.map((e) => [e.id, e]));
        const enriched: EnrichedItem[] = pipelineItems.map((item) => ({
          ...item,
          candidate: candidateMap.get(item.candidate_id),
          evaluation: item.evaluation_id ? evaluationMap.get(item.evaluation_id) : undefined,
        }));
        setItems(enriched);
      } catch (requestError) {
        console.error(requestError);
        setError("No fue posible cargar el pipeline.");
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, [mandateId]);

  const itemById = useMemo(() => {
    const m = new Map<number, EnrichedItem>();
    items.forEach((it) => m.set(it.id, it));
    return m;
  }, [items]);

  const selectedItems = useMemo(
    () => selectedIds.map((id) => itemById.get(id)).filter(Boolean) as EnrichedItem[],
    [selectedIds, itemById]
  );

  const poolItems = useMemo(() => {
    const lower = search.trim().toLowerCase();
    return items
      .filter((it) => !selectedIds.includes(it.id))
      .filter((it) => {
        if (!lower) return true;
        const haystack = [
          it.candidate?.full_name,
          it.candidate?.current_position,
          it.candidate?.current_company,
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();
        return haystack.includes(lower);
      })
      .sort((a, b) => (b.evaluation?.total_score ?? -1) - (a.evaluation?.total_score ?? -1));
  }, [items, selectedIds, search]);

  function addToCompare(itemId: number) {
    setSelectedIds((prev) => {
      if (prev.includes(itemId)) return prev;
      if (prev.length >= MAX_COMPARE) return prev;
      return [...prev, itemId];
    });
  }

  function removeFromCompare(itemId: number) {
    setSelectedIds((prev) => prev.filter((id) => id !== itemId));
  }

  function clearCompare() {
    setSelectedIds([]);
  }

  async function fetchComparisonPdf(): Promise<Blob | null> {
    const evaluationIds = selectedItems
      .map((item) => item.evaluation_id)
      .filter((id): id is number => typeof id === "number");
    if (evaluationIds.length === 0) {
      setError("Los candidatos seleccionados no tienen evaluación generada.");
      return null;
    }
    const response = await fetch(
      `${API_BASE_URL}/api/mandatos/${mandateId}/reportes/comparacion`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ evaluation_ids: evaluationIds }),
      }
    );
    if (!response.ok) {
      throw new Error(`Error ${response.status}`);
    }
    return await response.blob();
  }

  async function openPreview() {
    setPreviewLoading(true);
    setError(null);
    try {
      const blob = await fetchComparisonPdf();
      if (!blob) return;
      const url = URL.createObjectURL(blob);
      setPreviewUrl(url);
    } catch (previewError) {
      console.error(previewError);
      setError("No fue posible generar la vista previa del comparativo.");
    } finally {
      setPreviewLoading(false);
    }
  }

  function closePreview() {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
  }

  function openShareModal() {
    setShareResult(null);
    setShareCopied(false);
    setShareModalOpen(true);
  }

  function closeShareModal() {
    setShareModalOpen(false);
    setShareResult(null);
    setShareCopied(false);
  }

  async function createShareLink() {
    const evaluationIds = selectedItems
      .map((item) => item.evaluation_id)
      .filter((id): id is number => typeof id === "number");
    if (evaluationIds.length === 0) {
      setError("Los candidatos seleccionados no tienen evaluación generada.");
      return;
    }
    setShareLoading(true);
    setError(null);
    try {
      const body: Record<string, unknown> = {
        title: shareTitle.trim() || "Shortlist Talenscan",
        message_to_client: shareMessage,
        show_scores: shareShowScores,
        evaluation_ids: evaluationIds,
      };
      if (shareExpiresAt) {
        body.expires_at = new Date(shareExpiresAt).toISOString();
      }
      const result = await apiFetch<ClientShortlist>(
        `/api/mandatos/${mandateId}/shortlists`,
        {
          method: "POST",
          body: JSON.stringify(body),
        }
      );
      setShareResult(result);
    } catch (shareError) {
      console.error(shareError);
      setError("No fue posible generar el link del shortlist.");
    } finally {
      setShareLoading(false);
    }
  }

  async function copyShareLink() {
    if (!shareResult) return;
    const url = `${window.location.origin}/shortlist-cliente/${shareResult.public_token}`;
    try {
      await navigator.clipboard.writeText(url);
      setShareCopied(true);
      setTimeout(() => setShareCopied(false), 2200);
    } catch {
      // fallback: select-only
    }
  }

  async function downloadComparison() {
    setDownloadLoading(true);
    setError(null);
    try {
      const blob = await fetchComparisonPdf();
      if (!blob) return;
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `Comparativo_${selectedItems.length}_candidatos.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (downloadError) {
      console.error(downloadError);
      setError("No fue posible descargar el comparativo.");
    } finally {
      setDownloadLoading(false);
    }
  }

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  function handleDragStart(event: DragStartEvent) {
    const data = event.active.data.current as { itemId?: number } | undefined;
    if (data?.itemId !== undefined) setActiveId(data.itemId);
  }

  function handleDragEnd(event: DragEndEvent) {
    const data = event.active.data.current as { itemId?: number } | undefined;
    setActiveId(null);
    if (event.over?.id === "compare-zone" && data?.itemId !== undefined) {
      addToCompare(data.itemId);
    }
  }

  // --- Dimensiones agregadas (unión de todas las que aparecen en las evaluaciones seleccionadas) ---
  const allDimensions = useMemo(() => {
    const order: string[] = [];
    const maxByName = new Map<string, number>();
    selectedItems.forEach((item) => {
      dimensionsOf(item.evaluation).forEach((dim) => {
        const name = String(dim.dimension || "");
        if (!name) return;
        if (!order.includes(name)) order.push(name);
        const max = Number(dim.max_score || 0);
        if (!maxByName.has(name) || max > (maxByName.get(name) || 0)) {
          maxByName.set(name, max);
        }
      });
    });
    return { order, maxByName };
  }, [selectedItems]);

  // Para cada dimensión, identificar el mejor candidato (mayor score)
  const bestPerDimension = useMemo(() => {
    const result = new Map<string, number>(); // dimension → item.id
    allDimensions.order.forEach((dim) => {
      let bestScore = -Infinity;
      let bestItemId: number | null = null;
      selectedItems.forEach((item) => {
        const found = dimensionsOf(item.evaluation).find((d) => d.dimension === dim);
        const score = found ? Number(found.score || 0) : 0;
        if (score > bestScore) {
          bestScore = score;
          bestItemId = item.id;
        }
      });
      if (bestItemId !== null) result.set(dim, bestItemId);
    });
    return result;
  }, [selectedItems, allDimensions.order]);

  // Identificar el mejor score total
  const topScorer = useMemo(() => {
    if (selectedItems.length === 0) return null;
    return selectedItems.reduce((best, item) =>
      (item.evaluation?.total_score ?? -1) > (best.evaluation?.total_score ?? -1) ? item : best
    , selectedItems[0]);
  }, [selectedItems]);

  if (loading) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center text-sm text-brand-grayMid">
        Cargando candidatos del mandato...
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

  if (items.length === 0) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center">
        <p className="text-sm font-semibold text-brand-black">Pipeline vacío</p>
        <p className="mt-1 text-xs text-brand-grayMid">
          Sube CVs o agrega candidatos desde LinkedIn en "Evaluar candidatos" antes de comparar.
        </p>
      </div>
    );
  }

  const activeItem = activeId !== null ? itemById.get(activeId) : null;

  return (
    <DndContext sensors={sensors} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
      <div className="grid gap-5 lg:grid-cols-[320px_1fr]">
        {/* --- Pool de candidatos del pipeline --- */}
        <aside className="rounded-2xl border border-slate-200 bg-white p-4 shadow-soft">
          <header className="mb-3 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-brand-black">Candidatos del pipeline</h3>
              <p className="text-[11px] text-brand-grayMid">Arrastra al panel para comparar.</p>
            </div>
            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-brand-grayMid">
              {poolItems.length}
            </span>
          </header>
          <input
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Buscar por nombre, cargo, empresa..."
            className="mb-3 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-brand-black placeholder:text-brand-grayMid focus:border-brand-blue focus:outline-none focus:ring-2 focus:ring-brand-blue/15"
          />
          <div className="max-h-[calc(100vh-280px)] space-y-2 overflow-y-auto pr-1">
            {poolItems.length === 0 ? (
              <p className="rounded-lg border border-dashed border-slate-300 px-3 py-6 text-center text-xs text-brand-grayMid">
                No hay candidatos disponibles para agregar.
              </p>
            ) : (
              poolItems.map((item) => <PoolCandidateCard key={item.id} item={item} />)
            )}
          </div>
        </aside>

        {/* --- Zona de comparación --- */}
        <section>
          <header className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Users2 className="h-4 w-4 text-brand-blue" />
              <h3 className="text-sm font-semibold text-brand-black">
                Comparativo {selectedItems.length}/{MAX_COMPARE}
              </h3>
              {selectedItems.length === MAX_COMPARE ? (
                <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-medium text-amber-700">
                  Máximo alcanzado
                </span>
              ) : null}
            </div>
            {selectedItems.length > 0 ? (
              <div className="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  onClick={() => setAddToRoomOpen(true)}
                  disabled={previewLoading || downloadLoading}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-brand-blue/40 bg-brand-blueSoft px-3 py-1.5 text-xs font-semibold text-brand-blue transition hover:bg-brand-blueSoft/80 disabled:opacity-50"
                >
                  <DoorOpen className="h-3 w-3" />
                  Crear Decision Room
                </button>
                <button
                  type="button"
                  onClick={openPreview}
                  disabled={previewLoading || downloadLoading}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-brand-grayMid transition hover:border-brand-blue/40 hover:text-brand-black disabled:opacity-50"
                >
                  {previewLoading ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : (
                    <Eye className="h-3 w-3" />
                  )}
                  {previewLoading ? "Generando..." : "Vista previa PDF"}
                </button>
                <button
                  type="button"
                  onClick={downloadComparison}
                  disabled={previewLoading || downloadLoading}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-3 py-1.5 text-xs font-semibold text-white shadow-soft transition hover:bg-brand-blueDark disabled:opacity-50"
                >
                  {downloadLoading ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : (
                    <Download className="h-3 w-3" />
                  )}
                  {downloadLoading ? "Descargando..." : "Descargar PDF"}
                </button>
                <button
                  type="button"
                  onClick={clearCompare}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-brand-grayMid transition hover:border-rose-300 hover:text-rose-700"
                >
                  <Trash2 className="h-3 w-3" />
                  Limpiar
                </button>
              </div>
            ) : null}
          </header>

          <CompareDropZone hasItems={selectedItems.length > 0}>
            {selectedItems.length === 0 ? (
              <div className="flex flex-col items-center justify-center gap-2 px-4 py-16 text-center">
                <Plus className="h-8 w-8 text-slate-300" />
                <p className="text-sm font-semibold text-brand-black">
                  Arrastra hasta {MAX_COMPARE} candidatos
                </p>
                <p className="max-w-md text-xs text-brand-grayMid">
                  Cada candidato se compara dimensión por dimensión. El mejor por dimensión se
                  destaca en verde para facilitar la decisión.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Header con cards de cada candidato */}
                <div
                  className="grid gap-3"
                  style={{
                    gridTemplateColumns: `repeat(${selectedItems.length}, minmax(0, 1fr))`,
                  }}
                >
                  {selectedItems.map((item) => {
                    const isTop = topScorer?.id === item.id && selectedItems.length > 1;
                    const tone = categoryTone(item.evaluation?.score_category);
                    const ai = aiOf(item.evaluation);
                    const name = item.candidate?.full_name || `Candidato #${item.candidate_id}`;
                    return (
                      <article
                        key={item.id}
                        className={cn(
                          "relative rounded-xl border bg-white p-4 shadow-soft",
                          isTop ? "border-emerald-300 ring-2 ring-emerald-200" : "border-slate-200"
                        )}
                      >
                        {isTop ? (
                          <span className="absolute -top-2 left-3 inline-flex items-center gap-1 rounded-full bg-emerald-600 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-white">
                            <Target className="h-3 w-3" />
                            Top score
                          </span>
                        ) : null}
                        <button
                          type="button"
                          onClick={() => removeFromCompare(item.id)}
                          className="absolute right-2 top-2 inline-flex h-6 w-6 items-center justify-center rounded-full text-brand-grayMid transition hover:bg-rose-50 hover:text-rose-700"
                          aria-label="Quitar de comparación"
                        >
                          <X className="h-3.5 w-3.5" />
                        </button>
                        <div className="flex items-center gap-3">
                          <div
                            className={cn(
                              "flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-white text-base font-semibold ring-2",
                              tone.ring,
                              tone.text
                            )}
                          >
                            {item.evaluation?.total_score ?? "—"}
                          </div>
                          <div className="min-w-0">
                            <a
                              href={`/candidatos/${item.candidate_id}`}
                              className="truncate text-sm font-semibold text-brand-black hover:text-brand-blue hover:underline"
                            >
                              {name}
                            </a>
                            <p className="truncate text-xs text-brand-grayMid">
                              {item.candidate?.current_position || "—"}
                            </p>
                            <p className="truncate text-xs text-brand-grayMid">
                              {item.candidate?.current_company || "—"}
                            </p>
                          </div>
                        </div>
                        {item.evaluation?.score_category ? (
                          <span
                            className={cn(
                              "mt-3 inline-flex rounded-full px-2 py-0.5 text-[10px] font-medium",
                              tone.badge
                            )}
                          >
                            {item.evaluation.score_category}
                          </span>
                        ) : null}
                        {ai.talent_thesis ? (
                          <p className="mt-2 line-clamp-3 text-[11px] text-brand-grayMid">
                            {ai.talent_thesis}
                          </p>
                        ) : null}
                      </article>
                    );
                  })}
                </div>

                {/* Tabla comparativa de dimensiones */}
                <div className="overflow-hidden rounded-xl border border-slate-200">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-50 text-left text-[10px] font-semibold uppercase tracking-wider text-brand-grayMid">
                      <tr>
                        <th className="w-1/4 px-3 py-2.5">Dimensión</th>
                        {selectedItems.map((item) => (
                          <th key={item.id} className="px-3 py-2.5 text-center">
                            {item.candidate?.full_name?.split(" ")[0] || `#${item.candidate_id}`}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {/* Score total */}
                      <tr className="bg-slate-50/40">
                        <td className="px-3 py-3 font-semibold text-brand-black">
                          Score total
                        </td>
                        {selectedItems.map((item) => {
                          const isTop = topScorer?.id === item.id && selectedItems.length > 1;
                          return (
                            <td key={item.id} className="px-3 py-3 text-center">
                              <span
                                className={cn(
                                  "inline-flex h-8 min-w-[60px] items-center justify-center rounded-lg px-2 text-sm font-bold",
                                  isTop
                                    ? "bg-emerald-100 text-emerald-700"
                                    : "bg-white text-brand-black ring-1 ring-slate-200"
                                )}
                              >
                                {item.evaluation?.total_score ?? "—"} / 100
                              </span>
                            </td>
                          );
                        })}
                      </tr>

                      {allDimensions.order.map((dim) => {
                        const max = allDimensions.maxByName.get(dim) || 10;
                        const bestId = bestPerDimension.get(dim);
                        return (
                          <tr key={dim} className="hover:bg-slate-50/40">
                            <td className="px-3 py-2.5 text-xs font-medium text-brand-black">
                              {dim}
                            </td>
                            {selectedItems.map((item) => {
                              const found = dimensionsOf(item.evaluation).find(
                                (d) => d.dimension === dim
                              );
                              const score = found ? Number(found.score || 0) : null;
                              const ratio = score !== null && max > 0 ? score / max : 0;
                              const isBest = bestId === item.id && selectedItems.length > 1;
                              const barTone =
                                ratio >= 0.85
                                  ? "bg-emerald-400"
                                  : ratio >= 0.6
                                    ? "bg-blue-400"
                                    : ratio >= 0.4
                                      ? "bg-amber-400"
                                      : "bg-rose-400";
                              return (
                                <td
                                  key={item.id}
                                  className={cn(
                                    "px-3 py-2.5 text-center",
                                    isBest && "bg-emerald-50/60"
                                  )}
                                >
                                  {score === null ? (
                                    <span className="text-xs text-brand-grayMid">—</span>
                                  ) : (
                                    <div className="inline-flex flex-col items-center gap-1">
                                      <span
                                        className={cn(
                                          "text-xs font-semibold",
                                          isBest ? "text-emerald-700" : "text-brand-black"
                                        )}
                                      >
                                        {score} / {max}
                                      </span>
                                      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-slate-200">
                                        <div
                                          className={cn("h-full rounded-full", barTone)}
                                          style={{
                                            width: `${Math.min(100, Math.round(ratio * 100))}%`,
                                          }}
                                        />
                                      </div>
                                    </div>
                                  )}
                                </td>
                              );
                            })}
                          </tr>
                        );
                      })}

                      {/* Brechas */}
                      <tr className="bg-rose-50/30">
                        <td className="px-3 py-2.5 text-xs font-semibold text-rose-700">
                          <AlertTriangle className="mr-1 inline-block h-3 w-3" />
                          Brechas críticas
                        </td>
                        {selectedItems.map((item) => {
                          const ai = aiOf(item.evaluation);
                          const count =
                            ai.critical_gaps_detailed?.length ||
                            (item.evaluation?.critical_gaps as unknown[] | undefined)?.length ||
                            0;
                          return (
                            <td key={item.id} className="px-3 py-2.5 text-center">
                              <span
                                className={cn(
                                  "rounded-full px-2 py-0.5 text-xs font-semibold",
                                  count === 0
                                    ? "bg-emerald-100 text-emerald-700"
                                    : "bg-rose-100 text-rose-700"
                                )}
                              >
                                {count}
                              </span>
                            </td>
                          );
                        })}
                      </tr>

                      {/* Fortalezas */}
                      <tr className="bg-emerald-50/30">
                        <td className="px-3 py-2.5 text-xs font-semibold text-emerald-700">
                          <CheckCircle2 className="mr-1 inline-block h-3 w-3" />
                          Fortalezas calzadas
                        </td>
                        {selectedItems.map((item) => {
                          const ai = aiOf(item.evaluation);
                          const count =
                            ai.strengths_detailed?.length ||
                            (item.evaluation?.strengths as unknown[] | undefined)?.length ||
                            0;
                          return (
                            <td key={item.id} className="px-3 py-2.5 text-center">
                              <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-700">
                                {count}
                              </span>
                            </td>
                          );
                        })}
                      </tr>

                      {/* Oportunidades */}
                      <tr className="bg-indigo-50/30">
                        <td className="px-3 py-2.5 text-xs font-semibold text-indigo-700">
                          <Lightbulb className="mr-1 inline-block h-3 w-3" />
                          Oportunidades transferibles
                        </td>
                        {selectedItems.map((item) => {
                          const ai = aiOf(item.evaluation);
                          const count = ai.opportunities?.length || 0;
                          return (
                            <td key={item.id} className="px-3 py-2.5 text-center">
                              <span className="rounded-full bg-indigo-100 px-2 py-0.5 text-xs font-semibold text-indigo-700">
                                {count}
                              </span>
                            </td>
                          );
                        })}
                      </tr>

                      {/* Trayectoria */}
                      <tr>
                        <td className="px-3 py-2.5 text-xs font-semibold text-brand-grayMid">
                          <TrendingUp className="mr-1 inline-block h-3 w-3" />
                          Trayectoria
                        </td>
                        {selectedItems.map((item) => {
                          const ai = aiOf(item.evaluation);
                          const t = ai.career_trajectory;
                          return (
                            <td key={item.id} className="px-3 py-2.5 text-center text-[11px] text-brand-grayMid">
                              {t?.current_phase ? (
                                <span className="font-medium text-brand-black">{t.current_phase}</span>
                              ) : (
                                "—"
                              )}
                              {t?.tenure_stability ? (
                                <span className="mt-0.5 block text-[10px]">
                                  {t.tenure_stability}
                                </span>
                              ) : null}
                            </td>
                          );
                        })}
                      </tr>

                      {/* Recomendación */}
                      <tr className="bg-slate-50/40">
                        <td className="px-3 py-2.5 text-xs font-semibold text-brand-black">
                          Recomendación
                        </td>
                        {selectedItems.map((item) => (
                          <td
                            key={item.id}
                            className="px-3 py-2.5 text-center text-[11px] text-brand-grayMid"
                          >
                            {item.evaluation?.recommendation || "—"}
                          </td>
                        ))}
                      </tr>

                      {/* Ver evaluación */}
                      <tr>
                        <td className="px-3 py-2.5 text-xs font-semibold text-brand-grayMid">
                          Detalle
                        </td>
                        {selectedItems.map((item) => (
                          <td key={item.id} className="px-3 py-2.5 text-center">
                            {item.evaluation_id ? (
                              <a
                                href={`/evaluaciones/${item.evaluation_id}`}
                                className="text-xs font-medium text-brand-blue hover:underline"
                              >
                                Ver evaluación →
                              </a>
                            ) : (
                              <span className="text-xs text-brand-grayMid">Sin evaluación</span>
                            )}
                          </td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </CompareDropZone>
        </section>
      </div>

      <DragOverlay>
        {activeItem ? (
          <article className="cursor-grabbing rounded-xl border border-brand-blue/40 bg-white p-3 shadow-elevated ring-2 ring-brand-blue/30">
            <p className="text-sm font-semibold text-brand-black">
              {activeItem.candidate?.full_name || `Candidato #${activeItem.candidate_id}`}
            </p>
            <p className="text-xs text-brand-grayMid">
              {activeItem.candidate?.current_position || "—"}
            </p>
          </article>
        ) : null}
      </DragOverlay>

      {previewUrl ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
          <div className="flex h-[92vh] w-full max-w-7xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl">
            <header className="flex items-center justify-between border-b border-slate-200 px-5 py-3">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-brand-blue" />
                <h3 className="text-sm font-semibold text-brand-black">
                  Vista previa · Comparativo de {selectedItems.length} candidato
                  {selectedItems.length === 1 ? "" : "s"}
                </h3>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={downloadComparison}
                  disabled={downloadLoading}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-3 py-1.5 text-xs font-semibold text-white shadow-soft transition hover:bg-brand-blueDark disabled:opacity-50"
                >
                  <Download className="h-3 w-3" />
                  {downloadLoading ? "Descargando..." : "Descargar"}
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
              title="Vista previa comparativo PDF"
              className="h-full w-full flex-1 border-0"
            />
          </div>
        </div>
      ) : null}

      {addToRoomOpen && mandateId ? (
        <AddToRoomModal
          open
          mandateId={mandateId}
          evaluationIds={selectedItems
            .map((item) => item.evaluation_id)
            .filter((id): id is number => typeof id === "number")}
          selectionLabel={`${selectedItems.length} candidato${selectedItems.length === 1 ? "" : "s"} seleccionado${selectedItems.length === 1 ? "" : "s"}`}
          onClose={() => setAddToRoomOpen(false)}
          onSuccess={(room) => {
            window.alert(
              `Decision Room actualizado. Link: ${window.location.origin}/shortlist-cliente/${room.public_token}`
            );
          }}
        />
      ) : null}

      {shareModalOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
          <div className="flex w-full max-w-xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl">
            <header className="flex items-center justify-between border-b border-slate-200 px-5 py-3">
              <div className="flex items-center gap-2">
                <Link2 className="h-4 w-4 text-brand-blue" />
                <h3 className="text-sm font-semibold text-brand-black">
                  Compartir shortlist con cliente
                </h3>
              </div>
              <button
                type="button"
                onClick={closeShareModal}
                className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 bg-white text-brand-grayMid transition hover:border-rose-300 hover:text-rose-700"
                aria-label="Cerrar"
              >
                <X className="h-4 w-4" />
              </button>
            </header>

            {shareResult ? (
              <div className="space-y-4 px-5 py-4">
                <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3">
                  <p className="text-xs font-semibold uppercase tracking-wider text-emerald-700">
                    Link generado
                  </p>
                  <p className="mt-1 text-xs text-emerald-800">
                    Cualquiera con este link podrá ver el shortlist sanitizado y dejar feedback.
                    Podés revocar el acceso desde el detalle del mandato.
                  </p>
                </div>
                <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2">
                  <input
                    readOnly
                    value={`${typeof window !== "undefined" ? window.location.origin : ""}/shortlist-cliente/${shareResult.public_token}`}
                    onFocus={(event) => event.target.select()}
                    className="flex-1 bg-transparent text-xs text-brand-black focus:outline-none"
                  />
                  <button
                    type="button"
                    onClick={copyShareLink}
                    className="inline-flex items-center gap-1 rounded-md border border-slate-200 bg-white px-2 py-1 text-xs font-medium text-brand-grayMid hover:border-brand-blue/40 hover:text-brand-blue"
                  >
                    <Copy className="h-3 w-3" />
                    {shareCopied ? "Copiado" : "Copiar"}
                  </button>
                </div>
                <a
                  href={`/shortlist-cliente/${shareResult.public_token}`}
                  target="_blank"
                  rel="noreferrer noopener"
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-brand-blue hover:underline"
                >
                  Abrir vista del cliente
                  <ExternalLink className="h-3 w-3" />
                </a>
                <div className="flex justify-end gap-2 border-t border-slate-100 pt-3">
                  <button
                    type="button"
                    onClick={closeShareModal}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-3.5 py-2 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-blueDark"
                  >
                    Listo
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-4 px-5 py-4">
                <div>
                  <label className="block text-[11px] font-semibold uppercase tracking-wider text-brand-grayMid">
                    Título
                  </label>
                  <input
                    type="text"
                    value={shareTitle}
                    onChange={(event) => setShareTitle(event.target.value)}
                    placeholder="Shortlist Gerente Comercial Regional"
                    className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-brand-black placeholder:text-brand-grayMid focus:border-brand-blue focus:outline-none focus:ring-2 focus:ring-brand-blue/15"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold uppercase tracking-wider text-brand-grayMid">
                    Mensaje al cliente
                  </label>
                  <textarea
                    value={shareMessage}
                    onChange={(event) => setShareMessage(event.target.value)}
                    rows={4}
                    className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-brand-black placeholder:text-brand-grayMid focus:border-brand-blue focus:outline-none focus:ring-2 focus:ring-brand-blue/15"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[11px] font-semibold uppercase tracking-wider text-brand-grayMid">
                      Expira el (opcional)
                    </label>
                    <input
                      type="datetime-local"
                      value={shareExpiresAt}
                      onChange={(event) => setShareExpiresAt(event.target.value)}
                      className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-brand-black focus:border-brand-blue focus:outline-none focus:ring-2 focus:ring-brand-blue/15"
                    />
                  </div>
                  <div className="flex items-end">
                    <label className="flex cursor-pointer items-center gap-2 text-sm text-brand-black">
                      <input
                        type="checkbox"
                        checked={shareShowScores}
                        onChange={(event) => setShareShowScores(event.target.checked)}
                        className="h-4 w-4 rounded border-slate-300 text-brand-blue focus:ring-brand-blue/30"
                      />
                      Mostrar score al cliente
                    </label>
                  </div>
                </div>
                <div className="rounded-xl border border-slate-100 bg-slate-50 px-3 py-2 text-[11px] text-brand-grayMid">
                  {selectedItems.length} candidato{selectedItems.length === 1 ? "" : "s"} serán incluidos en el shortlist:
                  {" "}
                  {selectedItems.map((it) => it.candidate?.full_name || `#${it.candidate_id}`).join(", ")}
                </div>
                <div className="flex justify-end gap-2 border-t border-slate-100 pt-3">
                  <button
                    type="button"
                    onClick={closeShareModal}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-sm font-medium text-brand-grayMid transition hover:border-brand-blue/40 hover:text-brand-black"
                  >
                    Cancelar
                  </button>
                  <button
                    type="button"
                    onClick={createShareLink}
                    disabled={shareLoading}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-3.5 py-2 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-blueDark disabled:opacity-50"
                  >
                    {shareLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Link2 className="h-3.5 w-3.5" />}
                    {shareLoading ? "Generando..." : "Generar link"}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      ) : null}

      {error ? (
        <div className="fixed bottom-4 right-4 z-50 max-w-sm rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700 shadow-elevated">
          {error}
          <button
            type="button"
            onClick={() => setError(null)}
            className="ml-2 text-xs underline"
          >
            Cerrar
          </button>
        </div>
      ) : null}
    </DndContext>
  );
}
