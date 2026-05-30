"use client";

import {
  DndContext,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  arrayMove,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import {
  AlertTriangle,
  Building2,
  Check,
  ClipboardCopy,
  GripVertical,
  Layers,
  Loader2,
  Plus,
  RefreshCw,
  Sparkles,
  Target,
  ThumbsDown,
  ThumbsUp,
  Trash2,
  TrendingUp,
  Users,
  X,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { API_BASE_URL, apiFetch } from "@/lib/api";
import { cn } from "@/lib/utils";
import {
  CLOSENESS_LABELS,
  COMPANY_COVERAGE_LABELS,
  IMPACT_LABELS,
  MAP_STATUS_LABELS,
  MARKET_ASSESSMENT_LABELS,
  PRIORITY_LABELS,
  RECOMMENDATION_STATUS_LABELS,
  SEGMENT_COVERAGE_LABELS,
  SEGMENT_TYPE_LABELS,
  type ClosenessLevel,
  type CompanyCoverage,
  type EquivalentRole,
  type MarketAssessment,
  type MarketGap,
  type MarketSegment,
  type PriorityLevel,
  type RecalibrationRecommendation,
  type SegmentCoverage,
  type SegmentType,
  type TalentMarketMap as TalentMarketMapType,
  type TargetCompany,
} from "@/types/talent-market-map";

type Props = { mandateId: string };

type TabId = "resumen" | "segmentos" | "empresas" | "cargos" | "brechas" | "recalibracion";

const TABS: Array<[TabId, string]> = [
  ["resumen", "Resumen"],
  ["segmentos", "Segmentos"],
  ["empresas", "Empresas"],
  ["cargos", "Cargos equivalentes"],
  ["brechas", "Brechas"],
  ["recalibracion", "Recalibración"],
];

const PRIORITY_TONE: Record<PriorityLevel, string> = {
  high: "bg-rose-100 text-rose-700",
  medium: "bg-amber-100 text-amber-700",
  low: "bg-slate-100 text-brand-grayMid",
};

const SEGMENT_TYPE_TONE: Record<SegmentType, string> = {
  primary: "bg-brand-blueSoft text-brand-blue",
  adjacent: "bg-indigo-100 text-indigo-700",
  exploratory: "bg-cyan-100 text-cyan-700",
};

const IMPACT_TONE: Record<"high" | "medium" | "low", string> = {
  high: "bg-rose-100 text-rose-700",
  medium: "bg-amber-100 text-amber-700",
  low: "bg-slate-100 text-brand-grayMid",
};

// ===========================================================================
// Root
// ===========================================================================

export function TalentMarketMap({ mandateId }: Props) {
  const [map, setMap] = useState<TalentMarketMapType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [activeTab, setActiveTab] = useState<TabId>("resumen");

  async function reload() {
    setError(null);
    try {
      const data = await apiFetch<TalentMarketMapType>(
        `/api/mandatos/${mandateId}/talent-market-map`
      );
      setMap(data);
    } catch (caught) {
      console.error(caught);
      setError("No fue posible cargar el Talent Market Map del mandato.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    setLoading(true);
    void reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mandateId]);

  async function generate() {
    if (
      map &&
      (map.status === "generated" || map.status === "updated") &&
      !window.confirm(
        "¿Regenerar el mapa con IA? Se actualizarán las entidades sugeridas por IA; lo que agregaste o editaste manualmente se conserva."
      )
    ) {
      return;
    }
    setGenerating(true);
    setError(null);
    try {
      const data = await apiFetch<TalentMarketMapType>(
        `/api/mandatos/${mandateId}/talent-market-map/generate`,
        { method: "POST", body: JSON.stringify({}) }
      );
      setMap(data);
    } catch (caught) {
      console.error(caught);
      setError("No fue posible generar el mapa. Reintenta más tarde.");
    } finally {
      setGenerating(false);
    }
  }

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-brand-blue" />
      </div>
    );
  }

  if (error && !map) {
    return (
      <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700">
        {error}
      </div>
    );
  }

  if (!map) return null;

  const isEmpty =
    map.segments.length === 0 &&
    map.companies.length === 0 &&
    map.equivalent_roles.length === 0;

  if (isEmpty && map.status === "draft") {
    return <EmptyState generating={generating} onGenerate={generate} error={error} />;
  }

  return (
    <div className="space-y-5">
      <MapHeader map={map} generating={generating} onGenerate={generate} />

      {error ? (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-2 text-xs text-rose-700">
          {error}
        </div>
      ) : null}

      <div className="flex flex-wrap gap-1 border-b border-slate-200">
        {TABS.map(([id, label]) => {
          const count = tabCount(map, id);
          return (
            <button
              key={id}
              type="button"
              onClick={() => setActiveTab(id)}
              className={cn(
                "inline-flex items-center gap-1.5 border-b-2 px-3 py-2 text-sm font-medium transition",
                activeTab === id
                  ? "border-brand-blue text-brand-blue"
                  : "border-transparent text-brand-grayMid hover:text-brand-black"
              )}
            >
              {label}
              {count !== null ? (
                <span
                  className={cn(
                    "rounded-full px-1.5 py-0.5 text-[10px] font-semibold",
                    activeTab === id ? "bg-brand-blueSoft text-brand-blue" : "bg-slate-100 text-brand-grayMid"
                  )}
                >
                  {count}
                </span>
              ) : null}
            </button>
          );
        })}
      </div>

      {activeTab === "resumen" ? <ResumenTab map={map} onMap={setMap} /> : null}
      {activeTab === "segmentos" ? <SegmentosTab map={map} onMap={setMap} /> : null}
      {activeTab === "empresas" ? <EmpresasTab map={map} onMap={setMap} /> : null}
      {activeTab === "cargos" ? <CargosTab map={map} onMap={setMap} /> : null}
      {activeTab === "brechas" ? <BrechasTab map={map} onMap={setMap} /> : null}
      {activeTab === "recalibracion" ? <RecalibracionTab map={map} onMap={setMap} /> : null}
    </div>
  );
}

function tabCount(map: TalentMarketMapType, id: TabId): number | null {
  switch (id) {
    case "segmentos":
      return map.segments.length;
    case "empresas":
      return map.companies.length;
    case "cargos":
      return map.equivalent_roles.length;
    case "brechas":
      return map.gaps.length;
    case "recalibracion":
      return map.recommendations.filter((r) => r.status === "suggested").length || null;
    default:
      return null;
  }
}

// ===========================================================================
// Empty state
// ===========================================================================

function EmptyState({
  generating,
  onGenerate,
  error,
}: {
  generating: boolean;
  onGenerate: () => Promise<void>;
  error: string | null;
}) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center shadow-soft">
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-brand-blueSoft">
        <Target className="h-5 w-5 text-brand-blue" />
      </div>
      <h3 className="mt-3 text-lg font-semibold text-brand-black">
        Aún no generaste el mapa de mercado para esta búsqueda
      </h3>
      <p className="mx-auto mt-1 max-w-md text-sm text-brand-grayMid">
        Genera un mapa inicial a partir del mandato y el perfil objetivo: segmentos de
        industria, empresas target y cargos equivalentes. Después podrás editarlo,
        medir cobertura y detectar brechas.
      </p>
      <button
        type="button"
        onClick={onGenerate}
        disabled={generating}
        className="mt-5 inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-4 py-2 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-blueDark disabled:opacity-60"
      >
        {generating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
        Generar mapa con IA
      </button>
      <p className="mt-3 text-xs text-brand-grayMid">
        Si OpenAI no está disponible, se genera una versión inicial a partir del perfil objetivo.
      </p>
      {error ? <p className="mt-3 text-xs text-rose-700">{error}</p> : null}
    </div>
  );
}

// ===========================================================================
// Header (KPIs + acciones)
// ===========================================================================

function MapHeader({
  map,
  generating,
  onGenerate,
}: {
  map: TalentMarketMapType;
  generating: boolean;
  onGenerate: () => Promise<void>;
}) {
  const [copying, setCopying] = useState(false);
  const cov = map.coverage;

  async function copySummary() {
    setCopying(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/talent-market-maps/${map.id}/export/summary`,
        { cache: "no-store" }
      );
      const text = await response.text();
      await navigator.clipboard.writeText(text);
      window.alert("Resumen del mapa copiado al portapapeles.");
    } catch {
      window.alert("No fue posible copiar el resumen.");
    } finally {
      setCopying(false);
    }
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-gradient-to-br from-brand-blueSoft/30 via-white to-white p-6 shadow-soft">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] font-semibold text-brand-grayMid">
              {MAP_STATUS_LABELS[map.status]}
            </span>
            {map.market_assessment ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-brand-blueSoft px-2.5 py-0.5 text-[11px] font-semibold text-brand-blue">
                <TrendingUp className="h-3 w-3" />
                {MARKET_ASSESSMENT_LABELS[map.market_assessment]}
              </span>
            ) : null}
            {map.generated_by_model ? (
              <span className="inline-flex items-center rounded-full bg-white px-2.5 py-0.5 text-[11px] font-medium text-brand-grayMid">
                {map.generated_by_model === "rules-fallback"
                  ? "Generado por reglas"
                  : `IA · ${map.generated_by_model}`}
              </span>
            ) : null}
          </div>
          <h2 className="mt-3 text-2xl font-semibold tracking-tight text-brand-black">
            Mapa de mercado de talento
          </h2>
          {map.generated_at ? (
            <p className="mt-1 text-sm text-brand-grayMid">
              Última generación: {new Date(map.generated_at).toLocaleString("es-ES")}
            </p>
          ) : null}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={onGenerate}
            disabled={generating}
            className="inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-3 py-2 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-blueDark disabled:opacity-60"
          >
            {generating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Sparkles className="h-3.5 w-3.5" />}
            {map.status === "draft" ? "Generar con IA" : "Regenerar con IA"}
          </button>
          <button
            type="button"
            onClick={copySummary}
            disabled={copying}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-brand-grayMid transition hover:border-brand-blue/40 hover:text-brand-black disabled:opacity-60"
          >
            {copying ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <ClipboardCopy className="h-3.5 w-3.5" />}
            Copiar resumen
          </button>
        </div>
      </div>

      {/* KPIs de cobertura */}
      <div className="mt-5">
        <div className="flex items-center justify-between text-xs text-brand-grayMid">
          <span className="font-semibold uppercase tracking-wider">Cobertura general</span>
          <span className="font-semibold text-brand-black">{cov.coverage_pct}%</span>
        </div>
        <div className="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-slate-100">
          <div
            className="h-full rounded-full bg-brand-blue transition-all"
            style={{ width: `${cov.coverage_pct}%` }}
          />
        </div>
        <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          <Kpi icon={Users} label="Identificados" value={cov.candidates_identified} />
          <Kpi icon={Sparkles} label="Evaluados" value={cov.candidates_evaluated} />
          <Kpi icon={TrendingUp} label="Alto calce" value={cov.high_fit} tone="emerald" />
          <Kpi icon={Building2} label="Empresas target" value={cov.target_companies_total} />
          <Kpi icon={Check} label="Empresas revisadas" value={cov.target_companies_reviewed} />
          <Kpi icon={Layers} label="Industrias" value={cov.industries_covered} />
        </div>
      </div>
    </section>
  );
}

function Kpi({
  icon: Icon,
  label,
  value,
  tone,
}: {
  icon: typeof Users;
  label: string;
  value: number;
  tone?: "emerald";
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 shadow-soft">
      <div className="flex items-center gap-1.5 text-[11px] font-medium text-brand-grayMid">
        <Icon className={cn("h-3.5 w-3.5", tone === "emerald" ? "text-emerald-600" : "text-brand-blue")} />
        {label}
      </div>
      <p className="mt-1 text-xl font-bold text-brand-black">{value}</p>
    </div>
  );
}

// ===========================================================================
// Helpers compartidos
// ===========================================================================

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="block text-[11px] font-semibold uppercase tracking-wider text-brand-grayMid">
        {label}
      </span>
      <span className="mt-1 block">{children}</span>
    </label>
  );
}

const inputClass =
  "w-full rounded-md border border-slate-200 bg-white px-2 py-1.5 text-sm text-brand-black focus:border-brand-blue focus:outline-none focus:ring-2 focus:ring-brand-blue/15";

const selectClassXs =
  "rounded-md border border-slate-200 bg-white px-2 py-1 text-xs text-brand-black focus:border-brand-blue focus:outline-none";

function AiBadge() {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-brand-blueSoft px-2 py-0.5 text-[10px] font-semibold text-brand-blue">
      <Sparkles className="h-2.5 w-2.5" />
      IA
    </span>
  );
}

function ModalShell({
  title,
  eyebrow,
  onClose,
  children,
  footer,
}: {
  title: string;
  eyebrow: string;
  onClose: () => void;
  children: React.ReactNode;
  footer: React.ReactNode;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-brand-black/40 px-4 py-6 sm:items-center">
      <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl">
        <div className="flex items-start justify-between gap-2 border-b border-slate-100 pb-4">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-blue">{eyebrow}</p>
            <h3 className="mt-0.5 text-lg font-semibold text-brand-black">{title}</h3>
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
        <div className="mt-4 space-y-3">{children}</div>
        <div className="mt-5 flex items-center justify-end gap-2 border-t border-slate-100 pt-4">{footer}</div>
      </div>
    </div>
  );
}

// Hook de mutación: cada endpoint devuelve el mapa completo.
function useMapMutation(onMap: (m: TalentMarketMapType) => void) {
  const [busy, setBusy] = useState<string | null>(null);
  async function run(key: string, path: string, init?: RequestInit) {
    setBusy(key);
    try {
      const updated = await apiFetch<TalentMarketMapType>(path, init);
      onMap(updated);
      return true;
    } catch (caught) {
      console.error(caught);
      window.alert("La operación no pudo completarse. Reintenta más tarde.");
      return false;
    } finally {
      setBusy(null);
    }
  }
  return { busy, run };
}

// ===========================================================================
// Tab: Resumen
// ===========================================================================

function ResumenTab({
  map,
  onMap,
}: {
  map: TalentMarketMapType;
  onMap: (m: TalentMarketMapType) => void;
}) {
  const [summary, setSummary] = useState(map.executive_summary || "");
  const [assessment, setAssessment] = useState<MarketAssessment | "">(map.market_assessment || "");
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState<string | null>(null);
  const cov = map.coverage;

  useEffect(() => {
    setSummary(map.executive_summary || "");
    setAssessment(map.market_assessment || "");
  }, [map.id, map.executive_summary, map.market_assessment]);

  async function save() {
    setSaving(true);
    try {
      const updated = await apiFetch<TalentMarketMapType>(
        `/api/talent-market-maps/${map.id}`,
        {
          method: "PATCH",
          body: JSON.stringify({
            executive_summary: summary,
            market_assessment: assessment || null,
          }),
        }
      );
      onMap(updated);
      setSavedAt(new Date().toLocaleTimeString("es-ES"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-brand-black">Resumen ejecutivo</h3>
          {savedAt ? <span className="text-[11px] text-emerald-700">Guardado a las {savedAt}</span> : null}
        </div>
        <p className="mt-1 text-xs text-brand-grayMid">
          Síntesis del mercado objetivo. Editable y exportable para compartir con el equipo o el cliente.
        </p>
        <textarea
          value={summary}
          onChange={(e) => setSummary(e.target.value)}
          rows={9}
          placeholder="Genera el mapa con IA o redacta aquí el análisis del mercado objetivo…"
          className="mt-3 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm leading-relaxed text-brand-black focus:border-brand-blue focus:outline-none focus:ring-2 focus:ring-brand-blue/15"
        />
        <div className="mt-3 flex flex-wrap items-end justify-between gap-3">
          <Field label="Evaluación del mercado">
            <select
              value={assessment}
              onChange={(e) => setAssessment(e.target.value as MarketAssessment | "")}
              className={selectClassXs}
            >
              <option value="">—</option>
              {(Object.keys(MARKET_ASSESSMENT_LABELS) as MarketAssessment[]).map((k) => (
                <option key={k} value={k}>
                  {MARKET_ASSESSMENT_LABELS[k]}
                </option>
              ))}
            </select>
          </Field>
          <button
            type="button"
            onClick={save}
            disabled={saving}
            className="inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-4 py-2 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-blueDark disabled:opacity-60"
          >
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
            Guardar resumen
          </button>
        </div>
      </section>

      <aside className="space-y-4">
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
          <h3 className="text-sm font-semibold text-brand-black">Cobertura del pipeline</h3>
          <dl className="mt-3 space-y-2 text-sm">
            <CovRow label="Candidatos identificados" value={cov.candidates_identified} />
            <CovRow label="Cargados" value={cov.candidates_loaded} />
            <CovRow label="Evaluados" value={cov.candidates_evaluated} />
            <CovRow label="Alto calce (≥70)" value={cov.high_fit} tone="emerald" />
            <CovRow label="Calce medio (55–69)" value={cov.medium_fit} />
            <CovRow label="Bajo calce (<55)" value={cov.low_fit} />
            <CovRow label="Descartados" value={cov.discarded} />
            <CovRow label="En shortlist" value={cov.shortlisted} tone="blue" />
          </dl>
        </section>
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
          <h3 className="text-sm font-semibold text-brand-black">Empresas e industrias</h3>
          <dl className="mt-3 space-y-2 text-sm">
            <CovRow label="Empresas target" value={cov.target_companies_total} />
            <CovRow label="Revisadas" value={cov.target_companies_reviewed} tone="emerald" />
            <CovRow label="Pendientes" value={cov.target_companies_pending} />
            <CovRow label="Industrias cubiertas" value={cov.industries_covered} />
          </dl>
        </section>
      </aside>
    </div>
  );
}

function CovRow({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone?: "emerald" | "blue";
}) {
  return (
    <div className="flex items-center justify-between">
      <dt className="text-brand-grayMid">{label}</dt>
      <dd
        className={cn(
          "font-semibold tabular-nums",
          tone === "emerald" ? "text-emerald-700" : tone === "blue" ? "text-brand-blue" : "text-brand-black"
        )}
      >
        {value}
      </dd>
    </div>
  );
}

// ===========================================================================
// Tab: Segmentos (dnd reorder)
// ===========================================================================

function SegmentosTab({
  map,
  onMap,
}: {
  map: TalentMarketMapType;
  onMap: (m: TalentMarketMapType) => void;
}) {
  const { busy, run } = useMapMutation(onMap);
  const [adding, setAdding] = useState(false);
  const [items, setItems] = useState(map.segments);
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 4 } }));

  useEffect(() => setItems(map.segments), [map.segments]);

  async function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const oldIndex = items.findIndex((i) => String(i.id) === String(active.id));
    const newIndex = items.findIndex((i) => String(i.id) === String(over.id));
    if (oldIndex === -1 || newIndex === -1) return;
    const next = arrayMove(items, oldIndex, newIndex);
    setItems(next);
    await run("reorder", `/api/talent-market-maps/${map.id}/segments/reorder`, {
      method: "PATCH",
      body: JSON.stringify({ ordered_ids: next.map((i) => i.id) }),
    });
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-xs text-brand-grayMid">
          Segmentos del mercado, agrupados por cercanía al cargo. Arrastra para reordenar la prioridad de búsqueda.
        </p>
        <button
          type="button"
          onClick={() => setAdding(true)}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-brand-grayMid transition hover:border-brand-blue/40 hover:text-brand-black"
        >
          <Plus className="h-4 w-4" />
          Agregar segmento
        </button>
      </div>

      {items.length === 0 ? (
        <EmptyBlock text="Sin segmentos todavía. Genera el mapa con IA o agrega uno manualmente." />
      ) : (
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
          <SortableContext items={items.map((i) => String(i.id))} strategy={verticalListSortingStrategy}>
            <ul className="space-y-3">
              {items.map((seg) => (
                <SegmentCard key={seg.id} segment={seg} mapId={map.id} busy={busy} run={run} />
              ))}
            </ul>
          </SortableContext>
        </DndContext>
      )}

      {adding ? (
        <AddSegmentModal mapId={map.id} onMap={onMap} onClose={() => setAdding(false)} />
      ) : null}
    </div>
  );
}

function SegmentCard({
  segment,
  mapId,
  busy,
  run,
}: {
  segment: MarketSegment;
  mapId: number;
  busy: string | null;
  run: (key: string, path: string, init?: RequestInit) => Promise<boolean>;
}) {
  const sortable = useSortable({ id: String(segment.id) });
  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(sortable.transform),
    transition: sortable.transition,
    opacity: sortable.isDragging ? 0.4 : 1,
  };
  const base = `/api/talent-market-maps/${mapId}/segments/${segment.id}`;

  return (
    <li ref={sortable.setNodeRef} style={style} className="rounded-xl border border-slate-200 bg-white shadow-soft">
      <div className="flex items-start gap-2 p-4">
        <button
          type="button"
          aria-label="Mover"
          className="mt-1 cursor-grab text-slate-300 transition hover:text-brand-grayMid active:cursor-grabbing"
          {...sortable.attributes}
          {...sortable.listeners}
        >
          <GripVertical className="h-4 w-4" />
        </button>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className={cn("rounded-full px-2 py-0.5 text-[10px] font-semibold", SEGMENT_TYPE_TONE[segment.segment_type])}>
              {SEGMENT_TYPE_LABELS[segment.segment_type]}
            </span>
            <span className={cn("rounded-full px-2 py-0.5 text-[10px] font-semibold", PRIORITY_TONE[segment.priority])}>
              Prioridad {PRIORITY_LABELS[segment.priority].toLowerCase()}
            </span>
            {segment.ai_suggested ? <AiBadge /> : null}
            {segment.candidate_count > 0 ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-brand-grayMid">
                <Users className="h-2.5 w-2.5" />
                {segment.candidate_count}
              </span>
            ) : null}
          </div>
          <p className="mt-1.5 text-sm font-semibold text-brand-black">{segment.name}</p>
          {segment.description ? (
            <p className="mt-0.5 text-xs text-brand-grayMid">{segment.description}</p>
          ) : null}
          {segment.rationale ? (
            <p className="mt-1 text-[11px] italic text-brand-grayMid">{segment.rationale}</p>
          ) : null}
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <select
              value={segment.priority}
              onChange={(e) => run("upd", base, { method: "PATCH", body: JSON.stringify({ priority: e.target.value }) })}
              className={selectClassXs}
              title="Prioridad"
            >
              {(Object.keys(PRIORITY_LABELS) as PriorityLevel[]).map((k) => (
                <option key={k} value={k}>
                  Prioridad: {PRIORITY_LABELS[k]}
                </option>
              ))}
            </select>
            <select
              value={segment.coverage_status}
              onChange={(e) => run("upd", base, { method: "PATCH", body: JSON.stringify({ coverage_status: e.target.value }) })}
              className={selectClassXs}
              title="Cobertura"
            >
              {(Object.keys(SEGMENT_COVERAGE_LABELS) as SegmentCoverage[]).map((k) => (
                <option key={k} value={k}>
                  {SEGMENT_COVERAGE_LABELS[k]}
                </option>
              ))}
            </select>
          </div>
        </div>
        <button
          type="button"
          onClick={() => {
            if (window.confirm(`¿Eliminar el segmento "${segment.name}"?`)) {
              void run("del", base, { method: "DELETE" });
            }
          }}
          disabled={busy === "del"}
          className="inline-flex h-8 w-8 items-center justify-center rounded-md text-brand-grayMid transition hover:bg-rose-50 hover:text-rose-700 disabled:opacity-60"
          title="Eliminar segmento"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>
    </li>
  );
}

function AddSegmentModal({
  mapId,
  onMap,
  onClose,
}: {
  mapId: number;
  onMap: (m: TalentMarketMapType) => void;
  onClose: () => void;
}) {
  const [name, setName] = useState("");
  const [segmentType, setSegmentType] = useState<SegmentType>("primary");
  const [priority, setPriority] = useState<PriorityLevel>("medium");
  const [description, setDescription] = useState("");
  const [rationale, setRationale] = useState("");
  const [saving, setSaving] = useState(false);

  async function submit() {
    if (!name.trim()) return;
    setSaving(true);
    try {
      const updated = await apiFetch<TalentMarketMapType>(
        `/api/talent-market-maps/${mapId}/segments`,
        {
          method: "POST",
          body: JSON.stringify({
            name: name.trim(),
            segment_type: segmentType,
            priority,
            description: description || null,
            rationale: rationale || null,
          }),
        }
      );
      onMap(updated);
      onClose();
    } finally {
      setSaving(false);
    }
  }

  return (
    <ModalShell
      eyebrow="Nuevo segmento"
      title="Agregar segmento de mercado"
      onClose={onClose}
      footer={
        <>
          <button
            type="button"
            onClick={onClose}
            className="inline-flex items-center rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-brand-grayMid hover:bg-slate-50"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={submit}
            disabled={saving || !name.trim()}
            className="inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-4 py-2 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-blueDark disabled:opacity-60"
          >
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
            Agregar
          </button>
        </>
      }
    >
      <Field label="Nombre del segmento">
        <input value={name} onChange={(e) => setName(e.target.value)} className={inputClass} placeholder="Ej. Retail directo" />
      </Field>
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="Tipo">
          <select value={segmentType} onChange={(e) => setSegmentType(e.target.value as SegmentType)} className={inputClass}>
            {(Object.keys(SEGMENT_TYPE_LABELS) as SegmentType[]).map((k) => (
              <option key={k} value={k}>
                {SEGMENT_TYPE_LABELS[k]}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Prioridad">
          <select value={priority} onChange={(e) => setPriority(e.target.value as PriorityLevel)} className={inputClass}>
            {(Object.keys(PRIORITY_LABELS) as PriorityLevel[]).map((k) => (
              <option key={k} value={k}>
                {PRIORITY_LABELS[k]}
              </option>
            ))}
          </select>
        </Field>
      </div>
      <Field label="Descripción (opcional)">
        <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={2} className={inputClass} />
      </Field>
      <Field label="Justificación (opcional)">
        <textarea value={rationale} onChange={(e) => setRationale(e.target.value)} rows={2} className={inputClass} />
      </Field>
    </ModalShell>
  );
}

// ===========================================================================
// Tab: Empresas
// ===========================================================================

function EmpresasTab({
  map,
  onMap,
}: {
  map: TalentMarketMapType;
  onMap: (m: TalentMarketMapType) => void;
}) {
  const { busy, run } = useMapMutation(onMap);
  const [adding, setAdding] = useState(false);
  const [filter, setFilter] = useState("");
  const [coverageFilter, setCoverageFilter] = useState<CompanyCoverage | "">("");

  const segmentName = useMemo(() => {
    const byId = new Map(map.segments.map((s) => [s.id, s.name]));
    return (id: number | null) => (id ? byId.get(id) || "—" : "—");
  }, [map.segments]);

  const filtered = map.companies.filter((c) => {
    if (coverageFilter && c.coverage_status !== coverageFilter) return false;
    if (filter && !`${c.name} ${c.industry || ""}`.toLowerCase().includes(filter.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <input
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Buscar empresa o industria…"
            className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-brand-black focus:border-brand-blue focus:outline-none"
          />
          <select
            value={coverageFilter}
            onChange={(e) => setCoverageFilter(e.target.value as CompanyCoverage | "")}
            className={selectClassXs}
          >
            <option value="">Toda cobertura</option>
            {(Object.keys(COMPANY_COVERAGE_LABELS) as CompanyCoverage[]).map((k) => (
              <option key={k} value={k}>
                {COMPANY_COVERAGE_LABELS[k]}
              </option>
            ))}
          </select>
        </div>
        <button
          type="button"
          onClick={() => setAdding(true)}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-brand-grayMid transition hover:border-brand-blue/40 hover:text-brand-black"
        >
          <Plus className="h-4 w-4" />
          Agregar empresa
        </button>
      </div>

      {filtered.length === 0 ? (
        <EmptyBlock text="Sin empresas target que coincidan. Genera el mapa o agrega empresas manualmente." />
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-soft">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-[11px] uppercase tracking-wider text-brand-grayMid">
                <th className="px-4 py-3 font-semibold">Empresa</th>
                <th className="px-4 py-3 font-semibold">Segmento</th>
                <th className="px-4 py-3 font-semibold">Prioridad</th>
                <th className="px-4 py-3 font-semibold">Candidatos</th>
                <th className="px-4 py-3 font-semibold">Cobertura</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {filtered.map((co) => {
                const base = `/api/talent-market-maps/${map.id}/companies/${co.id}`;
                return (
                  <tr key={co.id} className="border-b border-slate-100 last:border-0">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-brand-black">{co.name}</span>
                        {co.ai_suggested ? <AiBadge /> : null}
                      </div>
                      {co.industry ? <p className="text-xs text-brand-grayMid">{co.industry}</p> : null}
                    </td>
                    <td className="px-4 py-3 text-xs text-brand-grayMid">{segmentName(co.segment_id)}</td>
                    <td className="px-4 py-3">
                      <span className={cn("rounded-full px-2 py-0.5 text-[10px] font-semibold", PRIORITY_TONE[co.priority])}>
                        {PRIORITY_LABELS[co.priority]}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-brand-grayMid">
                      {co.candidates_identified} ident. · {co.candidates_evaluated} eval. ·{" "}
                      <span className="font-semibold text-emerald-700">{co.high_fit_candidates} alto</span>
                    </td>
                    <td className="px-4 py-3">
                      <select
                        value={co.coverage_status}
                        onChange={(e) => run("upd", base, { method: "PATCH", body: JSON.stringify({ coverage_status: e.target.value }) })}
                        className={selectClassXs}
                      >
                        {(Object.keys(COMPANY_COVERAGE_LABELS) as CompanyCoverage[]).map((k) => (
                          <option key={k} value={k}>
                            {COMPANY_COVERAGE_LABELS[k]}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        type="button"
                        onClick={() => {
                          if (window.confirm(`¿Eliminar "${co.name}"?`)) void run("del", base, { method: "DELETE" });
                        }}
                        disabled={busy === "del"}
                        className="inline-flex h-8 w-8 items-center justify-center rounded-md text-brand-grayMid transition hover:bg-rose-50 hover:text-rose-700 disabled:opacity-60"
                        title="Eliminar empresa"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {adding ? (
        <AddCompanyModal map={map} onMap={onMap} onClose={() => setAdding(false)} />
      ) : null}
    </div>
  );
}

function AddCompanyModal({
  map,
  onMap,
  onClose,
}: {
  map: TalentMarketMapType;
  onMap: (m: TalentMarketMapType) => void;
  onClose: () => void;
}) {
  const [name, setName] = useState("");
  const [industry, setIndustry] = useState("");
  const [segmentId, setSegmentId] = useState<string>("");
  const [priority, setPriority] = useState<PriorityLevel>("medium");
  const [saving, setSaving] = useState(false);

  async function submit() {
    if (!name.trim()) return;
    setSaving(true);
    try {
      const updated = await apiFetch<TalentMarketMapType>(
        `/api/talent-market-maps/${map.id}/companies`,
        {
          method: "POST",
          body: JSON.stringify({
            name: name.trim(),
            industry: industry || null,
            segment_id: segmentId ? Number(segmentId) : null,
            priority,
          }),
        }
      );
      onMap(updated);
      onClose();
    } finally {
      setSaving(false);
    }
  }

  return (
    <ModalShell
      eyebrow="Nueva empresa"
      title="Agregar empresa target"
      onClose={onClose}
      footer={
        <>
          <button
            type="button"
            onClick={onClose}
            className="inline-flex items-center rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-brand-grayMid hover:bg-slate-50"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={submit}
            disabled={saving || !name.trim()}
            className="inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-4 py-2 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-blueDark disabled:opacity-60"
          >
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
            Agregar
          </button>
        </>
      }
    >
      <Field label="Nombre de la empresa">
        <input value={name} onChange={(e) => setName(e.target.value)} className={inputClass} placeholder="Ej. Falabella" />
      </Field>
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="Industria (opcional)">
          <input value={industry} onChange={(e) => setIndustry(e.target.value)} className={inputClass} placeholder="Retail" />
        </Field>
        <Field label="Prioridad">
          <select value={priority} onChange={(e) => setPriority(e.target.value as PriorityLevel)} className={inputClass}>
            {(Object.keys(PRIORITY_LABELS) as PriorityLevel[]).map((k) => (
              <option key={k} value={k}>
                {PRIORITY_LABELS[k]}
              </option>
            ))}
          </select>
        </Field>
      </div>
      <Field label="Segmento (opcional)">
        <select value={segmentId} onChange={(e) => setSegmentId(e.target.value)} className={inputClass}>
          <option value="">Sin segmento</option>
          {map.segments.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
      </Field>
    </ModalShell>
  );
}

// ===========================================================================
// Tab: Cargos equivalentes
// ===========================================================================

function CargosTab({
  map,
  onMap,
}: {
  map: TalentMarketMapType;
  onMap: (m: TalentMarketMapType) => void;
}) {
  const { busy, run } = useMapMutation(onMap);
  const [adding, setAdding] = useState(false);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-xs text-brand-grayMid">
          Cargos desde los cuales se puede atraer talento, ordenados por cercanía al perfil objetivo.
        </p>
        <button
          type="button"
          onClick={() => setAdding(true)}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-brand-grayMid transition hover:border-brand-blue/40 hover:text-brand-black"
        >
          <Plus className="h-4 w-4" />
          Agregar cargo
        </button>
      </div>

      {map.equivalent_roles.length === 0 ? (
        <EmptyBlock text="Sin cargos equivalentes todavía." />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {map.equivalent_roles.map((role) => (
            <RoleCard key={role.id} role={role} mapId={map.id} busy={busy} run={run} />
          ))}
        </div>
      )}

      {adding ? <AddRoleModal mapId={map.id} onMap={onMap} onClose={() => setAdding(false)} /> : null}
    </div>
  );
}

function RoleCard({
  role,
  mapId,
  busy,
  run,
}: {
  role: EquivalentRole;
  mapId: number;
  busy: string | null;
  run: (key: string, path: string, init?: RequestInit) => Promise<boolean>;
}) {
  const base = `/api/talent-market-maps/${mapId}/equivalent-roles/${role.id}`;
  const closenessTone: Record<ClosenessLevel, string> = {
    high: "bg-emerald-100 text-emerald-700",
    medium: "bg-amber-100 text-amber-700",
    low: "bg-slate-100 text-brand-grayMid",
  };
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-soft">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className={cn("rounded-full px-2 py-0.5 text-[10px] font-semibold", closenessTone[role.closeness])}>
              {CLOSENESS_LABELS[role.closeness]}
            </span>
            {role.ai_suggested ? <AiBadge /> : null}
            {role.candidate_count > 0 ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-brand-grayMid">
                <Users className="h-2.5 w-2.5" />
                {role.candidate_count}
              </span>
            ) : null}
          </div>
          <p className="mt-1.5 text-sm font-semibold text-brand-black">{role.title}</p>
          {role.seniority ? <p className="text-xs text-brand-grayMid">{role.seniority}</p> : null}
        </div>
        <button
          type="button"
          onClick={() => {
            if (window.confirm(`¿Eliminar el cargo "${role.title}"?`)) void run("del", base, { method: "DELETE" });
          }}
          disabled={busy === "del"}
          className="inline-flex h-8 w-8 items-center justify-center rounded-md text-brand-grayMid transition hover:bg-rose-50 hover:text-rose-700 disabled:opacity-60"
          title="Eliminar cargo"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>
      {role.rationale ? <p className="mt-2 text-[11px] italic text-brand-grayMid">{role.rationale}</p> : null}
      {role.industries.length > 0 ? (
        <div className="mt-2 flex flex-wrap gap-1">
          {role.industries.map((ind) => (
            <span key={ind} className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] text-brand-grayMid">
              {ind}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function AddRoleModal({
  mapId,
  onMap,
  onClose,
}: {
  mapId: number;
  onMap: (m: TalentMarketMapType) => void;
  onClose: () => void;
}) {
  const [title, setTitle] = useState("");
  const [seniority, setSeniority] = useState("");
  const [closeness, setCloseness] = useState<ClosenessLevel>("medium");
  const [industries, setIndustries] = useState("");
  const [saving, setSaving] = useState(false);

  async function submit() {
    if (!title.trim()) return;
    setSaving(true);
    try {
      const updated = await apiFetch<TalentMarketMapType>(
        `/api/talent-market-maps/${mapId}/equivalent-roles`,
        {
          method: "POST",
          body: JSON.stringify({
            title: title.trim(),
            seniority: seniority || null,
            closeness,
            industries: industries
              .split(",")
              .map((s) => s.trim())
              .filter(Boolean),
          }),
        }
      );
      onMap(updated);
      onClose();
    } finally {
      setSaving(false);
    }
  }

  return (
    <ModalShell
      eyebrow="Nuevo cargo equivalente"
      title="Agregar cargo equivalente"
      onClose={onClose}
      footer={
        <>
          <button
            type="button"
            onClick={onClose}
            className="inline-flex items-center rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-brand-grayMid hover:bg-slate-50"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={submit}
            disabled={saving || !title.trim()}
            className="inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-4 py-2 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-blueDark disabled:opacity-60"
          >
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
            Agregar
          </button>
        </>
      }
    >
      <Field label="Título del cargo">
        <input value={title} onChange={(e) => setTitle(e.target.value)} className={inputClass} placeholder="Ej. Head Comercial" />
      </Field>
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="Seniority (opcional)">
          <input value={seniority} onChange={(e) => setSeniority(e.target.value)} className={inputClass} placeholder="Gerencia" />
        </Field>
        <Field label="Cercanía">
          <select value={closeness} onChange={(e) => setCloseness(e.target.value as ClosenessLevel)} className={inputClass}>
            {(Object.keys(CLOSENESS_LABELS) as ClosenessLevel[]).map((k) => (
              <option key={k} value={k}>
                {CLOSENESS_LABELS[k]}
              </option>
            ))}
          </select>
        </Field>
      </div>
      <Field label="Industrias (separadas por coma)">
        <input value={industries} onChange={(e) => setIndustries(e.target.value)} className={inputClass} placeholder="Retail, Consumo masivo" />
      </Field>
    </ModalShell>
  );
}

// ===========================================================================
// Tab: Brechas
// ===========================================================================

function BrechasTab({
  map,
  onMap,
}: {
  map: TalentMarketMapType;
  onMap: (m: TalentMarketMapType) => void;
}) {
  const { busy, run } = useMapMutation(onMap);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-xs text-brand-grayMid">
          Brechas críticas que se repiten en las evaluaciones 360 del pipeline. Recalcula para incorporar nuevas evaluaciones.
        </p>
        <button
          type="button"
          onClick={() => run("recompute", `/api/talent-market-maps/${map.id}/gaps/recompute`, { method: "POST" })}
          disabled={busy === "recompute"}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-brand-grayMid transition hover:border-brand-blue/40 hover:text-brand-black disabled:opacity-60"
        >
          {busy === "recompute" ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          Recalcular brechas
        </button>
      </div>

      {map.gaps.length === 0 ? (
        <EmptyBlock text="Sin brechas detectadas. Evalúa candidatos en el pipeline y recalcula para ver las brechas repetidas." />
      ) : (
        <ul className="space-y-3">
          {map.gaps.map((gap) => (
            <GapRow key={gap.id} gap={gap} />
          ))}
        </ul>
      )}
    </div>
  );
}

function GapRow({ gap }: { gap: MarketGap }) {
  const pct = gap.total_evaluated > 0 ? Math.round((gap.frequency / gap.total_evaluated) * 100) : 0;
  return (
    <li className="rounded-xl border border-slate-200 bg-white p-4 shadow-soft">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-amber-500" />
          <span className="text-sm font-semibold text-brand-black">{gap.title}</span>
          <span className={cn("rounded-full px-2 py-0.5 text-[10px] font-semibold", IMPACT_TONE[gap.impact])}>
            {IMPACT_LABELS[gap.impact]}
          </span>
        </div>
        <span className="text-xs font-semibold text-brand-grayMid">
          {gap.frequency}/{gap.total_evaluated} candidatos ({pct}%)
        </span>
      </div>
      <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-slate-100">
        <div className="h-full rounded-full bg-amber-400" style={{ width: `${pct}%` }} />
      </div>
      {gap.evidence ? <p className="mt-2 text-xs text-brand-grayMid">{gap.evidence}</p> : null}
      {gap.recommendation ? (
        <p className="mt-2 rounded-lg bg-brand-blueSoft/40 px-3 py-2 text-xs text-brand-black">
          <span className="font-semibold">Sugerencia: </span>
          {gap.recommendation}
        </p>
      ) : null}
    </li>
  );
}

// ===========================================================================
// Tab: Recalibración
// ===========================================================================

function RecalibracionTab({
  map,
  onMap,
}: {
  map: TalentMarketMapType;
  onMap: (m: TalentMarketMapType) => void;
}) {
  const { busy, run } = useMapMutation(onMap);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-xs text-brand-grayMid">
          Recomendaciones para recalibrar la búsqueda, derivadas de la cobertura y las brechas detectadas.
        </p>
        <button
          type="button"
          onClick={() => run("regen", `/api/talent-market-maps/${map.id}/recommendations/regenerate`, { method: "POST" })}
          disabled={busy === "regen"}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-brand-grayMid transition hover:border-brand-blue/40 hover:text-brand-black disabled:opacity-60"
        >
          {busy === "regen" ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          Regenerar recomendaciones
        </button>
      </div>

      {map.recommendations.length === 0 ? (
        <EmptyBlock text="Sin recomendaciones. Recalcula brechas y regenera para obtener sugerencias de recalibración." />
      ) : (
        <ul className="space-y-3">
          {map.recommendations.map((rec) => (
            <RecommendationCard key={rec.id} rec={rec} mapId={map.id} busy={busy} run={run} />
          ))}
        </ul>
      )}
    </div>
  );
}

function RecommendationCard({
  rec,
  mapId,
  busy,
  run,
}: {
  rec: RecalibrationRecommendation;
  mapId: number;
  busy: string | null;
  run: (key: string, path: string, init?: RequestInit) => Promise<boolean>;
}) {
  const base = `/api/talent-market-maps/${mapId}/recommendations/${rec.id}`;
  const confTone: Record<"high" | "medium" | "low", string> = {
    high: "bg-emerald-100 text-emerald-700",
    medium: "bg-amber-100 text-amber-700",
    low: "bg-slate-100 text-brand-grayMid",
  };
  const statusTone: Record<string, string> = {
    suggested: "bg-slate-100 text-brand-grayMid",
    accepted: "bg-emerald-100 text-emerald-700",
    rejected: "bg-rose-100 text-rose-700",
  };
  return (
    <li
      className={cn(
        "rounded-xl border bg-white p-4 shadow-soft",
        rec.status === "accepted" ? "border-emerald-200" : rec.status === "rejected" ? "border-slate-200 opacity-70" : "border-slate-200"
      )}
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-brand-black">{rec.title}</span>
          <span className={cn("rounded-full px-2 py-0.5 text-[10px] font-semibold", confTone[rec.confidence])}>
            Confianza {PRIORITY_LABELS[rec.confidence].toLowerCase()}
          </span>
          {rec.generated_by === "ai" ? <AiBadge /> : null}
        </div>
        <span className={cn("rounded-full px-2 py-0.5 text-[10px] font-semibold", statusTone[rec.status])}>
          {RECOMMENDATION_STATUS_LABELS[rec.status]}
        </span>
      </div>
      <p className="mt-2 text-xs text-brand-grayMid">{rec.reason}</p>
      {rec.expected_impact ? (
        <p className="mt-1 text-[11px] text-brand-grayMid">
          <span className="font-semibold">Impacto esperado: </span>
          {rec.expected_impact}
        </p>
      ) : null}
      {rec.status === "suggested" ? (
        <div className="mt-3 flex items-center gap-2">
          <button
            type="button"
            onClick={() => run("dec", base, { method: "PATCH", body: JSON.stringify({ status: "accepted" }) })}
            disabled={busy === "dec"}
            className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-emerald-700 disabled:opacity-60"
          >
            <ThumbsUp className="h-3.5 w-3.5" />
            Aceptar
          </button>
          <button
            type="button"
            onClick={() => run("dec", base, { method: "PATCH", body: JSON.stringify({ status: "rejected" }) })}
            disabled={busy === "dec"}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-brand-grayMid transition hover:bg-slate-50 disabled:opacity-60"
          >
            <ThumbsDown className="h-3.5 w-3.5" />
            Descartar
          </button>
        </div>
      ) : null}
    </li>
  );
}

// ===========================================================================
// Misc
// ===========================================================================

function EmptyBlock({ text }: { text: string }) {
  return (
    <p className="rounded-2xl border border-dashed border-slate-200 bg-white px-4 py-10 text-center text-sm text-brand-grayMid shadow-soft">
      {text}
    </p>
  );
}
