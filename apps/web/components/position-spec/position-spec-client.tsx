"use client";

import {
  AlertCircle,
  Award,
  Building2,
  CheckSquare,
  FileText,
  HelpCircle,
  Lightbulb,
  ListTree,
  RefreshCw,
  Sparkles,
  Target,
} from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";
import { useDynamicId } from "@/lib/use-dynamic-id";
import type { PositionSpec } from "@/types/position-spec";

type PositionSpecClientProps = {
  mandateId?: string;
};

type RequirementItem = {
  requisito?: unknown;
  requirement?: unknown;
  tipo?: unknown;
  fuente_validacion?: unknown;
  peso_evaluacion?: unknown;
  preguntas_validacion?: unknown;
};

type ScoringItem = {
  dimension?: unknown;
  max_score?: unknown;
};

function getString(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

function getNumber(value: unknown, fallback = 0): number {
  return typeof value === "number" ? value : fallback;
}

function requirementText(req: RequirementItem): string {
  return getString(req.requisito, getString(req.requirement, "Requisito"));
}

function requirementWeight(req: RequirementItem): number {
  return getNumber(req.peso_evaluacion, 0);
}

export function PositionSpecClient({ mandateId: propId }: PositionSpecClientProps = {}) {
  const pathId = useDynamicId("mandatos");
  const mandateId = pathId && pathId !== "demo" ? pathId : propId || pathId;

  const [items, setItems] = useState<PositionSpec[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch<PositionSpec[]>(`/api/mandatos/${mandateId}/perfiles-objetivo`);
      setItems(data);
    } catch (requestError) {
      console.error(requestError);
      setError("No fue posible cargar perfiles objetivo para este mandato.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mandateId]);

  async function handleGenerate() {
    setGenerating(true);
    setError(null);
    try {
      const created = await apiFetch<PositionSpec>(
        `/api/mandatos/${mandateId}/generar-perfil-objetivo`,
        { method: "POST" }
      );
      setItems((previous) => [created, ...previous]);
    } catch (requestError) {
      console.error(requestError);
      setError("No fue posible generar el perfil objetivo.");
    } finally {
      setGenerating(false);
    }
  }

  if (loading) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center text-sm text-brand-grayMid">
        Cargando perfil objetivo...
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-soft">
        <div>
          <p className="text-sm font-semibold text-brand-black">Perfil objetivo del cargo</p>
          <p className="text-xs text-brand-grayMid">
            Genera la estructura evaluable del cargo desde el mandato. Usa gpt-4o-mini si está
            configurado; cae al motor determinista en caso contrario.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={handleGenerate} disabled={generating}>
            {generating ? "Generando perfil..." : "Generar perfil objetivo"}
          </Button>
          <button
            type="button"
            onClick={() => void load()}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-brand-grayMid transition hover:border-brand-blue/40 hover:text-brand-black"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Actualizar
          </button>
        </div>
      </div>

      {error ? (
        <p className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
          {error}
        </p>
      ) : null}

      {!items.length ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50/40 px-4 py-10 text-center">
          <Sparkles className="mx-auto h-8 w-8 text-brand-grayMid" />
          <p className="mt-3 text-sm font-semibold text-brand-black">
            Aún no hay perfil objetivo generado
          </p>
          <p className="mt-1 text-xs text-brand-grayMid">
            Pulsa "Generar perfil objetivo" para transformar el mandato en una estructura
            evaluable.
          </p>
        </div>
      ) : (
        items.map((spec) => <PositionSpecCard key={spec.id} spec={spec} />)
      )}
    </div>
  );
}

function PositionSpecCard({ spec }: { spec: PositionSpec }) {
  const mustHave = spec.must_have_requirements as RequirementItem[];
  const niceToHave = spec.nice_to_have_requirements as RequirementItem[];
  const scoringModel = spec.scoring_model as ScoringItem[];

  return (
    <article className="space-y-5">
      <header className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-blue">
          Perfil objetivo
        </p>
        <h2 className="mt-1 text-xl font-semibold tracking-tight text-brand-black">
          {spec.title}
        </h2>
        <p className="mt-2 text-sm text-brand-grayMid">{spec.executive_summary}</p>

        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <InfoBlock icon={Target} title="Misión del cargo" text={spec.role_mission} />
          <InfoBlock icon={Building2} title="Contexto" text={spec.search_context} />
        </div>
      </header>

      <div className="grid gap-5 lg:grid-cols-2">
        <RequirementsBlock
          title="Requisitos excluyentes"
          tone="emerald"
          items={mustHave}
        />
        <RequirementsBlock
          title="Requisitos deseables"
          tone="blue"
          items={niceToHave}
        />
      </div>

      <div className="grid gap-5 lg:grid-cols-3">
        <ListBlock
          icon={CheckSquare}
          title="Competencias técnicas"
          items={spec.technical_skills}
        />
        <ListBlock
          icon={ListTree}
          title="Competencias funcionales"
          items={spec.functional_skills}
        />
        <ListBlock
          icon={Award}
          title="Competencias de liderazgo"
          items={spec.leadership_skills}
        />
      </div>

      {scoringModel.length > 0 ? (
        <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
          <div className="flex items-center gap-2">
            <Target className="h-4 w-4 text-brand-blue" />
            <h3 className="text-base font-semibold text-brand-black">Matriz de scoring</h3>
          </div>
          <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {scoringModel.map((item, index) => (
              <div
                key={index}
                className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50/40 px-3 py-2"
              >
                <span className="text-sm text-brand-black">
                  {getString(item.dimension, `Dimensión ${index + 1}`)}
                </span>
                <span className="rounded-full bg-white px-2 py-0.5 text-xs font-semibold text-brand-blue ring-1 ring-brand-blue/20">
                  {getNumber(item.max_score, 0)} pts
                </span>
              </div>
            ))}
          </div>
        </article>
      ) : null}

      <div className="grid gap-5 lg:grid-cols-2">
        <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
          <div className="flex items-center gap-2">
            <HelpCircle className="h-4 w-4 text-brand-blue" />
            <h3 className="text-base font-semibold text-brand-black">
              Preguntas sugeridas para entrevista
            </h3>
          </div>
          {!spec.interview_questions.length ? (
            <p className="mt-2 text-sm text-brand-grayMid">No hay preguntas sugeridas.</p>
          ) : (
            <ol className="mt-3 space-y-2 text-sm text-brand-black">
              {spec.interview_questions.slice(0, 7).map((question, index) => (
                <li
                  key={index}
                  className="flex items-start gap-2 rounded-xl border border-slate-100 bg-slate-50/40 p-3"
                >
                  <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand-blueSoft text-[11px] font-semibold text-brand-blue">
                    {index + 1}
                  </span>
                  <span>{question}</span>
                </li>
              ))}
            </ol>
          )}
        </article>

        <article className="rounded-2xl border border-amber-200 bg-amber-50/40 p-6 shadow-soft">
          <div className="flex items-center gap-2 text-amber-700">
            <AlertCircle className="h-4 w-4" />
            <h3 className="text-base font-semibold">Señales de alerta</h3>
          </div>
          {!spec.red_flags.length ? (
            <p className="mt-2 text-sm text-brand-grayMid">Sin señales de alerta registradas.</p>
          ) : (
            <ul className="mt-3 space-y-2 text-sm text-brand-black">
              {spec.red_flags.map((flag, index) => (
                <li key={index} className="flex items-start gap-2">
                  <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />
                  <span>{flag}</span>
                </li>
              ))}
            </ul>
          )}
        </article>
      </div>

      {spec.evaluation_criteria.length > 0 ? (
        <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
          <div className="flex items-center gap-2">
            <Lightbulb className="h-4 w-4 text-brand-blue" />
            <h3 className="text-base font-semibold text-brand-black">Criterios de evaluación</h3>
          </div>
          <ul className="mt-3 grid gap-2 md:grid-cols-2">
            {spec.evaluation_criteria.map((criterion, index) => (
              <li
                key={index}
                className="flex items-start gap-2 rounded-xl border border-slate-100 bg-slate-50/40 p-2.5 text-sm text-brand-black"
              >
                <CheckSquare className="mt-0.5 h-3.5 w-3.5 shrink-0 text-brand-blue" />
                <span>{criterion}</span>
              </li>
            ))}
          </ul>
        </article>
      ) : null}

      <footer className="rounded-2xl border border-slate-100 bg-slate-50/40 p-3 text-[11px] text-brand-grayMid">
        Generado con modelo <span className="font-semibold">{spec.generated_by_model}</span> · prompt{" "}
        <span className="font-semibold">{spec.prompt_version}</span>
      </footer>
    </article>
  );
}

function InfoBlock({
  icon: Icon,
  title,
  text,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  text: string;
}) {
  return (
    <section className="rounded-xl border border-slate-200 bg-slate-50/40 p-3">
      <div className="flex items-center gap-1.5">
        <Icon className="h-3.5 w-3.5 text-brand-grayMid" />
        <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-grayMid">
          {title}
        </p>
      </div>
      <p className="mt-1 text-sm text-brand-black">
        {text || "No informado en el mandato."}
      </p>
    </section>
  );
}

function ListBlock({
  icon: Icon,
  title,
  items,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  items: string[];
}) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
      <div className="flex items-center gap-2">
        <Icon className="h-4 w-4 text-brand-blue" />
        <h3 className="text-sm font-semibold text-brand-black">{title}</h3>
      </div>
      {!items.length ? (
        <p className="mt-2 text-xs italic text-brand-grayMid">No definido en el perfil.</p>
      ) : (
        <ul className="mt-3 space-y-1.5 text-sm text-brand-black">
          {items.map((item, index) => (
            <li key={index} className="flex items-start gap-2">
              <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-brand-blue" />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}

function RequirementsBlock({
  title,
  tone,
  items,
}: {
  title: string;
  tone: "emerald" | "blue";
  items: RequirementItem[];
}) {
  const toneClasses =
    tone === "emerald"
      ? "border-emerald-200 bg-emerald-50/40"
      : "border-blue-200 bg-blue-50/40";
  const accent = tone === "emerald" ? "text-emerald-700" : "text-blue-700";
  const badgeClasses =
    tone === "emerald"
      ? "bg-emerald-100 text-emerald-700"
      : "bg-blue-100 text-blue-700";

  return (
    <article className={`rounded-2xl border ${toneClasses} p-6 shadow-soft`}>
      <div className={`flex items-center gap-2 ${accent}`}>
        <FileText className="h-4 w-4" />
        <h3 className="text-base font-semibold">{title}</h3>
      </div>
      {!items.length ? (
        <p className="mt-2 text-sm text-brand-grayMid">No definidos.</p>
      ) : (
        <ul className="mt-3 space-y-2 text-sm text-brand-black">
          {items.map((req, index) => (
            <li
              key={index}
              className="flex items-start justify-between gap-3 rounded-xl border border-white/60 bg-white/70 p-3"
            >
              <span className="font-medium">{requirementText(req)}</span>
              {requirementWeight(req) > 0 ? (
                <span
                  className={`shrink-0 rounded-full px-2 py-0.5 text-[11px] font-semibold ${badgeClasses}`}
                >
                  Peso {requirementWeight(req)}
                </span>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}
