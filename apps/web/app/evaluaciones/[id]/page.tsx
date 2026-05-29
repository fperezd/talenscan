import { EvaluationDetailClient } from "@/components/evaluaciones/evaluation-detail-client";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";

export function generateStaticParams() {
  return [{ id: "demo" }];
}

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  return (
    <AppShell>
      <PageHeader
        eyebrow="Evaluación 360"
        title="Evaluación 360 Talenscan"
        description="Score explicable por dimensión, brechas críticas, evidencia del CV y preguntas sugeridas para entrevista."
      />
      <EvaluationDetailClient evaluationId={id} />
    </AppShell>
  );
}
