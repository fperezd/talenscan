import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { SystemStatus } from "@/components/configuracion/system-status";

export default function Page() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Configuración"
        title="Configuración del sistema"
        description="Estado de los servicios, integración con OpenAI y recursos técnicos del backend."
      />
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
        <SystemStatus />
      </section>
    </AppShell>
  );
}
