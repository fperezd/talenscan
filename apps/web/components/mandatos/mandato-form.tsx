"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Combobox } from "@/components/ui/combobox";
import { MultiCombobox } from "@/components/ui/multi-combobox";
import {
  CITIES,
  COUNTRIES,
  INDUSTRIES,
  MANDATE_STATUSES,
  REPORT_TO_OPTIONS,
  SENIORITIES,
  TARGET_ROLES,
  URGENCIES,
  WORK_MODES,
} from "@/lib/catalog";
import type { MandateStatus, SearchMandateInput } from "@/types/search-mandate";

type MandatoFormProps = {
  initialValue?: SearchMandateInput;
  submitLabel: string;
  onSubmit: (value: SearchMandateInput) => Promise<void>;
};

type FormValue = {
  client_name: string;
  search_title: string;
  target_role: string;
  industry: string;
  country: string;
  city: string;
  work_mode: string;
  seniority_level: string;
  reports_to: string;
  business_context: string;
  role_objective: string;
  key_challenges: string;
  main_responsibilities: string;
  expected_results: string;
  must_have_requirements: string;
  nice_to_have_requirements: string;
  target_companies: string;
  target_industries: string[];
  equivalent_roles: string;
  compensation_context: string;
  urgency: string;
  target_hire_date: string;
  comments: string;
  status: MandateStatus;
};

function linesToList(value: string): string[] {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

function listToLines(value?: string[]): string {
  return (value || []).join("\n");
}

function toFormValue(initialValue?: SearchMandateInput): FormValue {
  return {
    client_name: initialValue?.client_name || "",
    search_title: initialValue?.search_title || "",
    target_role: initialValue?.target_role || "",
    industry: initialValue?.industry || "",
    country: initialValue?.country ?? "Chile",
    city: initialValue?.city ?? "Santiago",
    work_mode: initialValue?.work_mode || "",
    seniority_level: initialValue?.seniority_level || "",
    reports_to: initialValue?.reports_to || "",
    business_context: initialValue?.business_context || "",
    role_objective: initialValue?.role_objective || "",
    key_challenges: initialValue?.key_challenges || "",
    main_responsibilities: listToLines(initialValue?.main_responsibilities),
    expected_results: listToLines(initialValue?.expected_results),
    must_have_requirements: listToLines(initialValue?.must_have_requirements),
    nice_to_have_requirements: listToLines(initialValue?.nice_to_have_requirements),
    target_companies: listToLines(initialValue?.target_companies),
    target_industries: initialValue?.target_industries || [],
    equivalent_roles: listToLines(initialValue?.equivalent_roles),
    compensation_context: initialValue?.compensation_context || "",
    urgency: initialValue?.urgency || "",
    target_hire_date: initialValue?.target_hire_date || "",
    comments: initialValue?.comments || "",
    status: initialValue?.status || "Borrador",
  };
}

const fieldLabel = "block text-xs font-medium uppercase tracking-wide text-brand-grayMid";
const textInputClass =
  "mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-brand-black placeholder:text-brand-grayMid focus:border-brand-blue focus:outline-none focus:ring-2 focus:ring-brand-blue/15";

export function MandatoForm({ initialValue, submitLabel, onSubmit }: MandatoFormProps) {
  const [value, setValue] = useState<FormValue>(() => toFormValue(initialValue));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const lastSeedIndustryRef = useRef<string>(value.industry);

  const canSubmit = useMemo(() => {
    return Boolean(value.client_name.trim() && value.search_title.trim() && value.target_role.trim());
  }, [value]);

  function update<K extends keyof FormValue>(key: K, next: FormValue[K]) {
    setValue((previous) => ({ ...previous, [key]: next }));
  }

  // Pre-cargar la industria del cliente como primera industria objetivo.
  useEffect(() => {
    const currentIndustry = value.industry.trim();
    if (!currentIndustry) return;
    if (currentIndustry === lastSeedIndustryRef.current) return;
    lastSeedIndustryRef.current = currentIndustry;
    if (value.target_industries.includes(currentIndustry)) return;
    setValue((previous) => ({
      ...previous,
      target_industries: [currentIndustry, ...previous.target_industries.filter((i) => i !== currentIndustry)],
    }));
  }, [value.industry, value.target_industries]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError(null);

    try {
      await onSubmit({
        client_name: value.client_name.trim(),
        search_title: value.search_title.trim(),
        target_role: value.target_role.trim(),
        industry: value.industry.trim() || null,
        country: value.country.trim() || null,
        city: value.city.trim() || null,
        work_mode: value.work_mode.trim() || null,
        seniority_level: value.seniority_level.trim() || null,
        reports_to: value.reports_to.trim() || null,
        business_context: value.business_context.trim() || null,
        role_objective: value.role_objective.trim() || null,
        key_challenges: value.key_challenges.trim() || null,
        main_responsibilities: linesToList(value.main_responsibilities),
        expected_results: linesToList(value.expected_results),
        must_have_requirements: linesToList(value.must_have_requirements),
        nice_to_have_requirements: linesToList(value.nice_to_have_requirements),
        target_companies: linesToList(value.target_companies),
        target_industries: value.target_industries.filter((entry) => entry.trim().length > 0),
        equivalent_roles: linesToList(value.equivalent_roles),
        compensation_context: value.compensation_context.trim() || null,
        urgency: value.urgency.trim() || null,
        target_hire_date: value.target_hire_date.trim() || null,
        comments: value.comments.trim() || null,
        status: value.status,
      });
    } catch (submitError) {
      setError("No fue posible guardar el mandato. Revisa los campos e intenta nuevamente.");
      console.error(submitError);
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="space-y-8" onSubmit={handleSubmit}>
      <section>
        <h3 className="text-sm font-semibold text-brand-black">Contexto del cliente</h3>
        <p className="text-xs text-brand-grayMid">Identificación del cliente y del cargo objetivo.</p>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <label htmlFor="client_name" className={fieldLabel}>Cliente</label>
            <input
              id="client_name"
              className={textInputClass}
              value={value.client_name}
              onChange={(event) => update("client_name", event.target.value)}
              placeholder="Empresa cliente"
              required
            />
          </div>
          <div>
            <label htmlFor="search_title" className={fieldLabel}>Título del mandato</label>
            <input
              id="search_title"
              className={textInputClass}
              value={value.search_title}
              onChange={(event) => update("search_title", event.target.value)}
              placeholder="Búsqueda Gerente Comercial Retail"
              required
            />
          </div>
          <div>
            <label htmlFor="target_role" className={fieldLabel}>Cargo requerido</label>
            <Combobox
              id="target_role"
              value={value.target_role}
              onChange={(next) => update("target_role", next)}
              options={TARGET_ROLES}
              placeholder="Selecciona o escribe el cargo"
            />
          </div>
          <div>
            <label htmlFor="industry" className={fieldLabel}>Industria</label>
            <Combobox
              id="industry"
              value={value.industry}
              onChange={(next) => update("industry", next)}
              options={INDUSTRIES}
              placeholder="Industria del cliente"
            />
          </div>
        </div>
      </section>

      <section>
        <h3 className="text-sm font-semibold text-brand-black">Ubicación y modalidad</h3>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          <div>
            <label htmlFor="country" className={fieldLabel}>País</label>
            <Combobox
              id="country"
              value={value.country}
              onChange={(next) => update("country", next)}
              options={COUNTRIES}
              placeholder="Chile"
            />
          </div>
          <div>
            <label htmlFor="city" className={fieldLabel}>Ciudad</label>
            <Combobox
              id="city"
              value={value.city}
              onChange={(next) => update("city", next)}
              options={CITIES}
              placeholder="Santiago"
            />
          </div>
          <div>
            <label htmlFor="work_mode" className={fieldLabel}>Modalidad</label>
            <Combobox
              id="work_mode"
              value={value.work_mode}
              onChange={(next) => update("work_mode", next)}
              options={WORK_MODES}
              placeholder="Híbrido"
            />
          </div>
        </div>
      </section>

      <section>
        <h3 className="text-sm font-semibold text-brand-black">Nivel y reportabilidad</h3>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <label htmlFor="seniority_level" className={fieldLabel}>Nivel de seniority</label>
            <Combobox
              id="seniority_level"
              value={value.seniority_level}
              onChange={(next) => update("seniority_level", next)}
              options={SENIORITIES}
              placeholder="Senior"
            />
          </div>
          <div>
            <label htmlFor="reports_to" className={fieldLabel}>Reporta a</label>
            <Combobox
              id="reports_to"
              value={value.reports_to}
              onChange={(next) => update("reports_to", next)}
              options={REPORT_TO_OPTIONS}
              placeholder="CEO / Gerente General"
            />
          </div>
        </div>
      </section>

      <section>
        <h3 className="text-sm font-semibold text-brand-black">Contexto del negocio</h3>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <label htmlFor="business_context" className={fieldLabel}>Contexto del negocio</label>
            <textarea
              id="business_context"
              className={`${textInputClass} min-h-24`}
              value={value.business_context}
              onChange={(event) => update("business_context", event.target.value)}
              placeholder="Etapa de la empresa, escala, mercado, retos actuales..."
            />
          </div>
          <div>
            <label htmlFor="role_objective" className={fieldLabel}>Objetivo del cargo</label>
            <textarea
              id="role_objective"
              className={`${textInputClass} min-h-24`}
              value={value.role_objective}
              onChange={(event) => update("role_objective", event.target.value)}
              placeholder="¿Para qué se crea o se renueva este cargo?"
            />
          </div>
        </div>
      </section>

      <section>
        <h3 className="text-sm font-semibold text-brand-black">Responsabilidades y resultados</h3>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <label htmlFor="main_responsibilities" className={fieldLabel}>Responsabilidades (una por línea)</label>
            <textarea
              id="main_responsibilities"
              className={`${textInputClass} min-h-28`}
              value={value.main_responsibilities}
              onChange={(event) => update("main_responsibilities", event.target.value)}
            />
          </div>
          <div>
            <label htmlFor="expected_results" className={fieldLabel}>Resultados esperados (uno por línea)</label>
            <textarea
              id="expected_results"
              className={`${textInputClass} min-h-28`}
              value={value.expected_results}
              onChange={(event) => update("expected_results", event.target.value)}
            />
          </div>
        </div>
      </section>

      <section>
        <h3 className="text-sm font-semibold text-brand-black">Requisitos</h3>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <label htmlFor="must_have_requirements" className={fieldLabel}>Requisitos excluyentes (uno por línea)</label>
            <textarea
              id="must_have_requirements"
              className={`${textInputClass} min-h-28`}
              value={value.must_have_requirements}
              onChange={(event) => update("must_have_requirements", event.target.value)}
            />
          </div>
          <div>
            <label htmlFor="nice_to_have_requirements" className={fieldLabel}>Requisitos deseables (uno por línea)</label>
            <textarea
              id="nice_to_have_requirements"
              className={`${textInputClass} min-h-28`}
              value={value.nice_to_have_requirements}
              onChange={(event) => update("nice_to_have_requirements", event.target.value)}
            />
          </div>
        </div>
      </section>

      <section>
        <h3 className="text-sm font-semibold text-brand-black">Mercado objetivo</h3>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <label htmlFor="target_companies" className={fieldLabel}>Empresas objetivo (una por línea)</label>
            <textarea
              id="target_companies"
              className={`${textInputClass} min-h-24`}
              value={value.target_companies}
              onChange={(event) => update("target_companies", event.target.value)}
            />
          </div>
          <div>
            <label htmlFor="target_industries" className={fieldLabel}>Industrias objetivo</label>
            <p className="mt-1 text-[11px] text-brand-grayMid">
              Selecciona o escribe industrias para mapeo de mercado. La industria del cliente se
              agrega automáticamente.
            </p>
            <div className="mt-2">
              <MultiCombobox
                id="target_industries"
                value={value.target_industries}
                onChange={(next) => update("target_industries", next)}
                options={INDUSTRIES}
                placeholder="Agrega industrias..."
                addLabel="Agregar industria"
              />
            </div>
          </div>
          <div>
            <label htmlFor="equivalent_roles" className={fieldLabel}>Cargos equivalentes (uno por línea)</label>
            <textarea
              id="equivalent_roles"
              className={`${textInputClass} min-h-24`}
              value={value.equivalent_roles}
              onChange={(event) => update("equivalent_roles", event.target.value)}
            />
          </div>
          <div>
            <label htmlFor="compensation_context" className={fieldLabel}>Contexto de compensación</label>
            <textarea
              id="compensation_context"
              className={`${textInputClass} min-h-24`}
              value={value.compensation_context}
              onChange={(event) => update("compensation_context", event.target.value)}
              placeholder="Rango referencial, paquete, bonos, etc."
            />
          </div>
        </div>
      </section>

      <section>
        <h3 className="text-sm font-semibold text-brand-black">Estado y prioridad</h3>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          <div>
            <label htmlFor="urgency" className={fieldLabel}>Urgencia</label>
            <Combobox
              id="urgency"
              value={value.urgency}
              onChange={(next) => update("urgency", next)}
              options={URGENCIES}
              placeholder="Alta"
              allowCustom={false}
            />
          </div>
          <div>
            <label htmlFor="target_hire_date" className={fieldLabel}>Fecha objetivo de contratación</label>
            <input
              id="target_hire_date"
              type="date"
              className={textInputClass}
              value={value.target_hire_date}
              onChange={(event) => update("target_hire_date", event.target.value)}
            />
          </div>
          <div>
            <label htmlFor="status" className={fieldLabel}>Estado</label>
            <Combobox
              id="status"
              value={value.status}
              onChange={(next) => update("status", (next as MandateStatus) || "Borrador")}
              options={MANDATE_STATUSES}
              placeholder="Borrador"
              allowCustom={false}
            />
          </div>
        </div>
        <div className="mt-4">
          <label htmlFor="key_challenges" className={fieldLabel}>Riesgos o brechas clave</label>
          <textarea
            id="key_challenges"
            className={`${textInputClass} min-h-24`}
            value={value.key_challenges}
            onChange={(event) => update("key_challenges", event.target.value)}
          />
        </div>
      </section>

      <section>
        <label htmlFor="comments" className={fieldLabel}>Comentarios del consultor</label>
        <textarea
          id="comments"
          className={`${textInputClass} min-h-24`}
          value={value.comments}
          onChange={(event) => update("comments", event.target.value)}
          placeholder="Notas internas, contexto comercial, observaciones de la primera reunión..."
        />
      </section>

      {error ? (
        <p className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>
      ) : null}

      <div className="flex flex-wrap gap-2">
        <Button type="submit" disabled={!canSubmit || saving}>
          {saving ? "Guardando..." : submitLabel}
        </Button>
        <Button type="button" variant="secondary" onClick={() => update("status", "Borrador")}>
          Guardar borrador
        </Button>
      </div>
    </form>
  );
}
