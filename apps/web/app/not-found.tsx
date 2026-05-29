"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { CandidateDetailClient } from "@/components/candidatos/candidate-detail-client";
import { CandidateCompareClient } from "@/components/comparar/candidate-compare-client";
import { DecisionRoomBuilder } from "@/components/decision-room/decision-room-builder";
import { EvaluationDetailClient } from "@/components/evaluaciones/evaluation-detail-client";
import { EvaluarCandidatosClient } from "@/components/evaluaciones/evaluar-candidatos-client";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { MandatoDetailClient } from "@/components/mandatos/mandato-detail-client";
import { MandatoTabs } from "@/components/mandatos/mandato-tabs";
import { PipelineBoard } from "@/components/pipeline/pipeline-board";
import { PositionSpecClient } from "@/components/position-spec/position-spec-client";
import { ClientShortlistPublicView } from "@/components/shortlist-cliente/client-shortlist-public-view";

/**
 * Next.js con output: 'export' dispara notFound() para cualquier URL que no
 * está en el manifest estático (sólo está generado el id "demo"). Este
 * not-found.tsx intercepta esos casos y, si la URL coincide con un patrón
 * dinámico conocido, renderiza el componente correcto. El resto muestra el
 * 404 real.
 */
export default function NotFound() {
  const pathname = usePathname() || "";
  const [resolved, setResolved] = useState<string>(pathname);

  // En SSG el pathname inicial puede no reflejar la URL real del navegador
  // (que pasó por rewrite del Worker). Forzamos lectura desde window.
  useEffect(() => {
    if (typeof window !== "undefined") {
      setResolved(window.location.pathname);
    }
  }, []);

  const match = useMemo(() => matchDynamicRoute(resolved), [resolved]);

  if (match) {
    return match;
  }

  return (
    <AppShell>
      <PageHeader
        eyebrow="404"
        title="Página no encontrada"
        description="La página que buscas no existe o fue movida. Revisa el menú lateral para volver al producto."
      />
      <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center shadow-soft">
        <p className="text-sm text-brand-grayMid">
          Si llegaste aquí desde un enlace antiguo, vuelve al inicio o al listado de mandatos.
        </p>
        <div className="mt-4 flex justify-center gap-2">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-3.5 py-2 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-blueDark"
          >
            Ir al inicio
          </Link>
          <Link
            href="/mandatos"
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-sm font-medium text-brand-grayMid transition hover:border-brand-blue/40 hover:text-brand-black"
          >
            Ver mandatos
          </Link>
        </div>
      </div>
    </AppShell>
  );
}

function matchDynamicRoute(pathname: string): React.ReactNode | null {
  const cleanPath = pathname.replace(/\/$/, "");

  // /shortlist-cliente/{token} — vista pública del Decision Room.
  // NO va envuelta en AppShell (es la vista del cliente, sin sidebar).
  let shortlistMatch = cleanPath.match(/^\/shortlist-cliente\/([^/]+)$/);
  if (shortlistMatch) {
    return <ClientShortlistPublicView token={shortlistMatch[1]} />;
  }

  // /mandatos/{id}/pipeline
  let m = cleanPath.match(/^\/mandatos\/([^/]+)\/pipeline$/);
  if (m) {
    return (
      <AppShell>
        <PageHeader
          eyebrow="Pipeline"
          title="Pipeline de candidatos"
          description="Tablero Kanban con drag & drop para priorizar candidatos, armar shortlist y avanzar a presentación al cliente."
        />
        <MandatoTabs />
        <PipelineBoard mandateId={m[1]} />
      </AppShell>
    );
  }

  // /mandatos/{id}/perfil-objetivo
  m = cleanPath.match(/^\/mandatos\/([^/]+)\/perfil-objetivo$/);
  if (m) {
    return (
      <AppShell>
        <PageHeader
          eyebrow="Perfil objetivo"
          title="Perfil objetivo del cargo"
          description="Estructura evaluable del cargo: requisitos, competencias, criterios y matriz de scoring."
        />
        <MandatoTabs />
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
          <PositionSpecClient mandateId={m[1]} />
        </section>
      </AppShell>
    );
  }

  // /mandatos/{id}/evaluar
  m = cleanPath.match(/^\/mandatos\/([^/]+)\/evaluar$/);
  if (m) {
    return (
      <AppShell>
        <PageHeader
          eyebrow="Evaluar candidatos"
          title="Carga de CVs y Evaluación 360"
          description="Sube CVs, genera el perfil estructurado del candidato y obtén la Evaluación 360 Talenscan."
        />
        <MandatoTabs />
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
          <EvaluarCandidatosClient mandateId={m[1]} />
        </section>
      </AppShell>
    );
  }

  // /mandatos/{id}/decision-room
  m = cleanPath.match(/^\/mandatos\/([^/]+)\/decision-room$/);
  if (m) {
    return (
      <AppShell>
        <PageHeader
          eyebrow="Decision Room"
          title="Shortlist, feedback y decisiones del cliente en un solo lugar."
          description="Construye una sala privada para que el cliente revise candidatos preseleccionados, compare alternativas y deje feedback estructurado sobre la búsqueda."
        />
        <MandatoTabs />
        <DecisionRoomBuilder mandateId={m[1]} />
      </AppShell>
    );
  }

  // /mandatos/{id}/comparar
  m = cleanPath.match(/^\/mandatos\/([^/]+)\/comparar$/);
  if (m) {
    return (
      <AppShell>
        <PageHeader
          eyebrow="Comparar candidatos"
          title="Comparativo lado a lado"
          description="Selecciona hasta 5 candidatos del pipeline de este mandato y compáralos dimensión por dimensión."
        />
        <MandatoTabs />
        <CandidateCompareClient mandateId={m[1]} />
      </AppShell>
    );
  }

  // /mandatos/{id}
  m = cleanPath.match(/^\/mandatos\/([^/]+)$/);
  if (m) {
    return (
      <AppShell>
        <PageHeader
          eyebrow="Mandato"
          title="Detalle del mandato"
          description="Resumen consultivo del mandato, requisitos y mercado objetivo."
        />
        <MandatoTabs />
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
          <MandatoDetailClient mandateId={m[1]} />
        </section>
      </AppShell>
    );
  }

  // /candidatos/{id}
  m = cleanPath.match(/^\/candidatos\/([^/]+)$/);
  if (m) {
    return (
      <AppShell>
        <PageHeader
          eyebrow="Candidato"
          title="Perfil del candidato"
          description="Detalle estructurado, evidencia del CV y evaluaciones 360 asociadas."
        />
        <CandidateDetailClient candidateId={m[1]} />
      </AppShell>
    );
  }

  // /evaluaciones/{id}
  m = cleanPath.match(/^\/evaluaciones\/([^/]+)$/);
  if (m) {
    return (
      <AppShell>
        <PageHeader
          eyebrow="Evaluación 360"
          title="Evaluación 360 Talenscan"
          description="Score explicable por dimensión, brechas críticas, evidencia del CV y preguntas sugeridas para entrevista."
        />
        <EvaluationDetailClient evaluationId={m[1]} />
      </AppShell>
    );
  }

  return null;
}
