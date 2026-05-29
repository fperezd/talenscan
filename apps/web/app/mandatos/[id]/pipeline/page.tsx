import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { MandatoTabs } from "@/components/mandatos/mandato-tabs";
import { PipelineBoard } from "@/components/pipeline/pipeline-board";

export function generateStaticParams() {
  return [{ id: "demo" }];
}

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  return (
    <AppShell>
      <PageHeader
        eyebrow="Pipeline"
        title="Pipeline de candidatos"
        description="Tablero Kanban con drag & drop para priorizar candidatos, armar shortlist y avanzar a presentación al cliente."
      />
      <MandatoTabs />
      <PipelineBoard mandateId={id} />
    </AppShell>
  );
}
