"use client";

import {
  AlertTriangle,
  CheckCircle2,
  Database,
  FileText,
  Linkedin,
  RefreshCw,
  Server,
  Sparkles,
} from "lucide-react";
import { useEffect, useState } from "react";

import { API_BASE_URL, apiFetch } from "@/lib/api";
import { cn } from "@/lib/utils";

type SystemStatus = {
  service: string;
  environment: string;
  database: { ok: boolean; error: string | null };
  openai: { configured: boolean; model: string | null };
  apify?: { configured: boolean; actor: string | null };
  report_generation: { pdf: boolean; word: boolean };
};

function StatusItem({
  icon: Icon,
  title,
  ok,
  description,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  ok: boolean;
  description: string;
}) {
  return (
    <article className="flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-soft">
      <span
        className={cn(
          "inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg",
          ok ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"
        )}
      >
        <Icon className="h-4 w-4" />
      </span>
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <p className="text-sm font-semibold text-brand-black">{title}</p>
          {ok ? (
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-0.5 text-[11px] font-medium text-emerald-700">
              <CheckCircle2 className="h-3 w-3" />
              Operativo
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-[11px] font-medium text-amber-700">
              <AlertTriangle className="h-3 w-3" />
              No configurado
            </span>
          )}
        </div>
        <p className="mt-1 text-xs text-brand-grayMid">{description}</p>
      </div>
    </article>
  );
}

export function SystemStatus() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load(showSpinner = true) {
    if (showSpinner) setLoading(true);
    setRefreshing(true);
    try {
      const data = await apiFetch<SystemStatus>("/api/system/status");
      setStatus(data);
      setError(null);
    } catch (requestError) {
      console.error(requestError);
      setError("No fue posible consultar el estado del sistema.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    void load(true);
  }, []);

  if (loading) {
    return <p className="text-sm text-brand-grayMid">Cargando estado del sistema...</p>;
  }

  if (error || !status) {
    return (
      <p className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
        {error || "Sistema no disponible"}
      </p>
    );
  }

  return (
    <div className="space-y-5">
      <section>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-brand-black">Estado del sistema</h3>
            <p className="text-xs text-brand-grayMid">Información en vivo del backend conectado.</p>
          </div>
          <button
            type="button"
            onClick={() => load(false)}
            disabled={refreshing}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-brand-grayMid transition hover:border-brand-blue/40 hover:text-brand-black disabled:opacity-50"
          >
            <RefreshCw className={cn("h-3.5 w-3.5", refreshing && "animate-spin")} />
            {refreshing ? "Actualizando..." : "Actualizar"}
          </button>
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <StatusItem
            icon={Server}
            title="Backend API"
            ok={true}
            description={`Conectado a ${API_BASE_URL} · ambiente ${status.environment}`}
          />
          <StatusItem
            icon={Database}
            title="Base de datos PostgreSQL"
            ok={status.database.ok}
            description={
              status.database.ok
                ? "Conexión activa con persistencia transaccional"
                : `Error: ${status.database.error || "sin detalle"}`
            }
          />
          <StatusItem
            icon={Sparkles}
            title="Generación IA con OpenAI"
            ok={status.openai.configured}
            description={
              status.openai.configured
                ? `Modelo configurado: ${status.openai.model}. Las llamadas a IA usarán este modelo con validación Pydantic.`
                : "Sin OPENAI_API_KEY. Se usa el motor determinista (regex/keywords) como fallback. Configura el secret OPENAI_API_KEY en Fly para activar la IA."
            }
          />
          <StatusItem
            icon={Linkedin}
            title="Enriquecimiento LinkedIn (Apify)"
            ok={Boolean(status.apify?.configured)}
            description={
              status.apify?.configured
                ? `Activo. Cada URL de LinkedIn agregada se enriquece automáticamente con nombre, cargo, experiencia, educación y skills reales. Actor: ${status.apify.actor}. Costo pay-per-use ~$0.005-0.01 por perfil; $5/mes de créditos free incluidos.`
                : "Sin APIFY_TOKEN. Los candidatos LinkedIn se crean con nombre derivado del slug y placeholder. Para activarlo: regístrate en apify.com, copia tu API token y corre: fly secrets set APIFY_TOKEN=<token> -a talenscan-api"
            }
          />
          <StatusItem
            icon={FileText}
            title="Generación de informes"
            ok={status.report_generation.pdf && status.report_generation.word}
            description="PDF y Word disponibles desde cada evaluación con naming Evaluacion_Perfil_Nombre.PDF"
          />
        </div>
      </section>

      <section className="rounded-xl border border-slate-100 bg-slate-50/40 p-4">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-brand-grayMid">
          Recursos técnicos
        </h4>
        <ul className="mt-2 space-y-1 text-xs text-brand-grayMid">
          <li>
            <span className="font-medium text-brand-black">API:</span>{" "}
            <a
              href={API_BASE_URL}
              target="_blank"
              rel="noreferrer noopener"
              className="text-brand-blue hover:underline"
            >
              {API_BASE_URL}
            </a>
          </li>
          <li>
            <span className="font-medium text-brand-black">Healthcheck:</span>{" "}
            <a
              href={`${API_BASE_URL}/health`}
              target="_blank"
              rel="noreferrer noopener"
              className="text-brand-blue hover:underline"
            >
              {API_BASE_URL}/health
            </a>
          </li>
          <li>
            <span className="font-medium text-brand-black">Documentación OpenAPI:</span>{" "}
            <a
              href={`${API_BASE_URL}/docs`}
              target="_blank"
              rel="noreferrer noopener"
              className="text-brand-blue hover:underline"
            >
              {API_BASE_URL}/docs
            </a>
          </li>
        </ul>
      </section>
    </div>
  );
}
