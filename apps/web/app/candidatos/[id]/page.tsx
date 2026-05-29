import { CandidateDetailClient } from "@/components/candidatos/candidate-detail-client";
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
        eyebrow="Candidato"
        title="Perfil del candidato"
        description="Detalle estructurado, evidencia del CV y evaluaciones 360 asociadas."
      />
      <CandidateDetailClient candidateId={id} />
    </AppShell>
  );
}
