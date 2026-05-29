import {
  ArrowRight,
  ClipboardList,
  FileBarChart,
  KanbanSquare,
  Sparkles,
} from "lucide-react";

import { DashboardMetrics } from "@/components/dashboard/dashboard-metrics";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";

const accionesRapidas = [
  {
    title: "Crear mandato de búsqueda",
    description: "Levantamiento consultivo en español, estructurado y evaluable.",
    href: "/mandatos/nuevo",
    icon: ClipboardList,
  },
  {
    title: "Evaluar candidatos",
    description: "Sube CVs y genera Evaluación 360 Talenscan con evidencia.",
    href: "/mandatos",
    icon: Sparkles,
  },
  {
    title: "Ver pipeline",
    description: "Tablero Kanban con drag & drop por mandato.",
    href: "/pipeline",
    icon: KanbanSquare,
  },
  {
    title: "Descargar informes",
    description: "Informes Word/PDF profesionales para presentar al cliente.",
    href: "/reportes",
    icon: FileBarChart,
  },
];

export default function InicioPage() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Inicio"
        title="Bienvenido a Talenscan"
        description="Transforma mandatos de búsqueda, CVs y criterios en inteligencia accionable: prioriza candidatos, gestiona pipelines y presenta informes profesionales al cliente."
        actions={
          <a
            href="/mandatos/nuevo"
            className="inline-flex items-center gap-1.5 rounded-lg bg-brand-blue px-4 py-2 text-sm font-semibold text-white shadow-soft transition hover:bg-brand-blueDark"
          >
            Crear mandato de búsqueda
            <ArrowRight className="h-3.5 w-3.5" />
          </a>
        }
      />

      <DashboardMetrics />

      <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-semibold text-brand-black">Acciones rápidas</h3>
            <p className="text-xs text-brand-grayMid">Atajos al flujo principal de búsqueda ejecutiva.</p>
          </div>
        </div>
        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {accionesRapidas.map(({ title, description, href, icon: Icon }) => (
            <a
              key={href}
              href={href}
              className="group flex flex-col gap-2 rounded-xl border border-slate-200 bg-slate-50/40 p-4 transition hover:border-brand-blue/40 hover:bg-white hover:shadow-soft"
            >
              <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-white text-brand-blue ring-1 ring-slate-200">
                <Icon className="h-4 w-4" />
              </span>
              <div>
                <p className="text-sm font-semibold text-brand-black">{title}</p>
                <p className="mt-0.5 text-xs text-brand-grayMid">{description}</p>
              </div>
              <ArrowRight className="mt-auto h-4 w-4 self-end text-brand-grayMid transition group-hover:translate-x-0.5 group-hover:text-brand-blue" />
            </a>
          ))}
        </div>
      </section>
    </AppShell>
  );
}
