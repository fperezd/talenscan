"use client";

import {
  AlertTriangle,
  CheckCircle2,
  FileText,
  Linkedin,
  Loader2,
  Sparkles,
  Upload,
  X,
} from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { API_BASE_URL, apiFetch } from "@/lib/api";
import { useDynamicId } from "@/lib/use-dynamic-id";
import { cn } from "@/lib/utils";
import type {
  BulkEvaluationItem,
  BulkEvaluationResponse,
  BulkLinkedInItem,
  BulkLinkedInResponse,
} from "@/types/bulk";
import type { PositionSpec } from "@/types/position-spec";

type EvaluarCandidatosClientProps = {
  mandateId?: string;
};

type Tab = "cv" | "linkedin";

function formatBytes(size: number): string {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function statusTone(status: "created" | "duplicate" | "error"): string {
  if (status === "created") return "bg-emerald-100 text-emerald-700";
  if (status === "duplicate") return "bg-amber-100 text-amber-700";
  return "bg-rose-100 text-rose-700";
}

function statusLabel(status: "created" | "duplicate" | "error"): string {
  if (status === "created") return "Procesado";
  if (status === "duplicate") return "Duplicado";
  return "Error";
}

export function EvaluarCandidatosClient({ mandateId: propId }: EvaluarCandidatosClientProps = {}) {
  const pathId = useDynamicId("mandatos");
  const mandateId = pathId && pathId !== "demo" ? pathId : propId || pathId;

  const [tab, setTab] = useState<Tab>("cv");
  const [positionSpecs, setPositionSpecs] = useState<PositionSpec[]>([]);
  const [selectedSpecId, setSelectedSpecId] = useState<string>("");
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [linkedinEntries, setLinkedinEntries] = useState<{ url: string; profile_text: string }[]>([
    { url: "", profile_text: "" },
  ]);
  const [linkedinEvaluate, setLinkedinEvaluate] = useState(true);
  const [dragOver, setDragOver] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cvResults, setCvResults] = useState<BulkEvaluationItem[] | null>(null);
  const [linkedinResults, setLinkedinResults] = useState<BulkLinkedInItem[] | null>(null);

  useEffect(() => {
    async function loadSpecs() {
      try {
        const specs = await apiFetch<PositionSpec[]>(
          `/api/mandatos/${mandateId}/perfiles-objetivo`
        );
        setPositionSpecs(specs);
        if (specs.length > 0) {
          setSelectedSpecId(String(specs[0].id));
        }
      } catch (requestError) {
        console.error(requestError);
      }
    }

    void loadSpecs();
  }, [mandateId]);

  const validFiles = useMemo(
    () => selectedFiles.filter((file) => /\.(pdf|docx?|DOC)$/i.test(file.name)),
    [selectedFiles]
  );

  const canSubmitCv = useMemo(() => {
    return Boolean(selectedSpecId) && validFiles.length > 0;
  }, [selectedSpecId, validFiles]);

  const canSubmitLinkedIn = useMemo(() => {
    return linkedinEntries.some((entry) => entry.url.trim().length > 0);
  }, [linkedinEntries]);

  function handleFilesAdded(incoming: FileList | File[] | null) {
    if (!incoming) return;
    const files = Array.from(incoming).filter((file) => /\.(pdf|docx?|DOC)$/i.test(file.name));
    if (files.length === 0) {
      setError("Sólo se aceptan archivos PDF, DOC o DOCX.");
      return;
    }
    setError(null);
    setSelectedFiles((prev) => {
      const existingNames = new Set(prev.map((f) => f.name));
      const novel = files.filter((f) => !existingNames.has(f.name));
      return [...prev, ...novel];
    });
  }

  function removeFile(name: string) {
    setSelectedFiles((prev) => prev.filter((f) => f.name !== name));
  }

  async function submitCv(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmitCv) return;
    setSubmitting(true);
    setError(null);
    setCvResults(null);

    try {
      const formData = new FormData();
      for (const file of validFiles) {
        formData.append("files", file);
      }
      const response = await fetch(
        `${API_BASE_URL}/api/mandatos/${mandateId}/evaluaciones-bulk?position_spec_id=${selectedSpecId}`,
        { method: "POST", body: formData }
      );
      if (!response.ok) {
        const detail = await response.text();
        throw new Error(detail || "Error al procesar los CVs");
      }
      const data = (await response.json()) as BulkEvaluationResponse;
      setCvResults(data.items);
      setSelectedFiles([]);
    } catch (requestError) {
      console.error(requestError);
      setError("No fue posible procesar los CVs. Intenta nuevamente.");
    } finally {
      setSubmitting(false);
    }
  }

  async function submitLinkedIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmitLinkedIn) return;
    setSubmitting(true);
    setError(null);
    setLinkedinResults(null);
    try {
      const validEntries = linkedinEntries
        .map((entry) => ({
          url: entry.url.trim(),
          profile_text: entry.profile_text.trim() || null,
        }))
        .filter((entry) => entry.url.length > 0);
      const body: {
        entries: typeof validEntries;
        position_spec_id?: number;
      } = { entries: validEntries };
      if (linkedinEvaluate && selectedSpecId) {
        body.position_spec_id = Number(selectedSpecId);
      }
      const data = await apiFetch<BulkLinkedInResponse>(
        `/api/mandatos/${mandateId}/candidatos-desde-linkedin`,
        {
          method: "POST",
          body: JSON.stringify(body),
        }
      );
      setLinkedinResults(data.items);
      setLinkedinEntries([{ url: "", profile_text: "" }]);
    } catch (requestError) {
      console.error(requestError);
      setError("No fue posible procesar las URLs de LinkedIn. Verifica el formato.");
    } finally {
      setSubmitting(false);
    }
  }

  function updateLinkedinEntry(index: number, patch: Partial<{ url: string; profile_text: string }>) {
    setLinkedinEntries((prev) => prev.map((entry, i) => (i === index ? { ...entry, ...patch } : entry)));
  }

  function addLinkedinEntry() {
    setLinkedinEntries((prev) => [...prev, { url: "", profile_text: "" }]);
  }

  function removeLinkedinEntry(index: number) {
    setLinkedinEntries((prev) => {
      const next = prev.filter((_, i) => i !== index);
      return next.length === 0 ? [{ url: "", profile_text: "" }] : next;
    });
  }

  const noSpecs = positionSpecs.length === 0;

  return (
    <div className="space-y-6">
      {noSpecs ? (
        <div className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50/40 px-4 py-3 text-sm text-amber-800">
          <Sparkles className="mt-0.5 h-4 w-4 shrink-0" />
          <div>
            <p className="font-semibold">Aún no existe perfil objetivo para este mandato.</p>
            <p className="mt-0.5">
              Ve a la pestaña <span className="font-semibold">Perfil objetivo</span> y genera uno
              antes de evaluar candidatos.
            </p>
          </div>
        </div>
      ) : null}

      <section>
        <label htmlFor="spec_selector" className="block text-xs font-semibold uppercase tracking-wider text-brand-grayMid">
          Perfil objetivo a evaluar
        </label>
        <select
          id="spec_selector"
          className="mt-2 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-brand-black focus:border-brand-blue focus:outline-none focus:ring-2 focus:ring-brand-blue/15 md:max-w-md"
          value={selectedSpecId}
          onChange={(event) => setSelectedSpecId(event.target.value)}
          disabled={noSpecs}
        >
          {positionSpecs.map((spec) => (
            <option key={spec.id} value={spec.id}>
              {spec.title}
            </option>
          ))}
        </select>
        <p className="mt-1 text-xs text-brand-grayMid">
          La Evaluación 360 se generará automáticamente con este perfil. Los candidatos quedarán en la columna "Evaluados" del pipeline.
        </p>
      </section>

      <div className="flex border-b border-slate-200">
        <button
          type="button"
          onClick={() => setTab("cv")}
          className={cn(
            "flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium transition -mb-px",
            tab === "cv"
              ? "border-brand-blue text-brand-blue"
              : "border-transparent text-brand-grayMid hover:text-brand-black"
          )}
        >
          <Upload className="h-3.5 w-3.5" />
          Subir CVs ({selectedFiles.length})
        </button>
        <button
          type="button"
          onClick={() => setTab("linkedin")}
          className={cn(
            "flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium transition -mb-px",
            tab === "linkedin"
              ? "border-brand-blue text-brand-blue"
              : "border-transparent text-brand-grayMid hover:text-brand-black"
          )}
        >
          <Linkedin className="h-3.5 w-3.5" />
          Pegar URLs LinkedIn
        </button>
      </div>

      {tab === "cv" ? (
        <form onSubmit={submitCv} className="space-y-4">
          <label
            onDragOver={(event) => {
              event.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(event) => {
              event.preventDefault();
              setDragOver(false);
              handleFilesAdded(event.dataTransfer.files);
            }}
            className={cn(
              "flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed bg-slate-50/40 p-8 text-center transition",
              dragOver
                ? "border-brand-blue bg-brand-blueSoft"
                : "border-slate-300 hover:border-brand-blue/40 hover:bg-slate-50"
            )}
          >
            <Upload className="h-7 w-7 text-brand-grayMid" />
            <p className="mt-3 text-sm font-semibold text-brand-black">
              Arrastra uno o varios CVs o haz clic para seleccionar
            </p>
            <p className="mt-1 text-xs text-brand-grayMid">
              PDF, DOC o DOCX. El nombre del candidato se extrae del archivo.
            </p>
            <input
              type="file"
              multiple
              accept=".pdf,.doc,.docx"
              className="hidden"
              onChange={(event) => handleFilesAdded(event.target.files)}
            />
          </label>

          {selectedFiles.length > 0 ? (
            <div className="space-y-1.5">
              {selectedFiles.map((file) => (
                <div
                  key={file.name}
                  className="flex items-center justify-between gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2"
                >
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-brand-blue" />
                    <div>
                      <p className="text-sm font-medium text-brand-black">{file.name}</p>
                      <p className="text-[11px] text-brand-grayMid">{formatBytes(file.size)}</p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => removeFile(file.name)}
                    aria-label={`Quitar ${file.name}`}
                    className="rounded p-1 text-brand-grayMid hover:bg-slate-100 hover:text-brand-black"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          ) : null}

          {error ? (
            <p className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
              {error}
            </p>
          ) : null}

          <div className="flex items-center gap-3">
            <Button type="submit" disabled={!canSubmitCv || submitting}>
              {submitting ? (
                <span className="inline-flex items-center gap-1.5">
                  <Loader2 className="h-3.5 w-3.5 animate-spin" /> Procesando...
                </span>
              ) : (
                `Procesar ${validFiles.length} CV${validFiles.length === 1 ? "" : "s"}`
              )}
            </Button>
          </div>
        </form>
      ) : (
        <form onSubmit={submitLinkedIn} className="space-y-4">
          <div className="space-y-3">
            {linkedinEntries.map((entry, index) => (
              <div
                key={index}
                className="rounded-xl border border-slate-200 bg-white p-3"
              >
                <div className="flex items-center justify-between">
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-grayMid">
                    Candidato {index + 1}
                  </p>
                  {linkedinEntries.length > 1 ? (
                    <button
                      type="button"
                      onClick={() => removeLinkedinEntry(index)}
                      aria-label="Quitar candidato"
                      className="rounded p-1 text-brand-grayMid hover:bg-slate-100 hover:text-brand-black"
                    >
                      <X className="h-3.5 w-3.5" />
                    </button>
                  ) : null}
                </div>
                <input
                  type="url"
                  value={entry.url}
                  onChange={(event) => updateLinkedinEntry(index, { url: event.target.value })}
                  placeholder="https://www.linkedin.com/in/perezdiazfernando"
                  className="mt-2 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-brand-black placeholder:text-brand-grayMid focus:border-brand-blue focus:outline-none focus:ring-2 focus:ring-brand-blue/15"
                />
                <textarea
                  value={entry.profile_text}
                  onChange={(event) =>
                    updateLinkedinEntry(index, { profile_text: event.target.value })
                  }
                  placeholder="Opcional: pega aquí el contenido del perfil LinkedIn (Acerca de + Experiencia + Educación). Esto permite generar la Evaluación 360 con datos reales en vez de un placeholder."
                  className="mt-2 min-h-[100px] w-full rounded-lg border border-slate-200 bg-slate-50/40 px-3 py-2 text-xs text-brand-black placeholder:text-brand-grayMid focus:border-brand-blue focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-blue/15"
                />
              </div>
            ))}
            <button
              type="button"
              onClick={addLinkedinEntry}
              className="inline-flex items-center gap-1.5 rounded-lg border border-dashed border-slate-300 bg-white px-3 py-2 text-sm font-medium text-brand-grayMid transition hover:border-brand-blue/40 hover:text-brand-blue"
            >
              <Linkedin className="h-3.5 w-3.5" />
              Agregar otro candidato LinkedIn
            </button>
          </div>

          <label className="flex items-start gap-2 rounded-xl border border-slate-200 bg-slate-50/40 px-3 py-2">
            <input
              type="checkbox"
              checked={linkedinEvaluate}
              onChange={(event) => setLinkedinEvaluate(event.target.checked)}
              className="mt-0.5 h-3.5 w-3.5 accent-brand-blue"
              disabled={noSpecs}
            />
            <span className="text-xs text-brand-black">
              <span className="font-medium">Generar Evaluación 360 al agregar</span>
              <span className="block mt-0.5 text-brand-grayMid">
                Si pegas el texto del perfil, la Evaluación 360 usará esos datos como CV equivalente.
                Si no, el candidato cae con score basado sólo en la URL (placeholder, para evaluación real
                sube el CV después desde la ficha del candidato).
              </span>
            </span>
          </label>

          {error ? (
            <p className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
              {error}
            </p>
          ) : null}

          <div className="flex flex-col gap-1.5">
            <Button type="submit" disabled={!canSubmitLinkedIn || submitting}>
              {submitting ? (
                <span className="inline-flex items-center gap-1.5">
                  <Loader2 className="h-3.5 w-3.5 animate-spin" /> Consultando LinkedIn vía Apify...
                </span>
              ) : linkedinEvaluate && selectedSpecId ? (
                "Agregar y generar evaluaciones 360"
              ) : (
                "Agregar candidatos al pipeline"
              )}
            </Button>
            {submitting ? (
              <p className="text-[11px] text-brand-grayMid">
                Cada URL toma 10-30 segundos cuando se enriquece desde LinkedIn. No cierres esta pestaña.
              </p>
            ) : null}
          </div>
        </form>
      )}

      {cvResults && cvResults.length > 0 ? (
        <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
          <div className="flex items-center gap-2 text-brand-black">
            <CheckCircle2 className="h-5 w-5 text-emerald-500" />
            <h3 className="text-base font-semibold">Resultados de la carga</h3>
          </div>
          <p className="mt-1 text-xs text-brand-grayMid">
            {cvResults.filter((r) => r.status === "created").length} procesados ·{" "}
            {cvResults.filter((r) => r.status === "duplicate").length} duplicados ·{" "}
            {cvResults.filter((r) => r.status === "error").length} con errores. Los candidatos están en el pipeline en la columna "Evaluados".
          </p>
          <ul className="mt-4 space-y-2">
            {cvResults.map((item) => (
              <li
                key={item.file_name}
                className="flex items-center justify-between gap-3 rounded-xl border border-slate-100 bg-slate-50/40 px-3 py-2"
              >
                <div className="min-w-0 flex items-center gap-2">
                  <FileText className="h-3.5 w-3.5 shrink-0 text-brand-grayMid" />
                  <div>
                    <p className="truncate text-sm font-medium text-brand-black">{item.file_name}</p>
                    {item.candidate_name ? (
                      <p className="text-[11px] text-brand-grayMid">{item.candidate_name}</p>
                    ) : null}
                    {item.error ? (
                      <p className="text-[11px] text-rose-700">{item.error}</p>
                    ) : null}
                  </div>
                </div>
                <span className={cn("shrink-0 rounded-full px-2 py-0.5 text-[11px] font-medium", statusTone(item.status))}>
                  {statusLabel(item.status)}
                </span>
              </li>
            ))}
          </ul>
          <a
            href={`/mandatos/${mandateId}/pipeline`}
            className="mt-4 inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-3.5 py-2 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-blueDark"
          >
            Ver pipeline
          </a>
        </article>
      ) : null}

      {linkedinResults && linkedinResults.length > 0 ? (
        <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
          <div className="flex items-center gap-2 text-brand-black">
            <Linkedin className="h-5 w-5 text-brand-blue" />
            <h3 className="text-base font-semibold">URLs procesadas</h3>
          </div>
          <p className="mt-1 text-xs text-brand-grayMid">
            {linkedinResults.filter((r) => r.status === "created").length} agregados ·{" "}
            {linkedinResults.filter((r) => r.status === "duplicate").length} duplicados ·{" "}
            {linkedinResults.filter((r) => r.status === "error").length} con errores.
          </p>
          <ul className="mt-4 space-y-2">
            {linkedinResults.map((item) => (
              <li
                key={item.url}
                className="flex items-center justify-between gap-3 rounded-xl border border-slate-100 bg-slate-50/40 px-3 py-2"
              >
                <div className="min-w-0">
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noreferrer noopener"
                    className="truncate text-sm font-medium text-brand-blue hover:underline"
                  >
                    {item.url}
                  </a>
                  {item.candidate_name ? (
                    <p className="text-[11px] text-brand-grayMid">{item.candidate_name}</p>
                  ) : null}
                  {item.error ? (
                    <p className="text-[11px] text-rose-700">{item.error}</p>
                  ) : null}
                </div>
                <span className={cn("shrink-0 rounded-full px-2 py-0.5 text-[11px] font-medium", statusTone(item.status))}>
                  {statusLabel(item.status)}
                </span>
              </li>
            ))}
          </ul>
          <a
            href={`/mandatos/${mandateId}/pipeline`}
            className="mt-4 inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-3.5 py-2 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-blueDark"
          >
            Ver pipeline
          </a>
        </article>
      ) : null}

      {error && tab === "cv" && !cvResults ? null : null}
    </div>
  );
}
