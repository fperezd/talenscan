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
  type DragOverEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import {
  AlertTriangle,
  Briefcase,
  DoorOpen,
  ExternalLink,
  Eye,
  GripVertical,
  MoreVertical,
  Search,
  Star,
  StickyNote,
  Trash2,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { AddToRoomModal } from "@/components/decision-room/add-to-room-modal";
import { apiFetch } from "@/lib/api";
import { useDynamicId } from "@/lib/use-dynamic-id";
import { cn } from "@/lib/utils";
import type { Candidate } from "@/types/candidate";
import type { CandidateEvaluation } from "@/types/evaluation";
import {
  PIPELINE_STAGES,
  PIPELINE_STAGE_LABELS,
  PIPELINE_STAGE_TONES,
  type CandidatePipelineItem,
  type PipelineReorderItem,
  type PipelineStage,
} from "@/types/pipeline";

type PipelineBoardProps = {
  mandateId?: string;
};

type EnrichedItem = CandidatePipelineItem & {
  candidate?: Candidate;
  evaluation?: CandidateEvaluation;
};

type Filters = {
  search: string;
  onlyPriority: boolean;
  onlyCriticalGaps: boolean;
  category: string;
};

const ALL_CATEGORIES = "Todas las categorías";

function scoreCategoryTone(category: string | undefined): string {
  if (!category) return "bg-slate-100 text-brand-grayMid";
  const lower = category.toLowerCase();
  if (lower.includes("muy alto")) return "bg-emerald-100 text-emerald-700";
  if (lower.includes("buen")) return "bg-blue-100 text-blue-700";
  if (lower.includes("parcial")) return "bg-amber-100 text-amber-700";
  if (lower.includes("bajo")) return "bg-zinc-200 text-brand-grayMid";
  if (lower.includes("no recomendado")) return "bg-rose-100 text-rose-700";
  return "bg-slate-100 text-brand-grayMid";
}

function scoreRingColor(score: number | undefined): string {
  if (score === undefined) return "ring-slate-200 text-brand-grayMid";
  if (score >= 85) return "ring-emerald-300 text-emerald-700";
  if (score >= 70) return "ring-blue-300 text-blue-700";
  if (score >= 55) return "ring-amber-300 text-amber-700";
  if (score >= 40) return "ring-zinc-300 text-brand-grayMid";
  return "ring-rose-300 text-rose-700";
}

function PipelineCard({
  item,
  onDelete,
  onSaveNotes,
  onAddToRoom,
  isOverlay = false,
}: {
  item: EnrichedItem;
  onDelete?: (item: EnrichedItem) => void;
  onSaveNotes?: (item: EnrichedItem, notes: string) => Promise<void> | void;
  onAddToRoom?: (item: EnrichedItem) => void;
  isOverlay?: boolean;
}) {
  const sortable = useSortable({
    id: String(item.id),
    data: { stage: item.stage },
  });
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = sortable;
  const [menuOpen, setMenuOpen] = useState(false);
  const [notesEditing, setNotesEditing] = useState(false);
  const [notesDraft, setNotesDraft] = useState(item.consultant_notes || "");
  const [notesSaving, setNotesSaving] = useState(false);
  const menuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setNotesDraft(item.consultant_notes || "");
  }, [item.consultant_notes]);

  useEffect(() => {
    if (!menuOpen) return;
    function handleClickOutside(event: MouseEvent) {
      if (!menuRef.current) return;
      if (!menuRef.current.contains(event.target as Node)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [menuOpen]);

  const style: React.CSSProperties = isOverlay
    ? {}
    : {
        transform: CSS.Transform.toString(transform),
        transition,
        opacity: isDragging ? 0.3 : 1,
      };

  const name = item.candidate?.full_name || `Candidato #${item.candidate_id}`;
  const role = item.candidate?.current_position || "Cargo no informado";
  const company = item.candidate?.current_company || "Empresa no informada";
  const score = item.evaluation?.total_score;
  const category = item.evaluation?.score_category;
  const hasCriticalGaps =
    Array.isArray(item.evaluation?.critical_gaps) && (item.evaluation?.critical_gaps.length ?? 0) > 0;
  const linkedinUrl = item.candidate?.linkedin_url;
  const pendingEvaluation = !item.evaluation_id;

  return (
    <article
      ref={isOverlay ? undefined : setNodeRef}
      style={style}
      className={cn(
        "group relative rounded-xl border border-slate-200 bg-white p-3 shadow-soft transition hover:border-brand-blue/40 hover:shadow-md",
        item.is_priority && "ring-1 ring-amber-300",
        isOverlay && "rotate-1 shadow-elevated"
      )}
    >
      <div className="flex items-start gap-2">
        <button
          type="button"
          aria-label="Mover tarjeta"
          className="mt-1 cursor-grab text-slate-300 transition hover:text-brand-grayMid active:cursor-grabbing"
          {...attributes}
          {...listeners}
        >
          <GripVertical className="h-4 w-4" />
        </button>
        <div className="flex-1">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-brand-black">{name}</p>
              <p className="mt-0.5 flex items-center gap-1 truncate text-xs text-brand-grayMid">
                <Briefcase className="h-3 w-3 shrink-0" />
                <span className="truncate">{role}</span>
              </p>
              <p className="mt-0.5 truncate text-xs text-brand-grayMid">{company}</p>
            </div>
            <div
              className={cn(
                "flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-white text-sm font-semibold ring-2",
                scoreRingColor(score)
              )}
              title={category || "Sin evaluación"}
            >
              {score ?? "—"}
            </div>
          </div>

          {item.consultant_notes && !notesEditing ? (
            <p className="mt-2 line-clamp-2 rounded-md border border-amber-100 bg-amber-50/50 px-2 py-1 text-[11px] italic text-amber-800">
              {item.consultant_notes}
            </p>
          ) : null}
          {notesEditing && !isOverlay ? (
            <div className="mt-2 space-y-1.5">
              <textarea
                autoFocus
                value={notesDraft}
                onChange={(event) => setNotesDraft(event.target.value)}
                placeholder="Notas del consultor (visible solo internamente)"
                className="w-full rounded-md border border-slate-200 bg-white px-2 py-1.5 text-xs text-brand-black placeholder:text-brand-grayMid focus:border-brand-blue focus:outline-none focus:ring-2 focus:ring-brand-blue/15"
                rows={3}
              />
              <div className="flex gap-1.5">
                <button
                  type="button"
                  disabled={notesSaving}
                  onClick={async () => {
                    setNotesSaving(true);
                    try {
                      await onSaveNotes?.(item, notesDraft);
                      setNotesEditing(false);
                    } finally {
                      setNotesSaving(false);
                    }
                  }}
                  className="inline-flex items-center gap-1 rounded-md bg-brand-blue px-2 py-1 text-[11px] font-semibold text-white transition hover:bg-brand-blueDark disabled:opacity-50"
                >
                  {notesSaving ? "Guardando..." : "Guardar"}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setNotesEditing(false);
                    setNotesDraft(item.consultant_notes || "");
                  }}
                  className="inline-flex items-center gap-1 rounded-md border border-slate-200 bg-white px-2 py-1 text-[11px] font-medium text-brand-grayMid transition hover:border-brand-blue/40 hover:text-brand-black"
                >
                  Cancelar
                </button>
              </div>
            </div>
          ) : null}

          <div className="mt-2 flex flex-wrap items-center gap-1.5">
            {pendingEvaluation ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-brand-grayMid">
                CV pendiente
              </span>
            ) : null}
            {category && !pendingEvaluation && (
              <span className={cn("rounded-full px-2 py-0.5 text-[11px] font-medium", scoreCategoryTone(category))}>
                {category}
              </span>
            )}
            {linkedinUrl ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-brand-blueSoft px-2 py-0.5 text-[11px] font-medium text-brand-blue">
                LinkedIn
              </span>
            ) : null}
            {item.is_priority && (
              <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-[11px] font-medium text-amber-700">
                <Star className="h-3 w-3" />
                Prioritario
              </span>
            )}
            {hasCriticalGaps && (
              <span className="inline-flex items-center gap-1 rounded-full bg-rose-100 px-2 py-0.5 text-[11px] font-medium text-rose-700">
                <AlertTriangle className="h-3 w-3" />
                Brechas
              </span>
            )}
          </div>
        </div>
      </div>

      {!isOverlay ? (
        <div ref={menuRef} className="absolute right-2 top-2">
          <button
            type="button"
            aria-label="Acciones"
            onClick={(event) => {
              event.stopPropagation();
              setMenuOpen((prev) => !prev);
            }}
            onPointerDown={(event) => event.stopPropagation()}
            className="rounded p-1 text-brand-grayMid opacity-0 transition hover:bg-slate-100 hover:text-brand-black group-hover:opacity-100"
          >
            <MoreVertical className="h-4 w-4" />
          </button>
          {menuOpen ? (
            <div
              onClick={(event) => event.stopPropagation()}
              className="absolute right-0 top-full z-30 mt-1 w-48 rounded-xl border border-slate-200 bg-white p-1 shadow-elevated"
            >
              <a
                href={`/candidatos/${item.candidate_id}`}
                className="flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm text-brand-black hover:bg-slate-50"
              >
                <Eye className="h-3.5 w-3.5" />
                Ver candidato
              </a>
              {item.evaluation_id ? (
                <a
                  href={`/evaluaciones/${item.evaluation_id}`}
                  className="flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm text-brand-black hover:bg-slate-50"
                >
                  <Eye className="h-3.5 w-3.5" />
                  Ver evaluación
                </a>
              ) : null}
              {linkedinUrl ? (
                <a
                  href={linkedinUrl}
                  target="_blank"
                  rel="noreferrer noopener"
                  className="flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm text-brand-black hover:bg-slate-50"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                  Abrir LinkedIn
                </a>
              ) : null}
              <button
                type="button"
                onClick={() => {
                  setMenuOpen(false);
                  setNotesEditing(true);
                }}
                className="flex w-full items-center gap-2 rounded-lg px-3 py-1.5 text-left text-sm text-brand-black hover:bg-slate-50"
              >
                <StickyNote className="h-3.5 w-3.5" />
                {item.consultant_notes ? "Editar nota" : "Agregar nota"}
              </button>
              {item.evaluation_id && onAddToRoom ? (
                <button
                  type="button"
                  onClick={() => {
                    setMenuOpen(false);
                    onAddToRoom(item);
                  }}
                  className="flex w-full items-center gap-2 rounded-lg px-3 py-1.5 text-left text-sm text-brand-blue hover:bg-brand-blueSoft/40"
                >
                  <DoorOpen className="h-3.5 w-3.5" />
                  Agregar a Decision Room
                </button>
              ) : null}
              <button
                type="button"
                onClick={() => {
                  setMenuOpen(false);
                  onDelete?.(item);
                }}
                className="flex w-full items-center gap-2 rounded-lg px-3 py-1.5 text-left text-sm text-rose-700 hover:bg-rose-50"
              >
                <Trash2 className="h-3.5 w-3.5" />
                Eliminar candidato
              </button>
            </div>
          ) : null}
        </div>
      ) : null}
    </article>
  );
}

function PipelineColumn({
  stage,
  items,
  onTogglePriority,
  onDelete,
  onSaveNotes,
  onAddToRoom,
}: {
  stage: PipelineStage;
  items: EnrichedItem[];
  onTogglePriority: (item: EnrichedItem) => void;
  onDelete: (item: EnrichedItem) => void;
  onSaveNotes: (item: EnrichedItem, notes: string) => Promise<void>;
  onAddToRoom?: (item: EnrichedItem) => void;
}) {
  const { isOver, setNodeRef } = useDroppable({ id: stage, data: { stage } });

  return (
    <article
      className={cn(
        "flex w-72 shrink-0 flex-col rounded-2xl border p-3 transition",
        PIPELINE_STAGE_TONES[stage],
        isOver && "border-brand-blue/60 ring-2 ring-brand-blue/20"
      )}
    >
      <header className="mb-3 flex items-center justify-between px-1">
        <h3 className="text-sm font-semibold text-brand-black">{PIPELINE_STAGE_LABELS[stage]}</h3>
        <span className="rounded-full bg-white px-2 py-0.5 text-xs font-medium text-brand-grayMid">
          {items.length}
        </span>
      </header>

      <SortableContext
        items={items.map((item) => String(item.id))}
        strategy={verticalListSortingStrategy}
      >
        <div ref={setNodeRef} className="flex min-h-[120px] flex-col gap-2">
          {items.length === 0 ? (
            <div className="flex items-center justify-center rounded-lg border border-dashed border-slate-300 bg-white/40 px-3 py-6 text-center text-xs text-brand-grayMid">
              Arrastra candidatos aquí
            </div>
          ) : (
            items.map((item) => (
              <div key={item.id} onDoubleClick={() => onTogglePriority(item)}>
                <PipelineCard
                  item={item}
                  onDelete={onDelete}
                  onSaveNotes={onSaveNotes}
                  onAddToRoom={onAddToRoom}
                />
              </div>
            ))
          )}
        </div>
      </SortableContext>
    </article>
  );
}

export function PipelineBoard({ mandateId: propId }: PipelineBoardProps = {}) {
  const pathId = useDynamicId("mandatos");
  const mandateId = pathId && pathId !== "demo" ? pathId : propId || pathId;
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [items, setItems] = useState<EnrichedItem[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [filters, setFilters] = useState<Filters>({
    search: "",
    onlyPriority: false,
    onlyCriticalGaps: false,
    category: ALL_CATEGORIES,
  });

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 4 } }));
  const [addToRoomFor, setAddToRoomFor] = useState<EnrichedItem | null>(null);

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
        setError("No fue posible cargar el pipeline. Verifica que el backend esté disponible.");
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, [mandateId]);

  const visibleItems = useMemo(() => {
    const search = filters.search.trim().toLowerCase();
    return items.filter((item) => {
      if (filters.onlyPriority && !item.is_priority) return false;
      if (
        filters.onlyCriticalGaps &&
        !(Array.isArray(item.evaluation?.critical_gaps) && (item.evaluation?.critical_gaps.length ?? 0) > 0)
      ) {
        return false;
      }
      if (filters.category !== ALL_CATEGORIES && item.evaluation?.score_category !== filters.category) {
        return false;
      }
      if (search.length === 0) return true;
      const haystack = [
        item.candidate?.full_name,
        item.candidate?.current_position,
        item.candidate?.current_company,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return haystack.includes(search);
    });
  }, [items, filters]);

  const grouped = useMemo(() => {
    const base: Record<PipelineStage, EnrichedItem[]> = {
      received: [],
      analyzing: [],
      evaluated: [],
      preselected: [],
      interview: [],
      reserve: [],
      discarded: [],
      present_to_client: [],
    };
    for (const item of visibleItems) {
      base[item.stage].push(item);
    }
    for (const stage of PIPELINE_STAGES) {
      base[stage].sort((a, b) => a.stage_order - b.stage_order);
    }
    return base;
  }, [visibleItems]);

  const categoryOptions = useMemo(() => {
    const set = new Set<string>();
    for (const item of items) {
      if (item.evaluation?.score_category) set.add(item.evaluation.score_category);
    }
    return [ALL_CATEGORIES, ...Array.from(set).sort()];
  }, [items]);

  async function persistReorder(updated: EnrichedItem[]) {
    const payload: PipelineReorderItem[] = updated.map((entry) => ({
      id: entry.id,
      stage: entry.stage,
      stage_order: entry.stage_order,
    }));
    try {
      await apiFetch<CandidatePipelineItem[]>(`/api/mandatos/${mandateId}/pipeline/reorder`, {
        method: "PATCH",
        body: JSON.stringify({ items: payload }),
      });
    } catch (persistError) {
      console.error(persistError);
      setError("No fue posible guardar el movimiento. Se revirtió el cambio.");
      throw persistError;
    }
  }

  function handleDragStart(event: DragStartEvent) {
    setActiveId(Number(event.active.id));
  }

  function handleDragOver(_event: DragOverEvent) {
    // Visual feedback handled via useDroppable isOver.
  }

  function resolveTargetStage(overId: string | number): PipelineStage | null {
    if (typeof overId === "string" && PIPELINE_STAGES.includes(overId as PipelineStage)) {
      return overId as PipelineStage;
    }
    const targetItem = items.find((entry) => entry.id === Number(overId));
    return targetItem ? targetItem.stage : null;
  }

  async function handleDragEnd(event: DragEndEvent) {
    setActiveId(null);
    const { active, over } = event;
    if (!over) return;

    const activeNumericId = Number(active.id);
    const activeItem = items.find((entry) => entry.id === activeNumericId);
    if (!activeItem) return;

    const targetStage = resolveTargetStage(over.id);
    if (!targetStage) return;

    const previousItems = items;
    const droppedOnCard = !(
      typeof over.id === "string" && PIPELINE_STAGES.includes(over.id as PipelineStage)
    );
    const overNumericId = Number(over.id);

    // Reorder dentro de la misma columna
    if (activeItem.stage === targetStage && droppedOnCard && overNumericId !== activeNumericId) {
      const stageItems = items
        .filter((entry) => entry.stage === targetStage)
        .slice()
        .sort((a, b) => a.stage_order - b.stage_order);
      const oldIndex = stageItems.findIndex((entry) => entry.id === activeNumericId);
      const newIndex = stageItems.findIndex((entry) => entry.id === overNumericId);
      if (oldIndex === -1 || newIndex === -1 || oldIndex === newIndex) return;
      const reorderedStage = [...stageItems];
      const [moved] = reorderedStage.splice(oldIndex, 1);
      reorderedStage.splice(newIndex, 0, moved);
      const reorderedAll = items.map((entry) => {
        if (entry.stage !== targetStage) return entry;
        const idx = reorderedStage.findIndex((s) => s.id === entry.id);
        return idx >= 0 ? { ...entry, stage_order: idx } : entry;
      });
      setItems(reorderedAll);
      try {
        await persistReorder(reorderedAll);
      } catch {
        setItems(previousItems);
      }
      return;
    }

    // Cambio de columna
    if (activeItem.stage !== targetStage) {
      const nextItems = items.map((entry) =>
        entry.id === activeNumericId ? { ...entry, stage: targetStage } : entry
      );
      const reordered = PIPELINE_STAGES.flatMap((stage) =>
        nextItems
          .filter((entry) => entry.stage === stage)
          .map((entry, index) => ({ ...entry, stage_order: index }))
      );
      setItems(reordered);
      try {
        await persistReorder(reordered);
      } catch {
        setItems(previousItems);
      }
    }
  }

  async function handleTogglePriority(item: EnrichedItem) {
    const previousItems = items;
    const nextValue = !item.is_priority;
    setItems(items.map((entry) => (entry.id === item.id ? { ...entry, is_priority: nextValue } : entry)));
    try {
      await apiFetch<CandidatePipelineItem>(`/api/pipeline/items/${item.id}`, {
        method: "PATCH",
        body: JSON.stringify({ is_priority: nextValue }),
      });
    } catch (toggleError) {
      console.error(toggleError);
      setItems(previousItems);
      setError("No fue posible marcar la prioridad.");
    }
  }

  async function handleSaveNotes(item: EnrichedItem, notes: string) {
    const previousItems = items;
    const trimmed = notes.trim();
    setItems(items.map((entry) => (entry.id === item.id ? { ...entry, consultant_notes: trimmed } : entry)));
    try {
      await apiFetch<CandidatePipelineItem>(`/api/pipeline/items/${item.id}`, {
        method: "PATCH",
        body: JSON.stringify({ consultant_notes: trimmed }),
      });
    } catch (notesError) {
      console.error(notesError);
      setItems(previousItems);
      setError("No fue posible guardar la nota.");
    }
  }

  async function handleDelete(item: EnrichedItem) {
    const name = item.candidate?.full_name || `Candidato #${item.candidate_id}`;
    const confirmed = window.confirm(
      `¿Eliminar a ${name} del pipeline? Esto borra el candidato, su CV, perfil y evaluaciones. Esta acción no se puede deshacer.`
    );
    if (!confirmed) return;
    const previousItems = items;
    setItems(items.filter((entry) => entry.id !== item.id));
    try {
      await apiFetch(`/api/candidatos/${item.candidate_id}`, { method: "DELETE" });
    } catch (deleteError) {
      console.error(deleteError);
      setItems(previousItems);
      setError("No fue posible eliminar el candidato.");
    }
  }

  const activeItem = activeId !== null ? items.find((entry) => entry.id === activeId) : undefined;

  if (loading) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center text-sm text-brand-grayMid">
        Cargando pipeline...
      </div>
    );
  }

  if (error && items.length === 0) {
    return (
      <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
        {error}
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center">
        <p className="text-sm font-semibold text-brand-black">Aún no hay candidatos en este pipeline.</p>
        <p className="mt-1 text-xs text-brand-grayMid">
          Sube CVs o pega URLs de LinkedIn desde "Evaluar candidatos" para empezar.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
          {error}
        </div>
      )}

      <div className="flex flex-wrap items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2">
        <div className="relative flex-1 min-w-[220px]">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-brand-grayMid" />
          <input
            type="search"
            value={filters.search}
            onChange={(event) => setFilters({ ...filters, search: event.target.value })}
            placeholder="Buscar candidato, cargo o empresa..."
            className="w-full rounded-lg border border-slate-200 bg-slate-50 py-1.5 pl-9 pr-3 text-sm text-brand-black placeholder:text-brand-grayMid focus:border-brand-blue focus:bg-white focus:outline-none"
          />
        </div>
        <select
          value={filters.category}
          onChange={(event) => setFilters({ ...filters, category: event.target.value })}
          className="rounded-lg border border-slate-200 bg-white py-1.5 px-3 text-sm text-brand-grayMid focus:border-brand-blue focus:text-brand-black focus:outline-none"
        >
          {categoryOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
        <label className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm text-brand-grayMid">
          <input
            type="checkbox"
            checked={filters.onlyPriority}
            onChange={(event) => setFilters({ ...filters, onlyPriority: event.target.checked })}
            className="h-3.5 w-3.5 accent-brand-blue"
          />
          Prioritarios
        </label>
        <label className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm text-brand-grayMid">
          <input
            type="checkbox"
            checked={filters.onlyCriticalGaps}
            onChange={(event) => setFilters({ ...filters, onlyCriticalGaps: event.target.checked })}
            className="h-3.5 w-3.5 accent-brand-blue"
          />
          Con brechas
        </label>
      </div>

      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragOver={handleDragOver}
        onDragEnd={handleDragEnd}
      >
        <div className="overflow-x-auto pb-3">
          <div className="flex min-w-[1200px] gap-3">
            {PIPELINE_STAGES.map((stage) => (
              <PipelineColumn
                key={stage}
                stage={stage}
                items={grouped[stage]}
                onTogglePriority={handleTogglePriority}
                onDelete={handleDelete}
                onSaveNotes={handleSaveNotes}
                onAddToRoom={(item) => setAddToRoomFor(item)}
              />
            ))}
          </div>
        </div>

        <DragOverlay>
          {activeItem ? (
            <div className="w-72">
              <PipelineCard item={activeItem} isOverlay />
            </div>
          ) : null}
        </DragOverlay>
      </DndContext>

      <p className="text-xs text-brand-grayMid">
        Doble clic en una tarjeta para marcarla como prioritaria. Arrastra entre columnas o dentro de la misma columna para reordenar.
      </p>

      {addToRoomFor && addToRoomFor.evaluation_id && mandateId ? (
        <AddToRoomModal
          open
          mandateId={mandateId}
          evaluationIds={[addToRoomFor.evaluation_id]}
          selectionLabel={addToRoomFor.candidate?.full_name || `Candidato #${addToRoomFor.candidate_id}`}
          onClose={() => setAddToRoomFor(null)}
          onSuccess={() => {
            setAddToRoomFor(null);
          }}
        />
      ) : null}
    </div>
  );
}
