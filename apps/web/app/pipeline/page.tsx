import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { PipelineMandateList } from "@/components/pipeline/pipeline-mandate-list";

export default function Page() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Pipeline"
        title="Pipelines por mandato"
        description="Selecciona un mandato para abrir su tablero Kanban con drag & drop."
      />
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-soft">
        <PipelineMandateList />
      </section>
    </AppShell>
  );
}
